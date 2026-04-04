"""
KPIEngineV2 - DEPRECATED compatibility shim.

Canonical KPI authority is backend.src.kpi_engine.engine.run_metric_engine.
This module remains only to avoid import-time breaks while migration completes.
All calculations are delegated to run_metric_engine.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import warnings
from typing import Any, Dict, Optional

import pandas as pd

from backend.loans_analytics.kpis.ltv import calculate_ltv_sintetico
from backend.src.kpi_engine.engine import run_metric_engine


class KPIEngineV2:
    """Deprecated compatibility facade for legacy call sites."""

    def __init__(
        self,
        df: Optional[pd.DataFrame] = None,
        actor: str = "system",
        run_id: Optional[str] = None,
        kpi_definitions: Optional[Dict[str, Any]] = None,
    ) -> None:
        warnings.warn(
            "KPIEngineV2 is deprecated and will be removed in v1.4.0. "
            "Use run_metric_engine() from backend.src.kpi_engine.engine.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.df = df if isinstance(df, pd.DataFrame) else pd.DataFrame()
        self.actor = actor
        self.run_id = run_id
        self.kpi_definitions = kpi_definitions or {}

    def _as_marts(self, df: Optional[pd.DataFrame] = None) -> Dict[str, pd.DataFrame]:
        portfolio = df if isinstance(df, pd.DataFrame) else self.df
        if not isinstance(portfolio, pd.DataFrame):
            portfolio = pd.DataFrame()
        return {"portfolio_mart": portfolio}

    def get_audit_trail(self) -> pd.DataFrame:
        """Return an empty audit trail — full audit is in the canonical engine."""
        return pd.DataFrame(columns=["kpi_name", "status", "value", "timestamp"])

    def calculate(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Legacy entrypoint retained for compatibility; delegates to canonical engine."""
        warnings.warn(
            "KPIEngineV2.calculate() delegates to run_metric_engine() and is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        result = run_metric_engine(self._as_marts(df))
        metric_map: Dict[str, Any] = {}
        for section in ("risk_metrics", "pricing_metrics", "executive_metrics"):
            for metric in result.get(section, []):
                metric_map[metric.metric_id] = metric.value
        return metric_map

    def calculate_all(
        self, kpi_definitions: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Legacy batch entrypoint retained for compatibility; delegates to canonical engine."""
        if kpi_definitions:
            self.kpi_definitions = kpi_definitions
        warnings.warn(
            "KPIEngineV2.calculate_all() delegates to run_metric_engine() and is deprecated.",
            DeprecationWarning,
            stacklevel=2,
        )
        result = run_metric_engine(self._as_marts())
        normalized: Dict[str, Dict[str, Any]] = {}
        for section in ("risk_metrics", "pricing_metrics", "executive_metrics"):
            for metric in result.get(section, []):
                normalized[metric.metric_id] = {
                    "value": metric.value,
                    "context": {
                        "type": "run_metric_engine",
                        "domain": metric.source_mart,
                        "owner": metric.owner,
                    },
                }
        return normalized

    @staticmethod
    def _calculate_ltv_sintetico(df: pd.DataFrame) -> pd.Series:
        return calculate_ltv_sintetico(df)

    @staticmethod
    def _resolve_col(df: pd.DataFrame, *candidates: str) -> Optional[str]:
        return next((column for column in candidates if column in df.columns), None)

    def _compute_portfolio_velocity_of_default(self, df: pd.DataFrame) -> Optional[Decimal]:
        date_col = self._resolve_col(df, "as_of_date", "measurement_date", "period")
        if date_col is None:
            return None

        work = df.copy()
        work["_period_date"] = pd.to_datetime(work[date_col], errors="coerce", format="mixed")
        work = work.dropna(subset=["_period_date"])
        if work.empty:
            return None

        if "status" in work.columns:
            status = work["status"].astype(str).str.lower().fillna("active")
            work = work.loc[status != "closed"].copy()
            work["_is_defaulted"] = status.loc[work.index] == "defaulted"
        else:
            work["_is_defaulted"] = False

        if work.empty:
            return None

        work["_period"] = work["_period_date"].dt.to_period("M")
        grouped = work.groupby("_period", sort=True)["_is_defaulted"].mean() * 100.0
        if len(grouped) < 2:
            return None

        deltas = grouped.diff().dropna()
        if deltas.empty:
            return None
        return Decimal(str(round(float(deltas.iloc[-1]), 6)))

    def _calculate_derived_risk_kpis(self, df: pd.DataFrame) -> Dict[str, Decimal]:
        if df.empty:
            zero = Decimal("0.0")
            return {"npl_ratio": zero, "npl_90_ratio": zero}

        dpd_col = self._resolve_col(df, "dpd", "days_past_due")
        status_col = self._resolve_col(df, "status", "loan_status")
        if dpd_col is None:
            zero = Decimal("0.0")
            return {"npl_ratio": zero, "npl_90_ratio": zero}

        dpd = pd.to_numeric(df[dpd_col], errors="coerce").fillna(0.0)
        status = (
            df[status_col].astype(str).str.lower().fillna("active")
            if status_col is not None
            else pd.Series("active", index=df.index, dtype=str)
        )
        total = len(df.index)
        npl_90_ratio = Decimal(str(round(float((dpd >= 90).sum() / total * 100.0), 6)))
        npl_ratio = Decimal(
            str(round(float(((dpd >= 90) | (status == "defaulted")).sum() / total * 100.0), 6))
        )
        return {"npl_ratio": npl_ratio, "npl_90_ratio": npl_90_ratio}

    def calculate_ltv(self) -> tuple[Decimal, Dict[str, Any]]:
        loan_col = self._resolve_col(self.df, "loan_amount", "principal_amount", "amount")
        collateral_col = self._resolve_col(self.df, "collateral_value", "appraised_value", "valor_garantia")
        if loan_col is None or collateral_col is None:
            raise ValueError("missing required columns")

        loan_amount = Decimal(str(pd.to_numeric(self.df[loan_col], errors="coerce").fillna(0.0).sum()))
        collateral_value = Decimal(str(pd.to_numeric(self.df[collateral_col], errors="coerce").fillna(0.0).sum()))
        if collateral_value <= 0:
            raise ValueError("CRITICAL: LTV denominator must be > 0")

        value = (loan_amount / collateral_value * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return value, {
            "calculation_method": "v2_engine",
            "loan_column": loan_col,
            "collateral_column": collateral_col,
        }


__all__ = ["KPIEngineV2", "run_metric_engine"]
