"""Metric schema — standardised envelope for every KPI computed by the engine."""

from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class MetricResult(BaseModel):
    """Single metric result from the KPI engine."""

    metric_id: str = Field(..., description="Stable identifier, e.g. par_30")
    metric_name: str = Field(..., description="Human-readable name, e.g. PAR 30")
    value: float = Field(..., description="Computed value")
    unit: str = Field(..., description="ratio | percent | currency | count | months")
    as_of_date: str = Field(..., description="ISO-8601 date of the computation")
    source_mart: str = Field("portfolio_mart", description="Mart that sourced this metric")
    quality_status: str = Field("ok", description="ok | degraded | missing_data")
    dimension_context: Optional[Dict[str, str]] = Field(
        None, description="Optional segment breakdown context"
    )
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
