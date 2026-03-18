import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.python.kpis.engine import KPIEngineV2
from backend.python.kpis.formula_engine import KPIFormulaEngine  # re-exported as SSOT

__all__ = ["CalculationPhase", "KPIFormulaEngine"]

logger = logging.getLogger(__name__)


class CalculationPhase:
    """Pipeline phase for computing KPIs, segments, and time-series data.

    This phase serves as the primary orchestrator for the unified KPI engine (V2),
    handling data preparation, multi-dimensional segmentation, anomaly detection,
    and lineage manifest generation.
    """

    def __init__(self, kpi_definitions: Dict[str, Any]):
        """Initialize with KPI formula definitions."""
        self.kpi_definitions = kpi_definitions
        # KPIEngineV2 is the Single Source of Truth for all metric logic
        self.engine = KPIEngineV2(kpi_definitions)

    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Orchestrate the full calculation suite.

        Args:
            df: Input dataframe (homologated and cleaned).

        Returns:
            Dictionary containing unified KPIs, segments, time-series, and manifest.

        Raises:
            ValueError: If critical calculation failures occur.
        """
        if df.empty:
            error_msg = "CRITICAL: EMPTY DATAFRAME PROVIDED TO CALCULATIONPHASE"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # 1. Unified KPI Calculation (SSOT)
            # This replaces _calculate_kpis, _calculate_derived_risk_kpis,
            # _calculate_enriched_kpis, and _calculate_recurrent_tpv
            kpi_results = self.engine.calculate(df)

            # 2. Segment-based KPIs (Dimension-specific rollups)
            segments = self._calculate_segment_kpis(df)

            # 3. Time-series rollups (Daily, Weekly, Monthly)
            time_series = self._calculate_time_series(df)

            # 4. Anomaly Detection (Threshold-based monitoring)
            anomalies = self._detect_anomalies(kpi_results)

            # 5. Manifest generation (Traceability and Metadata)
            manifest = self._generate_manifest(kpi_results, df)

            return {
                "kpis": kpi_results,
                "segments": segments,
                "time_series": time_series,
                "anomalies": anomalies,
                "manifest": manifest,
            }

        except Exception as e:
            logger.error("CalculationPhase failure: %s", e, exc_info=True)
            # Fail-fast mandate: do not return partial/silent failures
            raise ValueError(f"CRITICAL: KPI calculation pipeline failed: {e}") from e

    def _calculate_time_series(self, df: pd.DataFrame) -> Dict[str, List]:
        """Calculate time-series rollups."""
        logger.info("Calculating time-series rollups")
        result = self._empty_time_series_result()
        date_columns = self._find_date_columns(df)

        if not date_columns:
            logger.debug("No date columns found for time-series analysis")
            return result

        date_col = date_columns[0]
        df_ts = self._prepare_time_series_dataframe(df, date_col)

        if df_ts.empty:
            return result

        numeric_cols = self._get_time_series_numeric_columns(df_ts)
        if not numeric_cols:
            return result

        result["daily"] = self._rollup_sum(df_ts, date_col, numeric_cols, "daily", 30)
        result["weekly"] = self._rollup_sum(df_ts, date_col, numeric_cols, "weekly", 12)
        result["monthly"] = self._rollup_sum(df_ts, date_col, numeric_cols, "monthly", 12)

        logger.info(
            "Time-series calculated: %d daily, %d weekly, %d monthly",
            len(result["daily"]),
            len(result["weekly"]),
            len(result["monthly"]),
        )
        return result

    @staticmethod
    def _empty_time_series_result() -> Dict[str, List[Dict[str, Any]]]:
        """Return empty result structure for time-series rollups."""
        return {"daily": [], "weekly": [], "monthly": []}

    def _find_date_columns(self, df: pd.DataFrame) -> List[str]:
        """Find columns that can be interpreted as dates."""
        date_columns: List[str] = []
        for col in df.columns:
            if df[col].dtype not in ["datetime64[ns]", "object"]:
                continue
            try:
                parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
                if parsed.notna().any():
                    date_columns.append(col)
            except Exception as exc:
                logger.debug("Skipping non-date column %s: %s", col, exc)
        return date_columns

    @staticmethod
    def _prepare_time_series_dataframe(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
        """Create clean dataframe with a parsed non-null date column."""
        df_ts = df.copy()
        df_ts[date_col] = pd.to_datetime(df_ts[date_col], errors="coerce", format="mixed")
        return df_ts.dropna(subset=[date_col])

    @staticmethod
    def _get_time_series_numeric_columns(df_ts: pd.DataFrame) -> List[str]:
        """Get numeric columns for rollups with fallback to amount."""
        if numeric_cols := df_ts.select_dtypes(include=[np.number]).columns.tolist():
            return numeric_cols
        return ["amount"] if "amount" in df_ts.columns else []

    def _rollup_sum(
        self, df_ts: pd.DataFrame, date_col: str, numeric_cols: List[str], period: str, limit: int
    ) -> List[Dict[str, Any]]:
        """Aggregate numeric columns by period and return record dictionaries."""
        try:
            if period == "daily":
                grouped = df_ts.groupby(df_ts[date_col].dt.date)[numeric_cols].sum()
            elif period == "weekly":
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period("W"))[numeric_cols].sum()
            else:
                grouped = df_ts.groupby(df_ts[date_col].dt.to_period("M"))[numeric_cols].sum()
            return grouped.to_dict("records")[:limit]
        except Exception as exc:
            logger.warning(
                "%s rollup failed for %s: %s",
                period.capitalize(),
                date_col,
                exc,
                exc_info=True,
            )
            return []

    def _detect_anomalies(self, kpi_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in KPI values."""
        anomalies: List[Dict[str, Any]] = []

        try:
            normal_ranges = self._default_anomaly_ranges()

            for kpi_name, kpi_value in kpi_results.items():
                anomaly = self._build_anomaly_record(kpi_name, kpi_value, normal_ranges)
                if anomaly is None:
                    continue
                anomalies.append(anomaly)
                min_val, max_val = anomaly["expected_range"]
                logger.warning(
                    "Anomaly detected in %s: %s (expected: %s-%s)",
                    kpi_name,
                    anomaly["value"],
                    min_val,
                    max_val,
                )

            if anomalies:
                logger.info("Detected %d KPI anomalies", len(anomalies))

        except Exception as e:
            logger.error("Anomaly detection failed: %s", e, exc_info=True)
            raise ValueError(f"CRITICAL: Anomaly pipeline failure: {e}") from e

        return anomalies

    @staticmethod
    def _default_anomaly_ranges() -> Dict[str, tuple[float, float]]:
        """Expected KPI ranges in percentage units (30 means 30%)."""
        return {
            "par_30": (0, 30),
            "par_90": (0, 15),
            "default_rate": (0, 4),
            "portfolio_yield": (5, 15),
        }

    @staticmethod
    def _build_anomaly_record(
        kpi_name: str,
        kpi_value: Any,
        normal_ranges: Dict[str, tuple[float, float]],
    ) -> Optional[Dict[str, Any]]:
        """Return anomaly metadata if KPI value is outside expected range."""
        if kpi_value is None or not isinstance(kpi_value, (int, float)):
            return None
        if kpi_name not in normal_ranges:
            return None

        min_val, max_val = normal_ranges[kpi_name]
        if min_val <= kpi_value <= max_val:
            return None

        return {
            "kpi_name": kpi_name,
            "value": kpi_value,
            "expected_range": (min_val, max_val),
            "severity": "critical" if abs(kpi_value - max_val) > max_val * 0.5 else "warning",
        }

    def _calculate_segment_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute PAR30/60/90, default_rate, and outstanding_balance by segment dimension.

        Segment dimensions: company, credit_line, kam_hunter, kam_farmer, gov, industry, doc_type.
        Returns a nested dict: {dimension: {segment_value: {kpi: value}}}.
        """
        segment_dims = self._available_segment_dimensions(df)
        if not segment_dims:
            return {}

        balance_col = self._resolve_col(df, "outstanding_balance", "current_balance", "amount")
        dpd_col = self._resolve_col(df, "dpd", "days_past_due")
        status_col = "status" if "status" in df.columns else None

        if balance_col is None:
            error_msg = "CRITICAL: MISSING BALANCE COLUMN FOR SEGMENT CALCULATION"
            logger.error(error_msg)
            raise ValueError(error_msg)

        work = self._prepare_segment_workframe(df, balance_col, dpd_col, status_col)
        if work.empty:
            return {}

        return {
            dim: self._calculate_dimension_segment_kpis(work, dim, balance_col, dpd_col, status_col)
            for dim in segment_dims
        }

    @staticmethod
    def _available_segment_dimensions(df: pd.DataFrame) -> List[str]:
        """Return supported segment dimensions present in the dataframe."""
        dimensions = []
        if "company" in df.columns or "empresa" in df.columns:
            dimensions.append("company")
        if any(c in df.columns for c in ("credit_line", "lineacredito", "linea_credito")):
            dimensions.append("credit_line")
        if "kam_hunter" in df.columns or "cod_kam_hunter" in df.columns:
            dimensions.append("kam_hunter")
        if any(c in df.columns for c in ("kam_farmer", "cod_kam_farmer", "farmer")):
            dimensions.append("kam_farmer")

        if any(c in df.columns for c in ("gov", "ministry", "ministerio")):
            dimensions.append("gov")
        if any(c in df.columns for c in ("industry", "industria", "giro")):
            dimensions.append("industry")
        if "doc_type" in df.columns:
            dimensions.append("doc_type")
        return dimensions

    @staticmethod
    def _prepare_segment_workframe(
        df: pd.DataFrame, balance_col: str, dpd_col: Optional[str], status_col: Optional[str]
    ) -> pd.DataFrame:
        """Build normalized dataframe used for segment KPI aggregation."""
        active_mask = (
            df[status_col].isin(["active", "delinquent", "defaulted"])
            if status_col
            else pd.Series(True, index=df.index, dtype=bool)
        )
        work = df.loc[active_mask].copy()
        if work.empty:
            return work

        work[balance_col] = pd.to_numeric(work[balance_col], errors="coerce").fillna(0.0)
        if dpd_col:
            work[dpd_col] = pd.to_numeric(work[dpd_col], errors="coerce").fillna(0.0)
        return work

    def _calculate_dimension_segment_kpis(
        self,
        work: pd.DataFrame,
        dim: str,
        balance_col: str,
        dpd_col: Optional[str],
        status_col: Optional[str],
    ) -> Dict[str, Any]:
        """Aggregate segment KPIs for a single dimension."""
        dim_result: Dict[str, Any] = {}

        # Mapping dimension key to possible column names
        dim_map = {
            "company": ["company", "empresa", "compania"],
            "credit_line": ["credit_line", "lineacredito", "linea_credito"],
            "kam_hunter": ["kam_hunter", "cod_kam_hunter"],
            "kam_farmer": ["kam_farmer", "cod_kam_farmer", "farmer"],
            "gov": ["gov", "ministry", "ministerio"],
            "industry": ["industry", "industria", "giro"],
            "doc_type": ["doc_type"],
        }

        resolved_dim = self._resolve_col(work, *(dim_map.get(dim, [dim])))
        if not resolved_dim:
            return {}

        for seg_val, grp in work.groupby(resolved_dim, sort=False):
            if seg_kpis := self._calculate_segment_group_kpis(
                grp, balance_col, dpd_col, status_col
            ):
                dim_result[str(seg_val)] = seg_kpis
        return dim_result

    def _calculate_segment_group_kpis(
        self,
        grp: pd.DataFrame,
        balance_col: str,
        dpd_col: Optional[str],
        status_col: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Compute KPI bundle for one segment group."""
        from decimal import Decimal, ROUND_HALF_UP

        total_bal_raw = grp[balance_col].sum()
        if total_bal_raw <= 0:
            return None

        total_bal = Decimal(str(total_bal_raw)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        seg_kpis: Dict[str, Any] = {
            "outstanding_balance": float(total_bal),
            "loan_count": len(grp),
        }
        if dpd_col:
            seg_kpis.update(
                self._calculate_segment_par_metrics(grp, balance_col, dpd_col, float(total_bal))
            )
        if status_col:
            seg_kpis["default_rate"] = self._calculate_segment_default_rate(grp, status_col)
        return seg_kpis

    @staticmethod
    def _calculate_segment_par_metrics(
        grp: pd.DataFrame, balance_col: str, dpd_col: str, total_bal: float
    ) -> Dict[str, float]:
        """Compute PAR30/60/90 for a segment group, adjusted for carousel/kiting behaviour.

        When the ``ratio_pago_real`` column is present, any account whose actual
        payment ratio is below 1.0 is treated as having a minimum DPD of 90,
        penalising silent delinquency even when the legacy system reports 0 DPD.
        """
        raw_dpd = pd.to_numeric(grp[dpd_col], errors="coerce").fillna(0.0)

        # Kiting adjustment: accounts with ratio_pago_real < 1.0 are forced to DPD >= 90
        if "ratio_pago_real" in grp.columns:
            ratio = pd.to_numeric(grp["ratio_pago_real"], errors="coerce").fillna(1.0)
            adjusted_dpd = np.where(ratio < 1.0, np.maximum(raw_dpd, 90), raw_dpd)
        else:
            adjusted_dpd = raw_dpd.to_numpy()

        adjusted_dpd = pd.Series(adjusted_dpd, index=grp.index)

        return {
            "par_30": round(
                float(grp.loc[adjusted_dpd >= 30, balance_col].sum()) / total_bal * 100, 4
            ),
            "par_60": round(
                float(grp.loc[adjusted_dpd >= 60, balance_col].sum()) / total_bal * 100, 4
            ),
            "par_90": round(
                float(grp.loc[adjusted_dpd >= 90, balance_col].sum()) / total_bal * 100, 4
            ),
        }

    @staticmethod
    def _calculate_segment_default_rate(grp: pd.DataFrame, status_col: str) -> float:
        """Compute default rate for a segment group."""
        n = len(grp)
        return round(float((grp[status_col] == "defaulted").sum()) / n * 100, 4) if n > 0 else 0.0

    @staticmethod
    def _resolve_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
        """Return the first candidate column present in df, or None."""
        return next((c for c in candidates if c in df.columns), None)

    def _generate_manifest(
        self, kpi_results: Dict[str, Any], source_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Generate calculation manifest with lineage."""
        return {
            "run_timestamp": datetime.now().isoformat(),
            "source_rows": len(source_df),
            "kpis_calculated": list(kpi_results.keys()),
            "formula_version": self.kpi_definitions.get("version", "unknown"),
            "traceability": {
                "source_columns": list(source_df.columns),
                "calculation_engine": "kpi_engine_v2",
            },
        }

    # ------------------------------------------------------------------
    # Risk metric helpers (Fail-Fast / Single Source of Truth)
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        """Compute Synthetic Factoring LTV per loan.

        LTV Sintético = capital_desembolsado / (valor_nominal_factura * (1 - tasa_dilucion))

        Returns an empty Series when required columns are absent or the DataFrame
        is empty.

        Invalid-denominator semantics (fail-safe opacity):
            When ``valor_nominal_factura * (1 - tasa_dilucion) == 0`` the LTV is
            mathematically undefined.  Returning 0.0 would silently encode a
            false low-risk value and collapse epistemic uncertainty.  These rows
            therefore yield ``np.nan``.  Use
            :py:meth:`_ltv_sintetico_invalid_mask` to produce an explicit boolean
            opacity flag identifying which loans require manual review.
        """
        required = {"capital_desembolsado", "valor_nominal_factura", "tasa_dilucion"}
        if not required.issubset(df.columns) or df.empty:
            return pd.Series(dtype=float)

        capital = pd.to_numeric(df["capital_desembolsado"], errors="coerce").fillna(0.0)
        nominal = pd.to_numeric(df["valor_nominal_factura"], errors="coerce").fillna(0.0)
        dilution = pd.to_numeric(df["tasa_dilucion"], errors="coerce").fillna(0.0)

        adjusted = nominal * (1.0 - dilution)
        # Zero denominator → np.nan (explicit opacity; see docstring).
        # Non-parseable capital (already 0.0 from fillna) with a valid denominator
        # returns 0.0 as expected.
        ltv = capital / adjusted.replace(0.0, np.nan)
        return ltv

    @staticmethod
    def _ltv_sintetico_invalid_mask(df: pd.DataFrame) -> pd.Series:
        """Return a boolean Series flagging loans with an invalid (zero) LTV denominator.

        A loan is marked ``True`` (invalid / opaque) when
        ``valor_nominal_factura * (1 - tasa_dilucion) == 0``, i.e. the
        adjusted invoice value is fully diluted or the nominal value is zero.
        These loans must not be used in portfolio LTV aggregations without
        explicit acknowledgement.

        Returns an all-False Series (no invalids) when required columns are
        absent or the DataFrame is empty.
        """
        required = {"valor_nominal_factura", "tasa_dilucion"}
        if not required.issubset(df.columns):
            return pd.Series(dtype=bool)
        if df.empty:
            return pd.Series(False, index=df.index, dtype=bool)

        nominal = pd.to_numeric(df["valor_nominal_factura"], errors="coerce").fillna(0.0)
        dilution = pd.to_numeric(df["tasa_dilucion"], errors="coerce").fillna(0.0)
        adjusted = nominal * (1.0 - dilution)
        return adjusted == 0.0

    @staticmethod
    def _calculate_velocity_of_default(
        df_ts: pd.DataFrame,
        default_rate_col: str = "default_rate",
        period_col: Optional[str] = None,
    ) -> pd.Series:
        """Compute period-over-period first derivative of the default rate.

        **Units**: The returned Series is expressed in the same units as
        *default_rate_col*.  When *default_rate_col* holds values in percent
        (e.g. 2.5 = 2.5 %), each element of the result is a percentage-point
        (pp) change per period.  One percentage point equals 100 basis points.

        **Chronology normalisation**: If *period_col* is provided the DataFrame
        is sorted ascending by that column before differencing, ensuring the
        result is monotonically aligned to the calendar timeline regardless of
        the input row order.

        Returns an empty Series when *default_rate_col* is absent.  With a
        single row the result contains one NaN (no prior period to diff against).
        """
        if default_rate_col not in df_ts.columns:
            return pd.Series(dtype=float)

        working = df_ts
        if period_col is not None and period_col in df_ts.columns:
            working = df_ts.sort_values(period_col)

        rate = pd.to_numeric(working[default_rate_col], errors="coerce")
        return rate.diff()

    def _compute_portfolio_velocity_of_default(
        self, df: pd.DataFrame
    ) -> Optional[Decimal]:
        """Compute portfolio-level Velocity of Default from the canonical date column.

        **Chronology**: Records are bucketed into calendar months (Period[M]).
        The groupby is always performed in ascending period order so that
        :py:meth:`pandas.Series.diff` produces the correct forward-looking
        delta between consecutive months.

        **Units**: The returned value is the change in portfolio default rate
        between the two most recent calendar months, expressed in percentage
        points (pp).  A Vd of ``+1.5`` means the default rate rose 1.5 pp
        (= 150 basis points) month-on-month.

        Uses the ``as_of_date`` column (or other recognised date columns) and
        excludes ``closed`` loans from the denominator to avoid dilution.

        Returns:
            ``Decimal`` Vd value quantised to 6 decimal places, or ``None``
            when no recognised date column exists or fewer than two distinct
            month-periods are present.
        """
        _date_candidates = [
            "as_of_date",
            "measurement_date",
            "snapshot_date",
            "reporting_date",
        ]
        date_col = next((c for c in _date_candidates if c in df.columns), None)
        if date_col is None:
            return None

        working = df.copy()
        working[date_col] = pd.to_datetime(working[date_col], errors="coerce")
        working = working.dropna(subset=[date_col])

        # Exclude closed loans from the active portfolio denominator
        if "status" in working.columns:
            working = working[working["status"] != "closed"]

        if working.empty:
            return None

        working["_period"] = working[date_col].dt.to_period("M")
        periods = sorted(working["_period"].unique())
        if len(periods) < 2:
            return None

        # Vectorised default-rate aggregation per period (ascending chronological order)
        if "status" in working.columns:
            working["_is_defaulted"] = (working["status"] == "defaulted").astype(int)
        else:
            working["_is_defaulted"] = 0

        period_agg = working.groupby("_period", sort=True).agg(
            _total=("_is_defaulted", "count"),
            _defaulted=("_is_defaulted", "sum"),
        )
        rates = (period_agg["_defaulted"] / period_agg["_total"].replace(0, np.nan)).fillna(
            0.0
        ) * 100.0

        # diff() on an ascending-sorted Series gives the correct forward delta
        vd_series = rates.diff()

        # Return the most recent velocity value using Decimal arithmetic for precision
        latest_vd = vd_series.iloc[-1]
        # Guard against None/NaN/inf before constructing a Decimal to avoid
        # representation artifacts and InvalidOperation during quantize.
        if latest_vd is None or not np.isfinite(latest_vd):
            return None

        try:
            latest_vd_decimal = Decimal(str(latest_vd))
            return latest_vd_decimal.quantize(Decimal("0.000001"))
        except InvalidOperation:
            logger.warning(
                "Unable to quantize Velocity of Default value %r; returning None", latest_vd
            )
            return None
