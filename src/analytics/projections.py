from datetime import datetime

import numpy as np
import pandas as pd


def project_growth(
    yield_start: float, yield_end: float, volume_start: float, volume_end: float, periods: int = 6
) -> pd.DataFrame:
    """
    Project yield and loan volume growth over a specified number of months.

    Args:
        yield_start: Starting yield percentage.
        yield_end: Target yield percentage.
        volume_start: Starting loan volume.
        volume_end: Target loan volume.
        periods: Number of months to project (minimum 2, default 6).

    Returns:
        pd.DataFrame: Projected growth with 'date', 'yield', and 'loan_volume' columns.

    Raises:
        ValueError: If periods is less than 2.
    """
    if periods < 2:
        raise ValueError("periods must be at least 2")

    dates = pd.date_range(start=datetime.now(), periods=periods, freq="MS")

    yields = np.linspace(yield_start, yield_end, periods)
    volumes = np.linspace(volume_start, volume_end, periods)

    return pd.DataFrame({"date": dates, "yield": yields, "loan_volume": volumes})
