from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import pandas as pd


class KPICalculator(ABC):
    """Base class for all KPI calculations with consistent interface."""

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate KPI value.

        Returns:
            Tuple of (value, context_dict) where context includes:
            - rows_processed: number of rows used in calculation
            - formula: human-readable formula applied
            - null_count: number of null values encountered
            - timestamp: calculation timestamp
        """
        pass


class KPIMetadata:
    """Metadata for a KPI including formula, thresholds, and ownership."""

    def __init__(
        self,
        name: str,
        description: str,
        formula: str,
        unit: str,
        data_sources: list,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None,
        owner: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.formula = formula
        self.unit = unit
        self.data_sources = data_sources
        self.threshold_warning = threshold_warning
        self.threshold_critical = threshold_critical
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "formula": self.formula,
            "unit": self.unit,
            "data_sources": self.data_sources,
            "threshold_warning": self.threshold_warning,
            "threshold_critical": self.threshold_critical,
            "owner": self.owner,
        }


def safe_numeric(series: pd.Series, fill_value: float = 0.0) -> pd.Series:
    """Convert series to numeric, handling nulls and coercion errors."""
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.fillna(fill_value)


def create_context(
    formula: str,
    rows_processed: int,
    null_count: int = 0,
    **extra: Any,
) -> Dict[str, Any]:
    """Create standardized context dict for KPI calculations."""
    return {
        "formula": formula,
        "rows_processed": rows_processed,
        "null_count": null_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
