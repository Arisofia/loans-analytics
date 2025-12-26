"""
⚠️ DEPRECATED MODULE - DO NOT USE

This module is deprecated as of 2025-12-26.

Migration Instructions:
========================

Old code using kpi_engine.py:
    from python.kpi_engine import KPIEngine
    engine = KPIEngine(df)
    results = engine.calculate_metric("PAR30")

Should be updated to:
    from python.kpi_engine_v2 import KPIEngineV2
    engine = KPIEngineV2(df)
    results = engine.calculate_all()
    par30_value = results["PAR30"]["value"]

Key Differences:
- KPIEngineV2 has integrated audit trail logging
- Results include context and metadata
- Error handling is more robust
- All calculations are validated

Timeline:
- Use kpi_engine_v2.py immediately
- This file will be deleted in v2.0 (scheduled 2026-02-01)

Questions? Contact: engineering-team@abaco.com
"""

import warnings
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate
from python.kpis.par_30 import calculate_par_30
from python.kpis.par_90 import calculate_par_90
from python.kpis.portfolio_health import calculate_portfolio_health

warnings.warn(
    "KPIEngine (v1) is deprecated and will be removed in v2.0 (2026-02-01). "
    "Use KPIEngineV2 from python.kpi_engine_v2 instead.",
    DeprecationWarning,
    stacklevel=2,
)


class KPIEngine:
    """
    Deprecated: Use KPIEngineV2 instead.

    Legacy KPI engine for backward compatibility.
    This class maintains the v1 interface while delegating to v2 calculators.
    """

    def __init__(self, df: pd.DataFrame):
        """Initialize with a DataFrame."""
        self.df = df

    def calculate_par_30(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR 30 - Deprecated, use KPIEngineV2.calculate_all()."""
        return calculate_par_30(self.df)

    def calculate_par_90(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate PAR 90 - Deprecated, use KPIEngineV2.calculate_all()."""
        return calculate_par_90(self.df)

    def calculate_collection_rate(self) -> Tuple[float, Dict[str, Any]]:
        """Calculate Collection Rate - Deprecated, use KPIEngineV2.calculate_all()."""
        return calculate_collection_rate(self.df)

    def calculate_portfolio_health(
        self,
        par_30: Optional[float] = None,
        collection_rate: Optional[float] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """Calculate Portfolio Health - Deprecated, use KPIEngineV2.calculate_all()."""
        if par_30 is None:
            par_30, _ = self.calculate_par_30()
        if collection_rate is None:
            collection_rate, _ = self.calculate_collection_rate()
        return calculate_portfolio_health(par_30, collection_rate)

    def calculate_metric(self, metric_name: str) -> float:
        """
        Calculate a single metric by name - Deprecated.

        Args:
            metric_name: Name of the metric (e.g., "PAR30", "PAR90", "CollectionRate")

        Returns:
            The calculated metric value
        """
        metric_name_lower = metric_name.lower()

        if metric_name_lower in ("par30", "par_30"):
            value, _ = self.calculate_par_30()
            return value
        elif metric_name_lower in ("par90", "par_90"):
            value, _ = self.calculate_par_90()
            return value
        elif metric_name_lower in ("collectionrate", "collection_rate"):
            value, _ = self.calculate_collection_rate()
            return value
        elif metric_name_lower in ("portfoliohealth", "portfolio_health"):
            value, _ = self.calculate_portfolio_health()
            return value
        else:
            raise ValueError(f"Unknown metric: {metric_name}")


__all__ = [
    "KPIEngine",
    "calculate_par_30",
    "calculate_par_90",
    "calculate_collection_rate",
    "calculate_portfolio_health",
]
