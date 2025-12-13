from __future__ import annotations

import numpy as np
import pandas as pd

from .collection_rate import calculate_par_90 as _calculate_par_90

__all__ = ["calculate_par_90"]


def calculate_par_90(df: pd.DataFrame) -> np.float64:
    """Delegate to the shared PAR90 implementation."""
    return _calculate_par_90(df)
