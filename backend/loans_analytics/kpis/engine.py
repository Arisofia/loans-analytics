"""Legacy KPI engine shim.

This module is kept only for backwards-compatible imports while the canonical
engine lives in backend.src.kpi_engine.engine.
"""
from __future__ import annotations

from datetime import datetime, timezone
import warnings
from typing import Any

import pandas as pd

from backend.src.kpi_engine.engine import flatten_metric_result_groups, run_metric_engine


class KPIEngineV2:
    """Deprecated compatibility class.

    Instantiating this shim emits a deprecation warning and callers should
    migrate to backend.src.kpi_engine.engine.
    """

    def __init__(
        self,
        df: pd.DataFrame | None = None,
        *args: Any,
        actor: str = "system",
        run_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        self.df = df if df is not None else pd.DataFrame()
        self.actor = actor
        self.run_id = run_id or "legacy-shim"
        warnings.warn(
            "KPIEngineV2 is deprecated; use backend.src.kpi_engine.engine instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def _to_marts(self, df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
        frame = self.df if df is None else df
        return {
            "portfolio_mart": frame,
            "finance_mart": frame,
            "sales_mart": frame,
            "disbursements_mart": frame,
            "payments_mart": frame,
        }

    def calculate_all(self) -> dict[str, dict[str, Any]]:
        grouped = run_metric_engine(self._to_marts())
        flat = flatten_metric_result_groups(grouped)
        timestamp = datetime.now(timezone.utc).isoformat()
        return {
            key: {
                "value": value,
                "context": {
                    "actor": self.actor,
                    "run_id": self.run_id,
                    "timestamp": timestamp,
                },
            }
            for key, value in flat.items()
        }

    def calculate(self, df: pd.DataFrame | None = None) -> dict[str, Any]:
        grouped = run_metric_engine(self._to_marts(df))
        return flatten_metric_result_groups(grouped)

    @staticmethod
    def get_audit_trail() -> pd.DataFrame:
        return pd.DataFrame(columns=["kpi_name", "status", "value", "timestamp"])


__all__ = ["KPIEngineV2"]
