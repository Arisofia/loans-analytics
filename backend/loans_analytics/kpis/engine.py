"""
KPIEngineV2 - DEPRECATED compatibility shim.

Canonical KPI authority is backend.src.kpi_engine.engine.run_metric_engine.
This module remains only to avoid import-time breaks while migration completes.
All calculations are delegated to run_metric_engine.
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, Optional

import pandas as pd

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

    def get_audit_trail(self) -> pd.DataFrame:
        """Return an empty audit trail — full audit lives in the canonical engine."""
        return pd.DataFrame(columns=["kpi_name", "status", "value", "timestamp"])

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


__all__ = ["KPIEngineV2", "run_metric_engine"]
