"""Semantic resolver — answer metric + dimension queries against mart data.

The resolver sits between raw KPI engine output and the agent/frontend layer.
It knows which metric lives in which mart, how to slice by dimension, and how
to join the metric contract metadata from the registry.
"""

from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.src.semantic.business_dimensions import DIMENSIONS, Dimension
from backend.src.semantic.metric_contracts import MetricContract, MetricUnit
from backend.src.semantic.metrics_registry import MetricsRegistry

logger = logging.getLogger(__name__)


class SemanticResolver:
    """Resolve metric queries by joining KPI engine output with the registry
    and supporting dimensional drill-down over mart data.
    """

    def __init__(self, registry: Optional[MetricsRegistry] = None):
        self._registry = registry or MetricsRegistry.load()

    # ── metric lookup ────────────────────────────────────────────────────
    def resolve_metric(
        self,
        metric_id: str,
        engine_output: Dict[str, Any],
        as_of_date: Optional[date] = None,
    ) -> Optional[MetricContract]:
        """Build a MetricContract from KPI engine output and registry metadata."""
        defn = self._registry.get(metric_id)
        value = engine_output.get(metric_id)
        if value is None:
            return None

        return MetricContract(
            metric_id=metric_id,
            metric_name=defn.metric_name if defn else metric_id,
            value=Decimal(str(value)),
            unit=MetricUnit(defn.unit) if defn and defn.unit in MetricUnit.__members__.values() else MetricUnit.RATIO,
            as_of_date=as_of_date or date.today(),
            source_mart=defn.mart if defn else "unknown",
            owner=defn.owner if defn else "platform",
            description=defn.description if defn else "",
        )

    def resolve_all(
        self,
        engine_output: Dict[str, Any],
        as_of_date: Optional[date] = None,
    ) -> List[MetricContract]:
        """Resolve all metrics present in engine output."""
        results: List[MetricContract] = []
        for metric_id in engine_output:
            contract = self.resolve_metric(metric_id, engine_output, as_of_date)
            if contract is not None:
                results.append(contract)
        return results

    # ── dimensional drill-down ───────────────────────────────────────────
    @staticmethod
    def slice_by_dimension(
        mart_df: pd.DataFrame,
        dim_id: str,
        agg_column: str,
        agg_func: str = "sum",
    ) -> Dict[str, float]:
        """Aggregate *agg_column* by *dim_id* over *mart_df*.

        Returns dict of ``{dimension_value: aggregated_value}``.
        """
        dim = DIMENSIONS.get(dim_id)
        if dim is None:
            raise ValueError(f"Unknown dimension: {dim_id}")

        col = dim.source_column
        if col not in mart_df.columns:
            logger.warning("Dimension column '%s' not in mart", col)
            return {}

        if agg_column not in mart_df.columns:
            logger.warning("Aggregation column '%s' not in mart", agg_column)
            return {}

        grouped = (
            mart_df.groupby(col, dropna=False)[agg_column]
            .agg(agg_func)
        )
        return {str(k): float(v) for k, v in grouped.items()}
