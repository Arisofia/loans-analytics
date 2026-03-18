import logging
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler

from backend.python.kpis.engine import KPIEngineV2
from backend.python.kpis.formula_engine import KPIFormulaEngine  # re-exported as SSOT

# Optional heavy ML dependencies — degrade gracefully when absent
try:
    import umap  # umap-learn

    _UMAP_AVAILABLE = True
except ImportError:  # pragma: no cover
    _UMAP_AVAILABLE = False

try:
    import hdbscan as hdbscan_module

    _HDBSCAN_AVAILABLE = True
except ImportError:  # pragma: no cover
    _HDBSCAN_AVAILABLE = False

__all__ = ["CalculationPhase", "KPIFormulaEngine"]

logger = logging.getLogger(__name__)

# Cohort labels ordered from lowest-risk to highest-risk
_COHORT_LABELS = ["Alfa", "Beta", "Gamma", "Delta"]

# Feature columns used for multidimensional cohort assignment.
# The ordering matters: features earlier in this list contribute to the
# centroid comparison when later features are absent.
_COHORT_FEATURE_COLS = [
    "ltv_sintetico",
    "dpd_adjusted",
    "vd_bps_month",
    "ratio_pago_real",
]


class CalculationPhase:
    """Pipeline phase for computing KPIs, segments, and time-series data.

    This phase serves as the primary orchestrator for the unified KPI engine (V2),
    handling data preparation, multi-dimensional segmentation, anomaly detection,
    and lineage manifest generation.
    """

    def __init__(self, config: Dict[str, Any], kpi_definitions: Dict[str, Any]):
        """Initialize with pipeline configuration and KPI formula definitions.

        Args:
            config: Calculation phase configuration from pipeline.yml
            kpi_definitions: KPI formula definitions from kpi_definitions.yaml
        """
        self.config = config
        self.kpi_definitions = kpi_definitions
        # KPIEngineV2 is the Single Source of Truth for all metric logic
        self.engine = KPIEngineV2(kpi_definitions=kpi_definitions)

    def execute(
        self,
        clean_data_path: Optional[Path] = None,
        df: Optional[pd.DataFrame] = None,
        run_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Execute the calculation phase.

        Loads cleaned data, runs the full calculation suite (KPIs, segments,
        time-series, anomalies, clustering), and returns results.

        Args:
            clean_data_path: Path to clean_data.parquet from Phase 2
            df: DataFrame (if already loaded; takes precedence over clean_data_path)
            run_dir: Directory for this pipeline run (unused currently, kept for API symmetry)

        Returns:
            Results dict with keys: status, kpis, kpi_engine, segment_kpis,
            time_series, anomalies, clustering_metrics, manifest
        """
        if df is None:
            if clean_data_path and Path(clean_data_path).exists():
                df = pd.read_parquet(clean_data_path)
            else:
                raise ValueError(
                    "CRITICAL: CalculationPhase.execute requires either a DataFrame "
                    "or a valid clean_data_path."
                )

        results = self.process(df)
        results["status"] = "success"
        results["kpi_engine"] = self.engine
        return results

    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Orchestrate the full calculation suite.

        Args:
            df: Input dataframe (homologated and cleaned).

        Returns:
            Dictionary containing unified KPIs, segments, time-series,
            anomalies, clustering_metrics, and manifest.

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

            # 3.5. Advanced Clustering — PCA → UMAP → HDBSCAN
            # Runs before Phase 4 (Output) so clustering_metrics are
            # available for the structured audit_metadata.json export.
            clustering_metrics = self._run_advanced_clustering(df)

            # 4. Anomaly Detection (Threshold-based monitoring)
            anomalies = self._detect_anomalies(kpi_results)

            # 5. Manifest generation (Traceability and Metadata)
            manifest = self._generate_manifest(kpi_results, df)

            return {
                "kpis": kpi_results,
                "segments": segments,
                "segment_kpis": segments,
                "time_series": time_series,
                "anomalies": anomalies,
                "clustering_metrics": clustering_metrics,
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
        """Find columns that can be interpreted as dates.

        Columns are first filtered by name heuristics (suffix ``_date``, ``_at``,
        ``_ts``, ``date_``, ``fecha``) to avoid expensive datetime-parse attempts on
        unrelated string columns such as borrower names or industry codes.
        """
        _KNOWN_DATE_COLS = frozenset(
            {
                "disbursement_date",
                "origination_date",
                "due_date",
                "payment_date",
                "measurement_date",
                "approved_at",
                "funded_at",
                "created_at",
                "updated_at",
            }
        )
        date_name_pattern = re.compile(
            r"(^date|_date$|_at$|_ts$|^fecha|_fecha$)", re.IGNORECASE
        )
        date_columns: List[str] = []
        for col in df.columns:
            dtype = df[col].dtype
            dtype_str = str(dtype)
            is_datetime = dtype_str.startswith("datetime64")
            is_string = dtype_str in ("object", "str") or dtype_str.startswith("string")
            if not is_datetime and not is_string:
                continue
            # Already typed as datetime — include directly
            if is_datetime:
                date_columns.append(col)
                continue
            # For object/string columns, apply name heuristics before expensive parsing
            if col not in _KNOWN_DATE_COLS and not date_name_pattern.search(col):
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
            return grouped.reset_index().to_dict("records")[:limit]
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
            logger.debug(
                "KPI '%s' has no anomaly range registered — anomaly monitoring skipped for this metric",
                kpi_name,
            )
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
        """Compute PAR30/60/90 for a segment group using canonical upstream DPD state."""
        raw_dpd = pd.to_numeric(grp[dpd_col], errors="coerce").fillna(0.0)
        if "dpd_adjusted" in grp.columns:
            adjusted_dpd = pd.to_numeric(grp["dpd_adjusted"], errors="coerce").fillna(raw_dpd)
        else:
            adjusted_dpd = raw_dpd
        if total_bal == 0:
            return {"par_30": 0.0, "par_60": 0.0, "par_90": 0.0}

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
    def _calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        """Calculate strict synthetic LTV and persist opacity metadata on the dataframe.

        Epistemic uncertainty rule:
        - Denominator <= 0 or NaN -> opaque observation
        - Opaque observations receive np.nan (never 0.0 fallback)
        """
        required = ("capital_desembolsado", "valor_nominal_factura", "tasa_dilucion")
        if not all(col in df.columns for col in required):
            return pd.Series(dtype=float)

        valor_nominal = pd.to_numeric(df["valor_nominal_factura"], errors="coerce")
        tasa_dilucion = pd.to_numeric(df["tasa_dilucion"], errors="coerce")
        capital = pd.to_numeric(df["capital_desembolsado"], errors="coerce")

        valor_ajustado = valor_nominal * (1 - tasa_dilucion)
        is_opaque = valor_ajustado.isna() | (valor_ajustado <= 0)

        ltv = np.where(is_opaque, np.nan, capital / valor_ajustado)
        df["ltv_sintetico_is_opaque"] = is_opaque.astype(int)
        df["ltv_sintetico"] = pd.Series(ltv, index=df.index, dtype=float)
        return df["ltv_sintetico"]

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
    # Risk metric helpers (companion opacity flag + Vd)
    # ------------------------------------------------------------------

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

    def _compute_portfolio_velocity_of_default(self, df: pd.DataFrame) -> Optional[Decimal]:
        """Compute portfolio-level Velocity of Default from the canonical date column.

        Delegates to :class:`~backend.python.kpis.engine.KPIEngineV2` as the
        Single Source of Truth for this metric.

        **Units**: percentage points per month (pp/month); 1 pp = 100 basis
        points.  Positive values indicate a worsening default trend.

        Returns:
            ``Decimal`` Vd value quantised to 6 decimal places, or ``None``
            when no recognised date column exists or fewer than two distinct
            month-periods are present.
        """
        return KPIEngineV2._compute_portfolio_velocity_of_default(df)

    # ------------------------------------------------------------------
    # Phase 3.5: Advanced Clustering — PCA → UMAP → HDBSCAN
    # ------------------------------------------------------------------

    def _run_advanced_clustering(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Execute the PCA → UMAP → HDBSCAN clustering pipeline.

        Feature matrix
        --------------
        - All ``{col}_is_missing`` opacity flags present in *df* (integer 0/1)
        - Robust-scaled versions of: ``ltv_sintetico``, ``dpd_adjusted``,
          ``vd_bps_month``, ``ratio_pago_real``
        - ``fillna`` is **not** used blindly; observations with NaN in any feature
          column are marked opaque and assigned the sentinel cohort "Unknown".

        Cohort assignment
        -----------------
        Each HDBSCAN cluster centroid is evaluated against the four canonical
        risk dimensions (ltv_sintetico, dpd_adjusted, vd_bps_month, ratio_pago_real)
        and assigned a label from ``[Alfa, Beta, Gamma, Delta]`` (low→high risk)
        based on a composite risk score derived from the multidimensional centroid.

        Returns
        -------
        dict with keys:
            n_clusters, n_noise, cohort_distribution, cluster_centroids,
            feature_columns, pca_explained_variance, umap_available,
            hdbscan_available
        """
        metrics: Dict[str, Any] = {
            "umap_available": _UMAP_AVAILABLE,
            "hdbscan_available": _HDBSCAN_AVAILABLE,
        }

        try:
            X, feature_cols, opaque_mask = self._build_feature_matrix(df)
            metrics["feature_columns"] = feature_cols
            metrics["n_opaque_excluded"] = int(opaque_mask.sum())

            if X.shape[0] < 10:
                logger.warning(
                    "Clustering skipped: insufficient non-opaque observations (%d < 10)",
                    X.shape[0],
                )
                metrics["skipped"] = True
                metrics["skip_reason"] = f"insufficient_observations ({X.shape[0]})"
                return metrics

            # 1. Robust scaling and PCA dimensionality reduction
            X_scaled, pca_explained = self._scale_and_reduce_pca(X)
            metrics["pca_explained_variance"] = pca_explained

            # 2. UMAP dimensionality reduction (optional)
            X_embed = self._apply_umap(X_scaled, metrics)

            # 3. HDBSCAN clustering (optional)
            labels = self._apply_hdbscan(X_embed, X_scaled, metrics)

            # 4. Map HDBSCAN cluster ids → institutional cohort labels
            cohort_series, centroids = self._map_cohorts(df, labels, opaque_mask, feature_cols)
            metrics["cohort_distribution"] = (
                cohort_series.value_counts().to_dict() if cohort_series is not None else {}
            )
            metrics["cluster_centroids"] = centroids

        except Exception as exc:
            logger.error("Advanced clustering failed: %s", exc, exc_info=True)
            metrics["error"] = str(exc)

        return metrics

    def _build_feature_matrix(self, df: pd.DataFrame) -> tuple[np.ndarray, List[str], pd.Series]:
        """Build the numeric feature matrix for clustering.

        Includes:
        - All ``{col}_is_missing`` opacity flags already in the dataframe.
        - The four canonical risk features (winsorization applied below in the scaler).

        NaN handling
        ------------
        Rows with NaN in ANY feature are excluded (opaque_mask=True).
        This prevents the zero-fill bias that would corrupt cluster geometry.

        Returns
        -------
        (X, feature_cols, opaque_mask)
        """
        feature_cols: List[str] = []

        # Add is_missing flags (they are already 0/1 integers).
        # Sort them to ensure deterministic feature ordering regardless of df.columns order.
        flag_cols = sorted(
            [
                c
                for c in df.columns
                if c.endswith("_is_missing") and pd.api.types.is_numeric_dtype(df[c])
            ]
        )
        feature_cols.extend(flag_cols)

        # Add canonical risk features if present
        for col in _COHORT_FEATURE_COLS:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                if col not in feature_cols:
                    feature_cols.append(col)

        if not feature_cols:
            raise ValueError(
                "No numeric feature columns available for clustering "
                f"(looked for: {_COHORT_FEATURE_COLS} + *_is_missing flags)"
            )

        feat_df = df[feature_cols].copy()
        opaque_mask = feat_df.isna().any(axis=1)
        feat_df_clean = feat_df.loc[~opaque_mask]

        X = feat_df_clean.to_numpy(dtype=float)
        return X, feature_cols, opaque_mask

    @staticmethod
    def _scale_and_reduce_pca(X: np.ndarray) -> tuple[np.ndarray, List[float]]:
        """Apply RobustScaler then PCA retaining up to 95% cumulative variance.

        Uses ``n_components=0.95`` so sklearn chooses the minimum number of
        principal components that explain at least 95% of the total variance,
        capped at 10 components.

        Note: ``svd_solver='full'`` is required because it is the only solver
        that accepts a fractional ``n_components`` value (variance threshold).
        Using 'auto' or 'arpack' would raise a ValueError at fit time.
        """
        scaler = RobustScaler()
        X_scaled = scaler.fit_transform(X)

        max_components = min(X_scaled.shape[1], X_scaled.shape[0] - 1, 10)
        if max_components >= 2:
            # svd_solver='full' is mandatory for fractional n_components.
            pca = PCA(n_components=0.95, svd_solver="full", random_state=42)
            X_pca = pca.fit_transform(X_scaled)
            explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]
            # Cap to max_components by slicing — avoids a second expensive fit.
            # PCA output columns are already ordered by explained variance (descending).
            if X_pca.shape[1] > max_components:
                X_pca = X_pca[:, :max_components]
                explained = explained[:max_components]
        else:
            pca = PCA(n_components=max_components, random_state=42)
            X_pca = pca.fit_transform(X_scaled)
            explained = [round(float(v), 4) for v in pca.explained_variance_ratio_]

        return X_pca, explained

    @staticmethod
    def _apply_umap(X_pca: np.ndarray, metrics: Dict[str, Any]) -> np.ndarray:
        """Apply UMAP if available; fall back to PCA output."""
        if not _UMAP_AVAILABLE:
            logger.info("UMAP not available — using PCA output for clustering.")
            return X_pca
        try:
            reducer = umap.UMAP(
                n_components=2,
                n_neighbors=min(15, max(2, X_pca.shape[0] // 5)),
                min_dist=0.1,
                random_state=42,
            )
            X_embed = reducer.fit_transform(X_pca)
            metrics["umap_n_components"] = 2
            return X_embed
        except Exception as exc:
            logger.warning("UMAP failed (%s); falling back to PCA output.", exc)
            return X_pca

    @staticmethod
    def _apply_hdbscan(
        X_embed: np.ndarray, X_fallback: np.ndarray, metrics: Dict[str, Any]
    ) -> np.ndarray:
        """Apply HDBSCAN if available; fall back to a simple PC1-quartile split.

        Notes
        -----
        When HDBSCAN is unavailable, we assign fallback cluster labels by
        splitting on quartiles of the first column of ``X_fallback``. In the
        current pipeline this column corresponds to the first principal
        component (PC1) of the scaled feature space, not a raw DPD feature.
        """
        if not _HDBSCAN_AVAILABLE:
            logger.info("HDBSCAN not available — using quartile-based fallback labels.")
            n = X_fallback.shape[0]
            labels = np.zeros(n, dtype=int)
            quartiles = np.percentile(X_fallback[:, 0], [25, 50, 75])
            for i, q in enumerate(quartiles, start=1):
                labels[X_fallback[:, 0] > q] = i
            metrics["hdbscan_fallback"] = "pc1_quartile_split"
            return labels
        try:
            clusterer = hdbscan_module.HDBSCAN(
                min_cluster_size=max(5, X_embed.shape[0] // 20),
                min_samples=2,
                cluster_selection_method="eom",
            )
            labels = clusterer.fit_predict(X_embed)
            metrics["n_clusters"] = int(len(set(labels)) - (1 if -1 in labels else 0))
            metrics["n_noise"] = int((labels == -1).sum())
            return labels
        except Exception as exc:
            logger.warning("HDBSCAN failed (%s); falling back to single cluster.", exc)
            metrics["hdbscan_error"] = str(exc)
            return np.zeros(X_embed.shape[0], dtype=int)

    def _map_cohorts(
        self,
        df: pd.DataFrame,
        labels: np.ndarray,
        opaque_mask: pd.Series,
        feature_cols: List[str],
    ) -> tuple[Optional[pd.Series], Dict[int, Dict[str, Any]]]:
        """Assign institutional cohort labels (Alfa/Beta/Gamma/Delta) to each cluster.

        Cohort assignment is based on a composite risk score computed from the
        cluster centroid across four canonical dimensions:
        - ``ltv_sintetico``   (higher → riskier)
        - ``dpd_adjusted``    (higher → riskier)
        - ``vd_bps_month``    (higher → riskier)
        - ``ratio_pago_real`` (lower  → riskier — inverted)

        Noise points (label == -1) and opaque observations receive "Unknown".
        """
        non_opaque_idx = df.index[~opaque_mask]

        if len(non_opaque_idx) != len(labels):
            logger.warning(
                "Label count (%d) != non-opaque rows (%d); skipping cohort map.",
                len(labels),
                len(non_opaque_idx),
            )
            return None, {}

        label_series = pd.Series(labels, index=non_opaque_idx, name="cluster_id")

        # Build per-cluster centroids for canonical risk features
        cluster_ids = sorted(set(labels))
        centroids: Dict[int, Dict[str, Any]] = {}
        risk_scores: Dict[int, float] = {}

        for cluster_id in cluster_ids:
            if cluster_id == -1:
                continue
            cluster_mask = label_series == cluster_id
            cluster_rows = df.loc[non_opaque_idx[cluster_mask.values]]
            centroid: Dict[str, Any] = {}
            risk_dims: List[float] = []

            for feat in _COHORT_FEATURE_COLS:
                if feat in cluster_rows.columns:
                    vals = pd.to_numeric(cluster_rows[feat], errors="coerce").dropna()
                    if not vals.empty:
                        mean_val = float(vals.mean())
                        centroid[feat] = round(mean_val, 6)
                        # Invert ratio_pago_real so that lower payment ratio = higher risk
                        risk_dims.append(-mean_val if feat == "ratio_pago_real" else mean_val)

            centroids[cluster_id] = centroid
            risk_scores[cluster_id] = float(np.mean(risk_dims)) if risk_dims else 0.0

        # Rank clusters by composite risk score and assign labels
        sorted_clusters = sorted(risk_scores.keys(), key=lambda c: risk_scores[c])
        cohort_map: Dict[int, str] = {}
        n_labels = len(_COHORT_LABELS)
        for rank, cluster_id in enumerate(sorted_clusters):
            label_idx = min(rank * n_labels // max(len(sorted_clusters), 1), n_labels - 1)
            cohort_map[cluster_id] = _COHORT_LABELS[label_idx]
            centroids[cluster_id]["cohort"] = _COHORT_LABELS[label_idx]
            centroids[cluster_id]["composite_risk_score"] = round(risk_scores[cluster_id], 6)

        # Build final cohort series over the full dataframe index
        full_cohort = pd.Series("Unknown", index=df.index, name="cohort", dtype=object)
        for cluster_id, cohort_name in cohort_map.items():
            mask = label_series == cluster_id
            full_cohort.loc[non_opaque_idx[mask.values]] = cohort_name

        logger.info(
            "Cohort assignment: %s",
            full_cohort.value_counts().to_dict(),
        )
        return full_cohort, centroids
