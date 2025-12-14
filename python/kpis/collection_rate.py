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
