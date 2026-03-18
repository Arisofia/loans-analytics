"""
KPIEngineV2: Standardized KPI calculation engine with built-in audit trails.

This module provides a unified interface for KPI calculations across the Abaco
loans analytics platform, replacing the v1 approach of individual function calls.
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.python.kpis.collection_rate import calculate_collection_rate
from backend.python.kpis.formula_engine import KPIFormulaEngine
from backend.python.kpis.par_30 import calculate_par_30
from backend.python.logging_config import get_logger

logger = get_logger(__name__)

# Log message format constants
_LOG_KPI_CALCULATED = "Calculated %s: %s"


class KPIEngineV2:
    """
    Unified KPI calculation engine with audit trail support.

    All KPI calculators return a consistent (value, context) tuple format,
    and every calculation is logged in an audit trail with timestamps,
    actor information, and run IDs for full traceability.
    """

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        actor: str = "system",
        run_id: Optional[str] = None,
        kpi_definitions: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize KPI engine.

        Args:
            df: Optional input DataFrame with loan/payment data
            actor: Identity of the entity requesting calculations.
            run_id: Optional unique identifier for this calculation run
            kpi_definitions: Optional dictionary of KPI formulas
        """
        self.df = self._ensure_loan_count_column(df if df is not None else pd.DataFrame())
        self.actor = actor
        self.run_id = run_id or self._generate_run_id()
        self.kpi_definitions = kpi_definitions or {}
        self._audit_records: List[Dict[str, Any]] = []

        logger.info("Initialized KPIEngineV2 with actor=%s, run_id=%s", actor, self.run_id)

    def _generate_run_id(self) -> str:
        """Generate a unique run ID based on timestamp."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _record_calculation(
        self,
        kpi_name: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Record a KPI calculation in the audit trail."""
        record = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "actor": self.actor,
            "kpi_name": kpi_name,
            "value": value,
            "context": context or {},
            "error": error,
            "status": "success" if error is None else "failed",
        }
        self._audit_records.append(record)

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluate only the dynamic formula KPIs defined in ``kpi_definitions``.

        Intended for callers that supply their own formula catalog and do not
        need the full legacy KPI suite (PAR30, LTV, etc.).  Returns a flat
        ``{kpi_name: value}`` mapping so that downstream consumers can index
        directly by name.
        """
        self.df = self._ensure_loan_count_column(df)
        dynamic_kpis = self._calculate_dynamic_kpis()
        return {
            name: (float(value) if value is not None else None)
            for name, value in dynamic_kpis.items()
        }

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio at Risk (30+ days)."""
        kpi_name = "PAR30"
        try:
            value = calculate_par_30(self.df)
            context = {
                "formula": "SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable) * 100",
                "rows_processed": len(self.df),
                "calculation_method": "v1_legacy",
            }
            self._record_calculation(kpi_name, value, context)
            logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
            return value, context
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to calculate %s: %s", kpi_name, error_msg)
            # Fail-fast mandate: do not return partial/silent failures
            raise ValueError(f"CRITICAL: {kpi_name} calculation failed: {e}") from e

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate collection rate."""
        kpi_name = "COLLECTION_RATE"
        try:
            value, _ = calculate_collection_rate(self.df)
            context = {
                "formula": "payments_collected / payments_due * 100",
                "rows_processed": len(self.df),
                "calculation_method": "v1_legacy",
            }
            self._record_calculation(kpi_name, value, context)
            logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
            return value, context
        except Exception as e:
            error_msg = str(e)
            logger.error("Failed to calculate %s: %s", kpi_name, error_msg)
            # Fail-fast mandate: do not return partial/silent failures
            raise ValueError(f"CRITICAL: {kpi_name} calculation failed: {e}") from e

    def calculate_ltv(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio-level Loan-to-Value ratio."""
        kpi_name = "LTV"
        required_columns = ["loan_amount", "collateral_value"]
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            value = 0.0
            context = {
                "formula": "total_loan_amount / total_collateral_value * 100",
                "rows_processed": len(self.df),
                "calculation_method": "v2_engine",
                "missing_columns": missing_columns,
                "calculation_status": "missing_required_columns",
            }
            error_msg = f"Missing required columns for {kpi_name}: {', '.join(missing_columns)}"
            logger.warning(error_msg)
            self._record_calculation(kpi_name, value, context, error_msg)
            return value, context

        total_loans = self.df["loan_amount"].sum()
        total_collateral = self.df["collateral_value"].sum()
        value = (total_loans / total_collateral * 100) if total_collateral > 0 else 0.0

        context = {
            "formula": "total_loan_amount / total_collateral_value * 100",
            "rows_processed": len(self.df),
            "calculation_method": "v2_engine",
        }
        self._record_calculation(kpi_name, value, context)
        logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)
        return value, context

    def calculate_all(self, kpi_definitions: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate all standard and dynamic KPIs.

        Returns:
            Dict mapping KPI names to dicts with "value" and "context" keys.
        """
        logger.info("KPIEngineV2: Calculating all KPIs")
        if kpi_definitions:
            self.kpi_definitions = kpi_definitions

        results = {}

        # 1. Standard Legacy KPIs
        par30_val, par30_ctx = self.calculate_par_30()
        results["PAR30"] = {"value": par30_val, "context": par30_ctx}

        coll_rate_val, coll_rate_ctx = self.calculate_collection_rate()
        results["COLLECTION_RATE"] = {"value": coll_rate_val, "context": coll_rate_ctx}

        # 2. V2 Standard KPIs
        ltv_val, ltv_ctx = self.calculate_ltv()
        results["LTV"] = {"value": ltv_val, "context": ltv_ctx}

        # 3. Dynamic Formula KPIs
        dynamic_kpis = self._calculate_dynamic_kpis()
        for name, value in dynamic_kpis.items():
            results[name] = {"value": float(value) if value is not None else None, "context": {"type": "dynamic_formula"}}

        # 4. Derived Risk KPIs
        derived_risk = self._calculate_derived_risk_kpis(self.df)
        for name, value in derived_risk.items():
            results[name] = {"value": float(value), "context": {"type": "derived_risk"}}

        # 5. Velocity of Default
        vd_val = self._compute_portfolio_velocity_of_default(self.df)
        if vd_val is not None:
            results["velocity_of_default"] = {"value": float(vd_val), "context": {"type": "risk_velocity"}}

        # 6. Enriched KPIs (from CONTROL DE MORA)
        enriched_kpis = self._calculate_enriched_kpis(self.df)
        for name, value in enriched_kpis.items():
            results[name] = {"value": float(value) if value is not None else None, "context": {"type": "enriched"}}

        logger.info("Calculated %d KPIs in total", len(results))
        return results

    def _calculate_dynamic_kpis(self) -> Dict[str, Optional[Decimal]]:
        """Calculate all KPIs from YAML definitions using Formula Engine."""
        engine_full, engine_unique = self._build_kpi_engines(self.df)
        kpis: Dict[str, Optional[Decimal]] = {}
        unique_grain_kpis = {"average_loan_size", "total_loans_count"}

        for category, kpi_name, formula in self._iter_kpi_formulas():
            engine = engine_unique if kpi_name in unique_grain_kpis else engine_full
            try:
                value = engine.calculate(formula)
                kpis[kpi_name] = value
                self._record_calculation(kpi_name, float(value), {"category": category, "formula": formula, "type": "dynamic"})
            except Exception as e:
                logger.error("Dynamic KPI %s failed: %s", kpi_name, e)
                # Fail-fast mandate: do not return partial/silent failures
                raise ValueError(f"CRITICAL: Dynamic KPI {kpi_name} calculation failed: {e}") from e
        
        return kpis

    def _build_kpi_engines(self, df: pd.DataFrame) -> tuple[KPIFormulaEngine, KPIFormulaEngine]:
        """Build full and grain-aware KPI engines."""
        engine_full = KPIFormulaEngine(df)
        dedupe_col = "loan_uid" if "loan_uid" in df.columns else "loan_id"
        if dedupe_col not in df.columns:
            return engine_full, engine_full

        if "origination_date" in df.columns:
            df_unique = df.sort_values("origination_date").drop_duplicates(dedupe_col)
        else:
            df_unique = df.drop_duplicates(dedupe_col)
        return engine_full, KPIFormulaEngine(df_unique)

    @staticmethod
    def _compute_portfolio_velocity_of_default(df: pd.DataFrame) -> Optional[Decimal]:
        """Build a monthly default-rate series and return the latest Velocity of Default.

        **Chronology**: Records are bucketed into calendar months (Period[M]).
        ``groupby(..., sort=True)`` guarantees ascending period order so that
        :py:meth:`pandas.Series.diff` produces the correct forward-looking delta.

        **Units**: The returned value is the change in portfolio default rate
        between the two most recent calendar months, expressed in percentage
        points (pp).  1 pp = 100 basis points.

        Excludes ``closed`` loans from the active-portfolio denominator.  When
        no ``status`` column is present, all records are treated as
        non-defaulted (default rate = 0 % in every period).

        Returns:
            ``Decimal`` Vd value quantised to 6 decimal places, or ``None``
            when no recognised date column exists or fewer than two distinct
            month-periods are present.
        """
        date_col = next(
            (c for c in (
                "as_of_date", "measurement_date", "snapshot_date",
                "origination_date", "FechaDesembolso", "application_date",
                "disbursement_date", "reporting_date",
            ) if c in df.columns),
            None,
        )
        if date_col is None:
            return None

        work = df.copy()
        work["_date"] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
        work = work.dropna(subset=["_date"])

        # Exclude closed loans from the active portfolio denominator
        if "status" in work.columns:
            work = work[work["status"] != "closed"]

        if work.empty:
            return None

        work["_period"] = work["_date"].dt.to_period("M")
        if work["_period"].nunique() < 2:
            return None

        if "status" in work.columns:
            work["_is_defaulted"] = (work["status"] == "defaulted").astype(int)
        else:
            work["_is_defaulted"] = 0

        period_agg = work.groupby("_period", sort=True).agg(
            _total=("_is_defaulted", "count"),
            _defaulted=("_is_defaulted", "sum"),
        )
        default_ratio = period_agg["_defaulted"] / period_agg["_total"].replace(0, np.nan)
        rates = default_ratio.fillna(0.0) * 100.0

        vd = rates.diff()
        vd_clean = vd.dropna()
        latest_vd = vd_clean.iloc[-1] if not vd_clean.empty else None
        if latest_vd is None or not np.isfinite(latest_vd):
            return None
        return Decimal(str(round(float(latest_vd), 6)))

    def _calculate_derived_risk_kpis(self, df: pd.DataFrame) -> Dict[str, Decimal]:
        """Compute derived risk KPIs not covered by the formula catalog."""
        balance_col = next((c for c in ("outstanding_balance", "current_balance") if c in df.columns), None)
        if "dpd" not in df.columns or "status" not in df.columns or balance_col is None:
            return {}

        active_df = df[df["status"].isin(["active", "delinquent", "defaulted"])]
        total_out = Decimal(str(active_df[balance_col].sum()))

        if total_out <= 0:
            return {
                "npl_ratio": Decimal("0.0"),
                "npl_90_ratio": Decimal("0.0"),
                "defaulted_outstanding_ratio": Decimal("0.0"),
                "top_10_borrower_concentration": Decimal("0.0"),
            }

        npl_mask = (active_df["dpd"] >= 90) | (active_df["status"] == "defaulted")
        npl_out = Decimal(str(active_df.loc[npl_mask, balance_col].sum()))
        npl_ratio = (npl_out / total_out) * 100
        defaulted_out = Decimal(str(active_df.loc[active_df["status"] == "defaulted", balance_col].sum()))

        kpis: Dict[str, Decimal] = {
            "npl_ratio": npl_ratio,
            "npl_90_ratio": npl_ratio,
            "defaulted_outstanding_ratio": (defaulted_out / total_out) * 100,
            "top_10_borrower_concentration": self._top_10_borrower_concentration(active_df, balance_col, total_out),
        }

        # LTV Sintético portfolio-level summary (exclude opaque/NaN observations)
        ltv_series = self._calculate_ltv_sintetico(df)
        if not ltv_series.empty:
            ltv_valid = ltv_series[ltv_series.notna() & (ltv_series > 0)]
            if not ltv_valid.empty:
                kpis["ltv_sintetico_mean"] = Decimal(str(round(float(ltv_valid.mean()), 6)))
                high_risk_pct = float((ltv_valid > 1.0).sum()) / float(len(ltv_valid)) * 100
                kpis["ltv_sintetico_high_risk_pct"] = Decimal(str(round(high_risk_pct, 4)))

        return kpis

    @staticmethod
    def _calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        """Calculate Synthetic Factoring LTV at the loan level.

        LTV Sintético = capital_desembolsado / (valor_nominal_factura * (1 - tasa_dilucion))

        Invalid-denominator semantics (fail-safe opacity):
            When the adjusted invoice value is zero or NaN the LTV is
            mathematically undefined.  Returning 0.0 would silently encode a
            false low-risk value.  These rows therefore yield ``np.nan`` so
            that callers can detect and handle them explicitly.
        """
        required = ("capital_desembolsado", "valor_nominal_factura", "tasa_dilucion")
        if not all(col in df.columns for col in required):
            return pd.Series(dtype=float)

        valor_nominal = pd.to_numeric(df["valor_nominal_factura"], errors="coerce")
        tasa_dilucion = pd.to_numeric(df["tasa_dilucion"], errors="coerce")
        capital = pd.to_numeric(df["capital_desembolsado"], errors="coerce")

        valor_ajustado = valor_nominal * (1 - tasa_dilucion)
        is_opaque = valor_ajustado.isna() | (valor_ajustado <= 0)
        # NaN/zero denominator → np.nan (explicit opacity; never 0.0 which encodes false low-risk)
        ltv = np.where(is_opaque, np.nan, capital / valor_ajustado)
        return pd.Series(ltv, index=df.index, dtype=float)

    def _top_10_borrower_concentration(self, active_df: pd.DataFrame, balance_col: str, total_out: Decimal) -> Decimal:
        """Compute top-10 borrower concentration ratio."""
        if "borrower_id" not in active_df.columns or total_out <= 0:
            return Decimal("0.0")
        concentration = active_df.groupby("borrower_id")[balance_col].sum().sort_values(ascending=False).head(10).sum()
        return (Decimal(str(concentration)) / total_out) * 100

    def _ensure_loan_count_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add loan_count when borrower_id and loan_id exist."""
        if "borrower_id" in df.columns and "loan_id" in df.columns and "loan_count" not in df.columns:
            df = df.copy()
            df["loan_count"] = df.groupby("borrower_id")["loan_id"].transform("nunique")
        return df

    def _iter_kpi_formulas(self) -> List[tuple[str, str, str]]:
        """Collect (category, KPI name, formula) from configured KPI definitions."""
        category_order = ["portfolio_kpis", "asset_quality_kpis", "cash_flow_kpis", "growth_kpis", "customer_kpis", "operational_kpis"]
        formulas: List[tuple[str, str, str]] = []
        for category in category_order:
            category_kpis = self.kpi_definitions.get(category, {})
            for kpi_name, kpi_config in category_kpis.items():
                if formula := kpi_config.get("formula"):
                    formulas.append((category, kpi_name, formula))
        return formulas

    def _calculate_enriched_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute new KPIs available from the CONTROL DE MORA enriched format."""
        enriched: Dict[str, Any] = {}
        balance_col = self._resolve_col(df, "outstanding_balance", "current_balance", "amount")
        total_bal = float(df[balance_col].sum()) if balance_col else 0.0

        self._add_categorical_exposure_rate(enriched, "collections_eligible_rate", df, balance_col, total_bal, ("collections_eligible", "procede_a_cobrar"), "Y")
        self._add_categorical_exposure_rate(enriched, "government_sector_exposure_rate", df, balance_col, total_bal, ("government_sector", "goes"), "GOES")

        if util_col := self._resolve_col(df, "utilization_pct", "porcentaje_utilizado"):
            avg_utilization = self._calculate_avg_credit_line_utilization(df, util_col)
            if avg_utilization is not None:
                enriched["avg_credit_line_utilization"] = avg_utilization

        capital_rate = self._calculate_capital_collection_rate(df, balance_col, total_bal)
        if capital_rate is not None:
            enriched["capital_collection_rate"] = capital_rate

        mdsc_rate = self._calculate_mdsc_posted_rate(df)
        if mdsc_rate is not None:
            enriched["mdsc_posted_rate"] = mdsc_rate

        return enriched

    def _add_categorical_exposure_rate(self, target: Dict[str, Any], metric_name: str, df: pd.DataFrame, balance_col: Optional[str], total_bal: float, candidates: tuple[str, str], match_value: str) -> None:
        """Add balance-weighted exposure for a categorical flag column."""
        source_col = self._resolve_col(df, *candidates)
        if source_col is None or balance_col is None or total_bal <= 0:
            return

        flag_mask = df[source_col].astype(str).str.strip().str.upper() == match_value
        flagged_balance = float(df.loc[flag_mask, balance_col].sum())
        target[metric_name] = round(flagged_balance / total_bal * 100, 4)

    @staticmethod
    def _calculate_avg_credit_line_utilization(df: pd.DataFrame, util_col: str) -> Optional[float]:
        """Compute average utilization, normalizing percent-like raw formats."""
        raw_util = df[util_col].astype(str).str.replace(r"[$,%\s]", "", regex=True)
        util_series = pd.to_numeric(raw_util, errors="coerce").dropna()
        if util_series.empty:
            return None

        if float(util_series.median()) < 2.0:
            util_series = util_series * 100
        return round(float(util_series.mean()), 4)

    def _calculate_capital_collection_rate(self, df: pd.DataFrame, balance_col: Optional[str], total_bal: float) -> Optional[float]:
        """Compute capital collection ratio over outstanding balance."""
        cap_col = self._resolve_col(df, "capital_collected", "capitalcobrado")
        if cap_col is None or balance_col is None or total_bal <= 0:
            return None

        cap_collected = pd.to_numeric(df[cap_col], errors="coerce").fillna(0.0).sum()
        return round(float(cap_collected) / total_bal * 100, 4)

    def _calculate_mdsc_posted_rate(self, df: pd.DataFrame) -> Optional[float]:
        """Compute average posted MDSC rate in percentage points."""
        mdsc_col = self._resolve_col(df, "mdsc_posted", "mdscposteado")
        if mdsc_col is None:
            return None

        mdsc = pd.to_numeric(df[mdsc_col], errors="coerce").fillna(0.0)
        n = len(mdsc)
        if n <= 0:
            return 0.0
        return round(float(mdsc.sum()) / n * 100, 4)

    @staticmethod
    def _resolve_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
        """Resolve a column from multiple candidates."""
        return next((c for c in candidates if c in df.columns), None)

    def calculate_nsm_metrics(self) -> Dict[str, Any]:
        """Classify clients as new / recurrent / recovered per period and compute TPV."""
        ts = self._build_client_tpv_timeseries(self.df)
        if ts.empty:
            return {}

        periods = sorted(ts["period"].unique())
        pivot = ts.pivot_table(index="client_id", columns="period", values="tpv", fill_value=0.0)

        by_period: Dict[str, Any] = {}
        for i, period in enumerate(periods):
            active_mask = pivot[period] > 0

            if i == 0:
                new_mask = active_mask
                recurrent_mask = pd.Series(False, index=pivot.index)
                recovered_mask = pd.Series(False, index=pivot.index)
            else:
                prev_period = periods[i - 1]
                prior_periods = periods[:i]
                
                previously_active = pivot[prior_periods].sum(axis=1) > 0
                recurrent_mask = active_mask & (pivot[prev_period] > 0)
                recovered_mask = active_mask & (~(pivot[prev_period] > 0)) & previously_active
                new_mask = active_mask & (~previously_active)

            by_period[period] = {
                "new_tpv": float(pivot.loc[new_mask, period].sum()),
                "recurrent_tpv": float(pivot.loc[recurrent_mask, period].sum()),
                "recovered_tpv": float(pivot.loc[recovered_mask, period].sum()),
                "new_count": int(new_mask.sum()),
                "recurrent_count": int(recurrent_mask.sum()),
                "recovered_count": int(recovered_mask.sum()),
            }

        latest_period = periods[-1]
        return {
            "by_period": by_period,
            "latest_period": latest_period,
            "latest": by_period[latest_period],
        }

    @staticmethod
    def _build_client_tpv_timeseries(df: pd.DataFrame) -> pd.DataFrame:
        """Build per-(period, client) TPV timeseries from transaction data."""
        if df.empty:
            return pd.DataFrame(columns=["period", "client_id", "tpv"])

        client_col = next((c for c in ("client_id", "borrower_id", "CodCliente") if c in df.columns), None)
        date_col = next((c for c in ("origination_date", "FechaDesembolso", "application_date", "disbursement_date") if c in df.columns), None)
        amount_col = next((c for c in ("amount", "MontoDesembolsado", "ValorAprobado", "loan_amount") if c in df.columns), None)

        if client_col is None or date_col is None or amount_col is None:
            return pd.DataFrame(columns=["period", "client_id", "tpv"])

        work = df[[client_col, date_col, amount_col]].copy()
        try:
            work["_date"] = pd.to_datetime(work[date_col], format="mixed", errors="coerce")
        except TypeError:
            work["_date"] = pd.to_datetime(work[date_col], errors="coerce")
        work = work.dropna(subset=["_date"])
        work["period"] = work["_date"].dt.to_period("M").astype(str)
        work["tpv"] = pd.to_numeric(work[amount_col], errors="coerce").fillna(0.0)
        work = work.rename(columns={client_col: "client_id"})

        result = work.groupby(["period", "client_id"], as_index=False)["tpv"].sum()
        return result[["period", "client_id", "tpv"]]

    def get_audit_trail(self) -> pd.DataFrame:
        """Export the calculation audit trail as a DataFrame."""
        if not self._audit_records:
            return pd.DataFrame(columns=["timestamp", "run_id", "actor", "kpi_name", "value", "context", "error", "status"])

        records_for_df = []
        for record in self._audit_records:
            record_copy = record.copy()
            context_value = record_copy.get("context", {})
            record_copy["context"] = json.dumps(context_value if context_value is not None else {})
            records_for_df.append(record_copy)

        return pd.DataFrame(records_for_df)
