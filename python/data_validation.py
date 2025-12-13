from __future__ import annotations

import pandas as pd
from typing import Dict, List

REQUIRED_COLUMNS: List[str] = [
    "segment",
    "measurement_date",
    "dpd_90_plus_usd",
    "total_receivable_usd",
    "total_eligible_usd",
    "cash_available_usd",
]

NUMERIC_COLUMNS: List[str] = [
    "dpd_90_plus_usd",
    "total_receivable_usd",
    "total_eligible_usd",
    "cash_available_usd",
]


def validate_df_basic(df: pd.DataFrame, required: List[str] | None = None) -> None:
    """Ensure required columns exist and normalize basic types."""
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")

    if required is None:
        required = REQUIRED_COLUMNS

    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["measurement_date"] = pd.to_datetime(df["measurement_date"], errors="coerce")
    for column in ["dpd_90_plus_usd", "total_receivable_usd", "total_eligible_usd", "cash_available_usd"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def validate_numeric_bounds(df: pd.DataFrame) -> Dict[str, bool]:
    """Check numeric columns are non-negative."""
    validation: Dict[str, bool] = {}
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            validation[f"{col}_non_negative"] = not (df[col] < 0).any()
    return validation
