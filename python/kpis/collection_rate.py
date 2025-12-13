from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional


def _to_numeric_safe(series: Optional[pd.Series]) -> pd.Series:
    if series is None:
        return pd.Series([], dtype=float)
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def calculate_par_90(df: pd.DataFrame) -> np.float64:
    if df is None or df.shape[0] == 0:
        return np.float64(0.0)

    dpd = _to_numeric_safe(df.get("dpd_90_plus_usd")).sum()
    total_receivable = _to_numeric_safe(df.get("total_receivable_usd")).sum()

    if total_receivable == 0:
        return np.float64(0.0)

    return np.float64((dpd / total_receivable) * 100.0)


def calculate_collection_rate(df: pd.DataFrame) -> np.float64:
    if df is None or df.shape[0] == 0:
        return np.float64(0.0)

    cash = _to_numeric_safe(df.get("cash_available_usd")).sum()
    eligible = _to_numeric_safe(df.get("total_eligible_usd")).sum()

    if eligible == 0:
        return np.float64(0.0)

    return np.float64((cash / eligible) * 100.0)
