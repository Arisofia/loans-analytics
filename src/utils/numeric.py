from typing import Optional

import pandas as pd


def safe_numeric(series: pd.Series, fill_value: Optional[float] = None) -> pd.Series:
    """
    Convert series to numeric, handling currency symbols, commas, and coercion errors.

    Args:
        series: Input pandas Series.
        fill_value: Value to fill NaNs with. If None, NaNs are preserved.
                   Defaults to None to preserve validation visibility.
    """
    if series is None:
        return pd.Series([], dtype=float)

    if series.dtype == "object":
        # Handle common currency symbols and separators
        clean = series.astype(str).str.replace(r"[$€£¥₽₡,%]", "", regex=True).str.strip()
        numeric = pd.to_numeric(clean, errors="coerce")
    else:
        numeric = pd.to_numeric(series, errors="coerce")

    if fill_value is not None:
        return numeric.fillna(fill_value)
    return numeric
