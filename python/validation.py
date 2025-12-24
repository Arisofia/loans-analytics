"""Module for data validation utilities and functions."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd

# Unified required columns for both ingestion and analytics
REQUIRED_ANALYTICS_COLUMNS: List[str] = [
    "loan_amount",
    "appraised_value",
    "borrower_income",
    "monthly_debt",
    "loan_status",
    "interest_rate",
    "principal_balance",
]

ANALYTICS_NUMERIC_COLUMNS: List[str] = [
    "loan_amount",
    "appraised_value",
    "borrower_income",
    "monthly_debt",
    "interest_rate",
    "principal_balance",
]

NUMERIC_COLUMNS: List[str] = [
    "dpd_0_7_usd",
    "dpd_7_30_usd",
    "dpd_30_60_usd",
    "dpd_60_90_usd",
    "dpd_90_plus_usd",
    "total_receivable_usd",
    "total_eligible_usd",
    "discounted_balance_usd",
    "cash_available_usd",
]

# Simplified ISO8601 regex: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS(.sss)?(Z|±HH:MM)?
ISO8601_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)


def is_missing_columns(df: pd.DataFrame, required: Optional[List[str]]) -> List[str]:
    if not required:
        return []
    return [col for col in required if col not in df.columns]


def is_numeric_column(df: pd.DataFrame, col: str) -> bool:
    return pd.api.types.is_numeric_dtype(df[col])


def is_iso8601(val: Any) -> bool:
    if pd.isnull(val):
        return True
    if isinstance(val, (pd.Timestamp, datetime)):
        return True
    if isinstance(val, str) and ISO8601_REGEX.fullmatch(val):
        return True
    return False


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    date_columns: Optional[List[str]] = None,
) -> None:
    missing = is_missing_columns(df, required_columns)
    if missing:
        raise ValueError(
            f"Missing required column(s): {', '.join(missing)}"
        )

    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required numeric column: {col}")
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if not is_numeric_column(df, col):
                raise ValueError(f"Column '{col}' must be numeric (column: {col})")

    if date_columns:
        for col in date_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required date column: {col}")
            if not all(is_iso8601(val) for val in df[col]):
                raise ValueError(f"Column '{col}' must contain ISO 8601 dates")


def assert_dataframe_schema(
    df: pd.DataFrame,
    *,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    date_columns: Optional[List[str]] = None,
    stage: str = "DataFrame",
) -> None:
    """Raise AssertionError when the DataFrame schema deviates from expectations."""
    try:
        validate_dataframe(
            df,
            required_columns=required_columns,
            numeric_columns=numeric_columns,
            date_columns=date_columns,
        )
    except ValueError as e:
        raise AssertionError(f"{stage} schema validation failed: {e}")


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Helper to find a column in the DataFrame matching one of the candidates.
    Prioritizes:
    1. Exact match
    2. Case-insensitive exact match
    3. Substring match
    """
    columns = list(df.columns)
    # 1. Exact match
    for candidate in candidates:
        if candidate in columns:
            return candidate
    # 2. Case-insensitive exact match
    lowered = {col.lower(): col for col in columns}
    for candidate in candidates:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    # 3. Substring match (case-insensitive)
    for candidate in candidates:
        for col in columns:
            if candidate.lower() in col.lower():
                return col
    return None
