from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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


@dataclass(frozen=True)
class KPIMetadata:
    """Metadata for a KPI including formula, thresholds, and ownership."""

    name: str
    description: str
    formula: str
    unit: str
    data_sources: List[str]
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    owner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
