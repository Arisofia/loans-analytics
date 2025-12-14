from __future__ import annotations

from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Optional
from python.validation import safe_numeric

def calculate_collection_rate(df: pd.DataFrame) -> np.float64:

    if df is None or df.shape[0] == 0:
        return np.float64(0.0)

    cash = safe_numeric(df.get("cash_available_usd", pd.Series())).sum()
    eligible = safe_numeric(df.get("total_eligible_usd", pd.Series())).sum()

    if eligible == 0:
        return np.float64(0.0)

    return np.float64((cash / eligible) * 100.0)

def calculate_par_90(df: pd.DataFrame) -> float:
    """Legacy test compatibility: Calculate PAR 90 as (dpd_90_plus_usd / total_receivable_usd) * 100."""
    if df is None or df.empty:
        return 0.0
    try:
        dpd_90 = pd.to_numeric(df.get("dpd_90_plus_usd", pd.Series()), errors="coerce").sum()
        receivable = pd.to_numeric(df.get("total_receivable_usd", pd.Series()), errors="coerce").sum()
        if not receivable:
            return 0.0
        return float((dpd_90 / receivable) * 100.0)
    except Exception:
        return 0.0
