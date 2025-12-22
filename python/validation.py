"""
Module for data validation utilities and functions.
"""


import pandas as pd
import re
from datetime import datetime
from typing import Dict, List, Optional

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

ISO8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)


def _missing_columns(df: pd.DataFrame, columns: List[str]) -> List[str]:
    return [col for col in columns if col not in df.columns]


def _validate_numeric_column(
    df: pd.DataFrame, column: str, context_label: str
) -> None:
    if column not in df.columns:
        raise ValueError(f"{context_label} missing required numeric column: {column}")

    series = df[column]
    if series.dtype == "object":
        if series.dropna().apply(lambda value: isinstance(value, str)).any():
            raise ValueError(f"{context_label} must be numeric: {column}")

    coerced = pd.to_numeric(series, errors="coerce")
    if not pd.api.types.is_numeric_dtype(coerced):
        raise ValueError(f"{context_label} must be numeric: {column}")

    df[column] = coerced


def _default_percentage_columns(df: pd.DataFrame) -> List[str]:
    exempt_columns = ["collateralization_pct", "collection_rate_pct"]
    return [
        c
        for c in df.columns
        if (
            ("percent" in c)
            or ("rate" in c)
            or c.endswith("_pct")
            or c.endswith("_rate")
        )
        and c not in exempt_columns
    ]


def _is_iso8601_value(value) -> bool:
    if pd.isnull(value):
        return True
    if isinstance(value, datetime):
        return True
    if isinstance(value, str) and ISO8601_PATTERN.match(value):
        return True
    return False

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


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
) -> None:
    """
    Validate that the DataFrame contains required columns and types.
    Args:
        df (pd.DataFrame): DataFrame to validate.
        required_columns (list[str], optional): Columns that must be present.
        numeric_columns (list[str], optional): Columns that must be numeric.
    Raises:
        ValueError: If validation fails.
    """
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            if len(missing) == 1:
                raise ValueError(f"Missing required column: {missing[0]}")
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    if numeric_columns:
        for col in numeric_columns:
            _validate_numeric_column(df, col, "Column")


def assert_dataframe_schema(
    df: pd.DataFrame,
    *,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    stage: str = "DataFrame",
) -> None:
    """Raise AssertionError when the DataFrame schema deviates from requirements."""
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            raise ValueError(
                f"{stage} missing required columns: {', '.join(missing)}"
            )
    if numeric_columns:
        for col in numeric_columns:
            _validate_numeric_column(df, col, stage)


def validate_numeric_bounds(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Check numeric columns are non-negative.
    
    Args:
        df: DataFrame to validate
        columns: Columns to check (defaults to NUMERIC_COLUMNS)
    
    Returns:
        Dict mapping column names to validation results. Columns not present 
        in the DataFrame are silently skipped.
    
    Note:
        NaN values are treated as validation failures.
    """
    cols_to_check = columns or NUMERIC_COLUMNS
    validation: Dict[str, bool] = {}
    for col in cols_to_check:
        if col in df.columns:
            # Check for NaN values and negative values
            has_nan = df[col].isna().any()
            has_negative = (df[col] < 0).any()
            validation[f"{col}_non_negative"] = not (has_nan or has_negative)
    return validation


def validate_percentage_bounds(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check percentage columns are between 0 and 100 inclusive."""
    if columns is None:
        columns = _default_percentage_columns(df)
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            valid = ((df[col] >= 0) & (df[col] <= 100)).all()
            validation[f"{col}_in_0_100"] = valid
    return validation


def safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric, handling currency symbols and commas.
    Note: If percentages are present (e.g., '50%'), removing '%' yields 50, not 0.5. Adjust as needed for your use case.
    """
    if series.dtype == "object":
        # Regex handles currency symbols ($, €, £, ¥, ₽, ₡) and commas
        clean = series.astype(str).str.replace(r"[$€£¥₽₡,]", "", regex=True)
        # To handle percentages as fractions, uncomment the following line:
        # clean = clean.str.replace(r"(\d+(?:\.\d+)?)\s*%", lambda m: str(float(m.group(1)) / 100), regex=True)
        return pd.to_numeric(clean, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """
    Helper to find a column in the DataFrame matching one of the candidates.
    Prioritizes:
    1. Exact match
    2. Case-insensitive exact match
    3. Substring match
    """
    columns = df.columns
    # 1. Exact match
    for candidate in candidates:
        if candidate in columns:
            return candidate
    # 2. Case-insensitive exact match & 3. Substring match
    for match_type in ["exact", "substring"]:
        for candidate in candidates:
            for col in columns:
                if (match_type == "exact" and candidate.lower() == col.lower()) or (
                    match_type == "substring" and candidate.lower() in col.lower()
                ):
                    return col
    return None


def validate_iso8601_dates(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Check that all values in the specified columns are valid ISO 8601 dates (YYYY-MM-DD or full ISO format).
    Returns a dict mapping column name to True/False.
    """
    if columns is None:
        # Heuristic: columns with 'date' in the name
        columns = [c for c in df.columns if "date" in c.lower() or c.lower().endswith("_at")]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            # Accept both string and datetime types
            valid = all(_is_iso8601_value(val) for val in df[col])
            validation[f"{col}_iso8601"] = valid
    return validation


def validate_monotonic_increasing(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Check that specified columns are monotonically increasing (non-decreasing).
    Returns a dict mapping column name to True/False.
    """
    if columns is None:
        # Heuristic: columns with 'count', 'total', or 'cumulative' in the name
        columns = [
            c for c in df.columns if any(x in c.lower() for x in ["count", "total", "cumulative"])
        ]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            # Ignore nulls for monotonicity check
            series = df[col].dropna()
            valid = series.is_monotonic_increasing
            validation[f"{col}_monotonic_increasing"] = valid
    return validation


def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Check that specified columns have no null values.
    Returns a dict mapping column name to True/False.
    """
    if columns is None:
        # Heuristic: all columns in REQUIRED_ANALYTICS_COLUMNS and NUMERIC_COLUMNS
        from python.validation import (NUMERIC_COLUMNS,
                                       REQUIRED_ANALYTICS_COLUMNS)

        columns = list(set(REQUIRED_ANALYTICS_COLUMNS + NUMERIC_COLUMNS))
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            validation[f"{col}_no_nulls"] = not df[col].isnull().any()
    return validation
