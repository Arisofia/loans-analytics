"""Metric contracts — typed metric definitions with validation and thresholds.

Extends MetricDefinition in metrics_registry with stricter Pydantic contracts
for use in the KPI engine output and agent consumption layer.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class MetricUnit(str, Enum):
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    CURRENCY = "currency"
    COUNT = "count"
    DAYS = "days"
    MONTHS = "months"
    BPS = "bps"


class ThresholdBand(BaseModel):
    """Warning / critical thresholds for a metric."""

    warning: Optional[Decimal] = None
    critical: Optional[Decimal] = None
    direction: str = "upper"  # "upper" = bad when above; "lower" = bad when below


class MetricContract(BaseModel):
    """Typed metric contract used as output of the KPI engine."""

    metric_id: str
    metric_name: str
    value: Decimal
    unit: MetricUnit = MetricUnit.RATIO
    as_of_date: date
    source_mart: str
    owner: str = "platform"
    thresholds: Optional[ThresholdBand] = None
    quality_status: str = "ok"  # ok | stale | missing | anomaly
    description: str = ""

    model_config = {"from_attributes": True}

    def is_breached(self) -> bool:
        """Return True if value breaches critical threshold."""
        if self.thresholds is None or self.thresholds.critical is None:
            return False
        if self.thresholds.direction == "upper":
            return self.value > self.thresholds.critical
        return self.value < self.thresholds.critical

    def is_warning(self) -> bool:
        """Return True if value breaches warning threshold."""
        if self.thresholds is None or self.thresholds.warning is None:
            return False
        if self.thresholds.direction == "upper":
            return self.value > self.thresholds.warning
        return self.value < self.thresholds.warning
