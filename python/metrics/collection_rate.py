from __future__ import annotations

import numpy as np
import pandas as pd

from python.kpis.collection_rate import calculate_collection_rate as _calculate_collection_rate

__all__ = ["calculate_collection_rate"]


def calculate_collection_rate(df: pd.DataFrame) -> np.float64:
    """Wrapper that delegates to the canonical KPI implementation."""
    return _calculate_collection_rate(df)
