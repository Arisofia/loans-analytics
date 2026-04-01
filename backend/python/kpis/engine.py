from __future__ import annotations
import hashlib
import json
import warnings
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple
import numpy as np
import pandas as pd
from backend.python.kpis.ltv import calculate_ltv_sintetico
from backend.python.kpis.collection_rate import calculate_collection_rate
from backend.python.kpis.formula_engine import KPIFormulaEngine
from backend.python.kpis.ssot_asset_quality import calculate_asset_quality_metrics
from backend.python.logging_config import get_logger

logger = get_logger(__name__)
_LOG_KPI_CALCULATED = "Calculated %s: %s"
_LOG_KPI_CALCULATION_ERROR = "Failed to calculate %s: %s"
_NPL_STRICT_STATUSES: tuple[str, ...] = ("defaulted",)


class KPIEngineV2:

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        actor: str = "system",
        run_id: Optional[str] = None,
        kpi_definitions: Optional[Dict[str, Any]] = None,
    ):
        self.df = self._ensure_loan_count_column(df if df is not None else pd.DataFrame())
        self.actor = actor
        self.kpi_definitions = kpi_definitions or {}
        self.run_id = run_id or self._generate_run_id()
        self._audit_records: List[Dict[str, Any]] = []
        logger.info("Initialized KPIEngineV2 with actor=%s, run_id=%s", actor, self.run_id)

    def _generate_run_id(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_str = json.dumps(self.kpi_definitions, sort_keys=True, default=str)
        config_hash = hashlib.sha256(config_str.encode()).hexdigest()[:8]
        return f"{ts}_{config_hash}"

    def _record_calculation(
        self,
        kpi_name: str,
        value: Any,
        context: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
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
        if error is None:
            logger.debug(_LOG_KPI_CALCULATED, kpi_name, value)

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        self.df = self._ensure_loan_count_column(df)
        dynamic_kpis = self._calculate_dynamic_kpis()
        return {
            name: float(value) if value is not None else None
            for name, value in dynamic_kpis.items()
        }

    def _calc_par30_legacy(self) -> tuple[Decimal, str]:
        """Legacy PAR30 from pre-bucketed DPD columns.

        .. deprecated::
            Prefer SSOT path via ``calculate_asset_quality_metrics``.
            This fallback is retained for data schemas that lack a raw
            ``dpd`` column but provide pre-bucketed USD columns.
        """
        logger.warning(
            "_calc_par30_legacy is deprecated; data should provide a raw 'dpd' column "
            "so the SSOT path (ssot_asset_quality) is used instead."
        )
        required = ["dpd_30_60_usd", "dpd_60_90_usd", "dpd_90_plus_usd", "total_receivable_usd"]
        if missing := [col for col in required if col not in self.df.columns]:
            raise ValueError(f"Missing required columns for PAR30: {', '.join(missing)}")
        d30_60 = pd.to_numeric(self.df["dpd_30_60_usd"], errors="coerce").fillna(0.0).sum()
        d60_90 = pd.to_numeric(self.df["dpd_60_90_usd"], errors="coerce").fillna(0.0).sum()
        d90p = pd.to_numeric(self.df["dpd_90_plus_usd"], errors="coerce").fillna(0.0).sum()
        total = pd.to_numeric(self.df["total_receivable_usd"], errors="coerce").fillna(0.0).sum()
        if total <= 0:
            return (Decimal("0.00"), "v1_legacy_buckets")
        return (
            Decimal(str(round((d30_60 + d60_90 + d90p) / total * 100, 2))).quantize(
                Decimal("0.01")
            ),
            "v1_legacy_buckets",
        )

    def _calc_par90_legacy(self) -> tuple[Decimal, str]:
        """Legacy PAR90 from pre-bucketed DPD columns.

        .. deprecated::
            Prefer SSOT path via ``calculate_asset_quality_metrics``.
            This fallback is retained for data schemas that lack a raw
            ``dpd`` column but provide pre-bucketed USD columns.
        """
        logger.warning(
            "_calc_par90_legacy is deprecated; data should provide a raw 'dpd' column "
            "so the SSOT path (ssot_asset_quality) is used instead."
        )
        required = ["dpd_90_plus_usd", "total_receivable_usd"]
        if missing := [col for col in required if col not in self.df.columns]:
            raise ValueError(f"Missing required columns for PAR90: {', '.join(missing)}")
        d90p = pd.to_numeric(self.df["dpd_90_plus_usd"], errors="coerce").fillna(0.0).sum()
        total = pd.to_numeric(self.df["total_receivable_usd"], errors="coerce").fillna(0.0).sum()
        if total <= 0:
            return (Decimal("0.00"), "v1_legacy_buckets")
        return (
            Decimal(str(round(d90p / total * 100, 2))).quantize(Decimal("0.01")),
            "v1_legacy_buckets",
        )

    def _resolve_par_columns(self) -> tuple[Optional[str], Optional[str]]:
        balance_col = self._resolve_col(
            self.df, "outstanding_balance", "current_balance", "amount", "total_receivable_usd"
        )
        dpd_col = self._resolve_col(self.df, "dpd", "days_past_due")
        return (balance_col, dpd_col)

    def _calculate_par_value(
        self,
        metric_alias: str,
        legacy_column: str,
        legacy_calculator: Callable[[], tuple[Decimal, str]],
    ) -> tuple[Decimal, str]:
        balance_col, dpd_col = self._resolve_par_columns()
        if not dpd_col and legacy_column in self.df.columns:
            logger.warning(
                "PAR/%s: falling back to legacy bucket-based calculation — "
                "data lacks a raw 'dpd' column. Migrate data to include 'dpd' "
                "for SSOT-consistent results.",
                metric_alias,
            )
            return legacy_calculator()
        if balance_col and dpd_col:
            results = calculate_asset_quality_metrics(
                balance=self.df[balance_col],
                dpd=self.df[dpd_col],
                status=self.df.get("status"),
                actor=self.actor,
                metric_aliases=[metric_alias],
            )
            value = Decimal(str(round(results[metric_alias], 2))).quantize(Decimal("0.01"))
            return (value, "ssot_asset_quality")
        logger.warning(
            "PAR/%s: no SSOT columns available — falling back to legacy calculator.",
            metric_alias,
        )
        return legacy_calculator()

    def _build_par_context(self, threshold_days: int, method: str) -> Dict[str, Any]:
        return {
            "formula": f"SUM(balance WHERE DPD >= {threshold_days}) / SUM(total_balance) * 100",
            "rows_processed": len(self.df),
            "calculation_method": method,
        }

    def _finalize_kpi_success(
        self, kpi_name: str, value: Decimal, context: Dict[str, Any]
    ) -> Tuple[Decimal, Dict[str, Any]]:
        self._record_calculation(kpi_name, value, context)
        return (value, context)

    def _raise_kpi_calculation_error(self, kpi_name: str, error: Exception) -> NoReturn:
        error_msg = str(error)
        logger.error(_LOG_KPI_CALCULATION_ERROR, kpi_name, error_msg)
        raise ValueError(f"CRITICAL: {kpi_name} calculation failed: {error}") from error

    def _calculate_par(
        self,
        kpi_name: str,
        metric_alias: str,
        legacy_column: str,
        legacy_calculator: Callable[[], tuple[Decimal, str]],
        threshold_days: int,
    ) -> Tuple[Decimal, Dict[str, Any]]:
        try:
            value, method = self._calculate_par_value(
                metric_alias=metric_alias,
                legacy_column=legacy_column,
                legacy_calculator=legacy_calculator,
            )
            context = self._build_par_context(threshold_days=threshold_days, method=method)
            return self._finalize_kpi_success(kpi_name, value, context)
        except Exception as e:
            self._raise_kpi_calculation_error(kpi_name, e)

    def calculate_par_30(self) -> Tuple[Decimal, Dict[str, Any]]:
        return self._calculate_par(
            kpi_name="PAR30",
            metric_alias="par30",
            legacy_column="dpd_30_60_usd",
            legacy_calculator=self._calc_par30_legacy,
            threshold_days=30,
        )

    def calculate_par_90(self) -> Tuple[Decimal, Dict[str, Any]]:
        return self._calculate_par(
            kpi_name="PAR90",
            metric_alias="par90",
            legacy_column="dpd_90_plus_usd",
            legacy_calculator=self._calc_par90_legacy,
            threshold_days=90,
        )

    def calculate_collection_rate(self) -> Tuple[Decimal, Dict[str, Any]]:
        kpi_name = "COLLECTION_RATE"
        try:
            value, _ = calculate_collection_rate(self.df)
            context = {
                "formula": "payments_collected / payments_due * 100",
                "rows_processed": len(self.df),
                "calculation_method": "v1_legacy",
            }
            return self._finalize_kpi_success(kpi_name, value, context)
        except Exception as e:
            self._raise_kpi_calculation_error(kpi_name, e)

    def calculate_ltv(self) -> Tuple[Decimal, Dict[str, Any]]:
        kpi_name = "LTV"
        required_columns = ["loan_amount", "collateral_value"]
        missing_columns = [col for col in required_columns if col not in self.df.columns]
        if missing_columns:
            raise ValueError(
                f"CRITICAL: {kpi_name} missing required columns: {', '.join(missing_columns)}"
            )
        total_loans = sum(
            (Decimal(str(v)) for v in self.df["loan_amount"] if pd.notna(v)),
            Decimal("0"),
        )
        total_collateral = sum(
            (Decimal(str(v)) for v in self.df["collateral_value"] if pd.notna(v)),
            Decimal("0"),
        )
        if total_collateral <= Decimal("0"):
            raise ValueError(
                f"CRITICAL: {kpi_name} denominator (total_collateral_value={total_collateral}) is zero or "
                "negative — LTV is mathematically undefined. Please investigate collateral data and overall input "
                "data quality before calculating LTV."
            )
        value = (total_loans / total_collateral * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        context = {
            "formula": "total_loan_amount / total_collateral_value * 100",
            "rows_processed": len(self.df),
            "calculation_method": "v2_engine",
        }
        return self._finalize_kpi_success(kpi_name, value, context)

    def _collect_standard_kpis(
        self, results: Dict[str, Dict[str, Any]], failures: list[str]
    ) -> None:
        try:
            val, ctx = self.calculate_par_30()
            results["PAR30"] = {"value": val, "context": ctx}
        except Exception as e:
            logger.warning("Standard KPI PAR30 failed: %s", e)
            failures.append(f"PAR30={e}")
        try:
            val, ctx = self.calculate_par_90()
            results["PAR90"] = {"value": val, "context": ctx}
        except Exception as e:
            logger.warning("Standard KPI PAR90 failed: %s", e)
            failures.append(f"PAR90={e}")
        try:
            val, ctx = self.calculate_collection_rate()
            results["COLLECTION_RATE"] = {"value": val, "context": ctx}
        except Exception as e:
            logger.warning("Standard KPI COLLECTION_RATE failed: %s", e)
            failures.append(f"COLLECTION_RATE={e}")
        try:
            val, ctx = self.calculate_ltv()
            results["LTV"] = {"value": val, "context": ctx}
        except Exception as e:
            logger.warning("Standard KPI LTV failed: %s", e)
            failures.append(f"LTV={e}")

    def _collect_derived_kpis(
        self, results: Dict[str, Dict[str, Any]], failures: list[str]
    ) -> None:
        try:
            dynamic_kpis = self._calculate_dynamic_kpis()
            for name, value in dynamic_kpis.items():
                results[name] = {
                    "value": float(value) if value is not None else None,
                    "context": {"type": "dynamic_formula"},
                }
        except Exception as e:
            logger.warning("Dynamic KPIs calculation failed: %s", e)
            failures.append(f"DYNAMIC={e}")
        try:
            derived_risk = self._calculate_derived_risk_kpis(self.df)
            for name, value in derived_risk.items():
                results[name] = {"value": float(value), "context": {"type": "derived_risk"}}
        except Exception as e:
            logger.warning("Derived risk KPIs failed: %s", e)
            failures.append(f"DERIVED_RISK={e}")
        try:
            vd_val = self._compute_portfolio_velocity_of_default(self.df)
            if vd_val is not None:
                results["velocity_of_default"] = {
                    "value": float(vd_val),
                    "context": {"type": "risk_velocity"},
                }
        except Exception as e:
            logger.warning("Velocity of default calculation failed: %s", e)
            failures.append(f"VELOCITY_OF_DEFAULT={e}")
        try:
            enriched_kpis = self._calculate_enriched_kpis(self.df)
            for name, value in enriched_kpis.items():
                results[name] = {
                    "value": float(value) if value is not None else None,
                    "context": {"type": "enriched"},
                }
        except Exception as e:
            logger.warning("Enriched KPIs calculation failed: %s", e)
            failures.append(f"ENRICHED={e}")

    def calculate_all(
        self, kpi_definitions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        logger.info("KPIEngineV2: Calculating all KPIs")
        if kpi_definitions:
            self.kpi_definitions = kpi_definitions
        results: Dict[str, Dict[str, Any]] = {}
        failures: list[str] = []
        self._collect_standard_kpis(results, failures)
        self._collect_derived_kpis(results, failures)
        if failures:
            raise ValueError(
                "CRITICAL: KPI batch calculation failed with one or more errors: "
                + " | ".join(failures)
            )
        logger.info("Calculated %d KPIs in total", len(results))
        return results

    def _calculate_dynamic_kpis(self) -> Dict[str, Optional[Decimal]]:
        engine_full, engine_unique = self._build_kpi_engines(self.df)
        kpis: Dict[str, Optional[Decimal]] = {}
        unique_grain_kpis = {"average_loan_size", "total_loans_count"}
        for category, kpi_name, formula in self._iter_kpi_formulas():
            engine = engine_unique if kpi_name in unique_grain_kpis else engine_full
            try:
                if engine.has_kpi_definition(kpi_name):
                    ssot_result = engine.calculate_kpi(kpi_name, strict_comparison_errors=True)
                    value = ssot_result["value"]
                    context = {
                        "category": category,
                        "formula": formula,
                        "type": "dynamic",
                        "formula_version": ssot_result.get("formula_version", "unknown"),
                        "execution_time_ms": ssot_result.get("execution_time_ms", 0),
                    }
                else:
                    value = engine.calculate(formula, strict_comparison_errors=True)
                    context = {"category": category, "formula": formula, "type": "dynamic"}
                kpis[kpi_name] = value
                self._record_calculation(kpi_name, float(value), context)
            except Exception as e:
                if "Division by zero" in str(e):
                    logger.warning(
                        "Skipping dynamic KPI %s due to zero-division math (e.g., missing previous month data).",
                        kpi_name,
                    )
                    continue
                if "Unsupported expression node" in str(e) or "not found in registry" in str(e):
                    logger.warning(
                        "Skipping dynamic KPI %s: formula incompatible with current data schema: %s",
                        kpi_name,
                        e,
                    )
                    continue
                logger.error("Dynamic KPI %s failed: %s", kpi_name, e)
                raise ValueError(f"CRITICAL: Dynamic KPI {kpi_name} calculation failed: {e}") from e
        return kpis

    def _build_kpi_engines(self, df: pd.DataFrame) -> tuple[KPIFormulaEngine, KPIFormulaEngine]:
        engine_full = KPIFormulaEngine(
            df, actor=self.actor, run_id=self.run_id, registry_data=self.kpi_definitions
        )
        dedupe_col = "loan_uid" if "loan_uid" in df.columns else "loan_id"
        if dedupe_col not in df.columns:
            return (engine_full, engine_full)
        if "origination_date" in df.columns:
            df_unique = df.sort_values("origination_date").drop_duplicates(dedupe_col)
        else:
            df_unique = df.drop_duplicates(dedupe_col)
        return (
            engine_full,
            KPIFormulaEngine(
                df_unique, actor=self.actor, run_id=self.run_id, registry_data=self.kpi_definitions
            ),
        )

    @staticmethod
    def _compute_portfolio_velocity_of_default(df: pd.DataFrame) -> Optional[Decimal]:
        date_col = next(
            (
                c
                for c in (
                    "as_of_date",
                    "measurement_date",
                    "snapshot_date",
                    "origination_date",
                    "FechaDesembolso",
                    "application_date",
                    "disbursement_date",
                    "reporting_date",
                )
                if c in df.columns
            ),
            None,
        )
        if date_col is None:
            return None
        work = df.copy()
        work["_date"] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
        work = work.dropna(subset=["_date"])
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
            _total=("_is_defaulted", "count"), _defaulted=("_is_defaulted", "sum")
        )
        default_ratio = period_agg["_defaulted"] / period_agg["_total"].replace(0, np.nan)
        rates = default_ratio.fillna(0.0) * 100.0
        vd = rates.diff()
        vd_clean = vd.dropna()
        latest_vd = None if vd_clean.empty else vd_clean.iloc[-1]
        if latest_vd is None or not np.isfinite(latest_vd):
            return None
        return Decimal(str(round(float(latest_vd), 6)))

    def _calculate_derived_risk_kpis(self, df: pd.DataFrame) -> Dict[str, Decimal]:
        balance_col = self._resolve_col(
            df, "outstanding_balance", "current_balance", "amount", "total_receivable_usd"
        )
        dpd_col = self._resolve_col(df, "dpd", "days_past_due")
        if not balance_col or not dpd_col:
            return {}
        results = calculate_asset_quality_metrics(
            balance=df[balance_col],
            dpd=df[dpd_col],
            status=df.get("status"),
            actor=getattr(self, "actor", "system"),
            metric_aliases=["par30", "par90", "npl", "npl90"],
        )
        active_df = (
            df[df["status"].isin(["active", "delinquent", "defaulted"])]
            if "status" in df.columns
            else df
        )
        total_out = Decimal(str(active_df[balance_col].sum()))
        if total_out <= 0:
            raise ValueError(
                "CRITICAL: Derived risk KPI calculation requires positive outstanding balance."
            )
        npl_90_ratio = Decimal(str(round(results["npl90"], 6)))
        npl_ratio = Decimal(str(round(results["npl"], 6)))
        defaulted_out = Decimal(
            str(active_df.loc[active_df["status"].isin(_NPL_STRICT_STATUSES), balance_col].sum())
            if "status" in active_df.columns
            else 0.0
        )
        kpis: Dict[str, Decimal] = {
            "npl_ratio": npl_ratio,
            "npl_90_ratio": npl_90_ratio,
            "defaulted_outstanding_ratio": defaulted_out / total_out * 100,
            "top_10_borrower_concentration": self._top_10_borrower_concentration(
                active_df, balance_col, total_out
            ),
        }
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
        return calculate_ltv_sintetico(df)

    def _top_10_borrower_concentration(
        self, active_df: pd.DataFrame, balance_col: str, total_out: Decimal
    ) -> Decimal:
        if "borrower_id" not in active_df.columns or total_out <= 0:
            return Decimal("0.0")
        concentration = (
            active_df.groupby("borrower_id")[balance_col]
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .sum()
        )
        return Decimal(str(concentration)) / total_out * 100

    def _ensure_loan_count_column(self, df: pd.DataFrame) -> pd.DataFrame:
        if (
            "borrower_id" in df.columns
            and "loan_id" in df.columns
            and ("loan_count" not in df.columns)
        ):
            df = df.copy()
            df["loan_count"] = df.groupby("borrower_id")["loan_id"].transform("nunique")
        return df

    def _iter_kpi_formulas(self) -> List[tuple[str, str, str]]:
        category_order = [
            "portfolio_kpis",
            "asset_quality_kpis",
            "cash_flow_kpis",
            "growth_kpis",
            "customer_kpis",
            "operational_kpis",
        ]
        formulas: List[tuple[str, str, str]] = []
        for category in category_order:
            category_kpis = self.kpi_definitions.get(category, {})
            for kpi_name, kpi_config in category_kpis.items():
                if formula := kpi_config.get("formula"):
                    formulas.append((category, kpi_name, formula))
        return formulas

    def _calculate_enriched_kpis(self, df: pd.DataFrame) -> Dict[str, Any]:
        enriched: Dict[str, Any] = {}
        balance_col = self._resolve_col(df, "outstanding_balance", "current_balance", "amount")
        total_bal = float(df[balance_col].sum()) if balance_col else 0.0
        self._add_categorical_exposure_rate(
            enriched,
            "collections_eligible_rate",
            df,
            balance_col,
            total_bal,
            ("collections_eligible", "procede_a_cobrar"),
            "Y",
        )
        self._add_categorical_exposure_rate(
            enriched,
            "government_sector_exposure_rate",
            df,
            balance_col,
            total_bal,
            ("government_sector", "goes"),
            "GOES",
        )
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

    def _add_categorical_exposure_rate(
        self,
        target: Dict[str, Any],
        metric_name: str,
        df: pd.DataFrame,
        balance_col: Optional[str],
        total_bal: float,
        candidates: tuple[str, str],
        match_value: str,
    ) -> None:
        source_col = self._resolve_col(df, *candidates)
        if source_col is None or balance_col is None or total_bal <= 0:
            return
        flag_mask = df[source_col].astype(str).str.strip().str.upper() == match_value
        flagged_balance = float(df.loc[flag_mask, balance_col].sum())
        target[metric_name] = round(flagged_balance / total_bal * 100, 4)

    @staticmethod
    def _calculate_avg_credit_line_utilization(df: pd.DataFrame, util_col: str) -> Optional[float]:
        raw_util = df[util_col].astype(str).str.replace("[$,%\\s]", "", regex=True)
        util_series = pd.to_numeric(raw_util, errors="coerce").dropna()
        if util_series.empty:
            return None
        if float(util_series.median()) < 2.0:
            util_series = util_series * 100
        return round(float(util_series.mean()), 4)

    def _calculate_capital_collection_rate(
        self, df: pd.DataFrame, balance_col: Optional[str], total_bal: float
    ) -> Optional[float]:
        cap_col = self._resolve_col(df, "capital_collected", "capitalcobrado")
        if cap_col is None or balance_col is None or total_bal <= 0:
            return None
        cap_collected = pd.to_numeric(df[cap_col], errors="coerce").fillna(0.0).sum()
        return round(float(cap_collected) / total_bal * 100, 4)

    def _calculate_mdsc_posted_rate(self, df: pd.DataFrame) -> Optional[float]:
        mdsc_col = self._resolve_col(df, "mdsc_posted", "mdscposteado")
        if mdsc_col is None:
            return None
        mdsc = pd.to_numeric(df[mdsc_col], errors="coerce").fillna(0.0)
        n = len(mdsc)
        return 0.0 if n <= 0 else round(float(mdsc.sum()) / n * 100, 4)

    @staticmethod
    def _resolve_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
        return next((c for c in candidates if c in df.columns), None)

    def calculate_nsm_metrics(self) -> Dict[str, Any]:
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
                recovered_mask = active_mask & ~(pivot[prev_period] > 0) & previously_active
                new_mask = active_mask & ~previously_active
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
        if df.empty:
            return pd.DataFrame(columns=["period", "client_id", "tpv"])
        client_col = next(
            (c for c in ("client_id", "borrower_id", "CodCliente") if c in df.columns), None
        )
        date_col = next(
            (
                c
                for c in (
                    "origination_date",
                    "FechaDesembolso",
                    "application_date",
                    "disbursement_date",
                )
                if c in df.columns
            ),
            None,
        )
        amount_col = next(
            (
                c
                for c in ("amount", "MontoDesembolsado", "ValorAprobado", "loan_amount")
                if c in df.columns
            ),
            None,
        )
        if client_col is None or date_col is None or amount_col is None:
            return pd.DataFrame(columns=["period", "client_id", "tpv"])
        work = df[[client_col, date_col, amount_col]].copy()
        try:
            work["_date"] = pd.to_datetime(work[date_col], format="mixed", errors="coerce")
        except TypeError:
            work["_date"] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
        work = work.dropna(subset=["_date"])
        work["period"] = work["_date"].dt.to_period("M").astype(str)
        work["tpv"] = pd.to_numeric(work[amount_col], errors="coerce").fillna(0.0)
        work = work.rename(columns={client_col: "client_id"})
        result = work.groupby(["period", "client_id"], as_index=False)["tpv"].sum()
        return result[["period", "client_id", "tpv"]]

    def get_audit_trail(self) -> pd.DataFrame:
        if not self._audit_records:
            return pd.DataFrame(
                columns=[
                    "timestamp",
                    "run_id",
                    "actor",
                    "kpi_name",
                    "value",
                    "context",
                    "error",
                    "status",
                ]
            )
        records_for_df = []
        for record in self._audit_records:
            record_copy = record.copy()
            context_value = record_copy.get("context", {})
            record_copy["context"] = json.dumps(context_value if context_value is not None else {})
            records_for_df.append(record_copy)
        return pd.DataFrame(records_for_df)


class KPIEngine:
    """Strict SSOT dispatcher for canonical asset-quality KPI execution."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config or {}
        self.dispatch_table = {
            "par_30": lambda df: calculate_asset_quality_metrics(
                balance=df["outstanding_principal"],
                dpd=df["days_past_due"],
                status=df.get("status"),
                actor="system",
                metric_aliases=["par_30"],
            )["par_30"],
            "par_60": lambda df: calculate_asset_quality_metrics(
                balance=df["outstanding_principal"],
                dpd=df["days_past_due"],
                status=df.get("status"),
                actor="system",
                metric_aliases=["par_60"],
            )["par_60"],
            "par_90": lambda df: calculate_asset_quality_metrics(
                balance=df["outstanding_principal"],
                dpd=df["days_past_due"],
                status=df.get("status"),
                actor="system",
                metric_aliases=["par_90"],
            )["par_90"],
            "npl_90_ratio": lambda df: calculate_asset_quality_metrics(
                balance=df["outstanding_principal"],
                dpd=df["days_past_due"],
                status=df.get("status"),
                actor="system",
                metric_aliases=["npl_90_ratio"],
            )["npl_90_ratio"],
            "default_rate": lambda df: calculate_asset_quality_metrics(
                balance=df["outstanding_principal"],
                dpd=df["days_past_due"],
                status=df.get("status"),
                actor="system",
                metric_aliases=["default_rate"],
            )["default_rate"],
        }

    def compute_all(self, df: pd.DataFrame) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for kpi_name in self.config.get("requested_kpis", []):
            if kpi_name not in self.dispatch_table:
                raise NotImplementedError(
                    f"KPI '{kpi_name}' is requested in config but lacks an SSOT mapping."
                )
            results[kpi_name] = float(self.dispatch_table[kpi_name](df))
        return results
