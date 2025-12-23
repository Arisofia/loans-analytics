import numpy as np
import pandas as pd

CURRENCY_SYMBOLS = r"[₡$€£¥₽%]"


def standardize_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series

    cleaned = (
        series.astype(str)
        .str.strip()
        .str.replace(CURRENCY_SYMBOLS, "", regex=True)
        .str.replace(",", "", regex=False)
        .replace({"": np.nan, "nan": np.nan})
    )
    return pd.to_numeric(cleaned, errors="coerce")


def project_growth(
    current_yield: float,
    target_yield: float,
    current_loan_volume: float,
    target_loan_volume: float,
    periods: int = 6,
) -> pd.DataFrame:
    """Project portfolio yield and loan volume over a monthly horizon."""

    if periods < 2:
        raise ValueError("periods must be at least 2 to create a projection range")

    schedule = pd.date_range(pd.Timestamp.now().normalize(), periods=periods, freq="MS")
    projection = pd.DataFrame(
        {
            "month": schedule,
            "yield": np.linspace(current_yield, target_yield, periods),
            "loan_volume": np.linspace(current_loan_volume, target_loan_volume, periods),
        }
    )

    return projection
