import numpy as np
import pandas as pd
from python.validation import safe_numeric


def calculate_par_90(df: pd.DataFrame) -> np.float64:
    """
    Calculate Portfolio at Risk > 90 days (PAR 90).
    Formula: SUM(dpd_90_plus_usd) / SUM(total_receivable_usd)
    """
    if df is None or df.shape[0] == 0:
        return np.float64(0.0)

    dpd = safe_numeric(df.get("dpd_90_plus_usd", pd.Series())).sum()
    total_receivable = safe_numeric(df.get("total_receivable_usd", pd.Series())).sum()

    if total_receivable == 0:
        return np.float64(0.0)

    return np.float64((dpd / total_receivable) * 100.0)
