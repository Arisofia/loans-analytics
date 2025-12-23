import numpy as np
import pandas as pd

from python.validation import safe_numeric


def calculate_par_30(df: pd.DataFrame) -> np.float64:
    """Portfolio at Risk (30+ days)
    Formula: SUM(dpd_30_60 + dpd_60_90 + dpd_90+) / SUM(total_receivable)
    """
    if df is None or df.shape[0] == 0:
        return np.float64(0.0)

    dpd_30_60 = safe_numeric(df.get("dpd_30_60_usd", pd.Series())).sum()
    dpd_60_90 = safe_numeric(df.get("dpd_60_90_usd", pd.Series())).sum()
    dpd_90_plus = safe_numeric(df.get("dpd_90_plus_usd", pd.Series())).sum()

    total_receivable = safe_numeric(df.get("total_receivable_usd", pd.Series())).sum()

    if total_receivable == 0:
        return np.float64(0.0)

    return np.float64(((dpd_30_60 + dpd_60_90 + dpd_90_plus) / total_receivable) * 100.0)
