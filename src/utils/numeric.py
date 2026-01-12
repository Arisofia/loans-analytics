from typing import Optional

import pandas as pd


def safe_numeric(series: pd.Series, fill_value: Optional[float] = None) -> pd.Series:
    """
    Convert series to numeric, handling currency symbols, commas, parentheses, and coercion errors.

    Args:
        series: Input pandas Series.
        fill_value: Value to fill NaNs with. If None, NaNs are preserved.
                   Defaults to None to preserve validation visibility.
    """
    if series is None:
        return pd.Series([], dtype=float)

    if series.dtype == "object":
        # Handle common currency symbols, separators, and accounting negative numbers (parentheses)
        clean = (
            series.astype(str)
            .str.replace(r"[$€£¥₽₡,%]", "", regex=True)
            .str.replace(r"\((.*)\)", r"-\1", regex=True)
            .str.strip()
        )
        # Handle empty strings resulting from cleanup
        clean = clean.replace("", "nan")

        # Heuristic: only convert if a significant portion of the sample is numeric
        sample = clean.dropna().head(100)
        if not sample.empty:
            numeric_sample = pd.to_numeric(sample, errors="coerce")
            if numeric_sample.notna().mean() < 0.5:
                return series

        numeric = pd.to_numeric(clean, errors="coerce")
    else:
        numeric = pd.to_numeric(series, errors="coerce")

    if fill_value is not None:
        return numeric.fillna(fill_value)
    return numeric
