"""
Module for data validation utilities and functions.
"""
from typing import List, Optional, Dict
import pandas as pd
import re
from datetime import datetime


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

def validate_dataframe(df: pd.DataFrame, required_columns: Optional[List[str]] = None, numeric_columns: Optional[List[str]] = None) -> None:
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
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            if len(missing) == 1:
                raise ValueError(f"Missing required column: {missing[0]}")
            else:
                raise ValueError(f"Missing required columns: {', '.join(missing)}")
            
    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required numeric column: {col}")
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column '{col}' must be numeric (column: {col})")


def assert_dataframe_schema(
    df: pd.DataFrame,
    *,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    stage: str = "DataFrame",
) -> None:
    """Raise AssertionError when the DataFrame schema deviates from expectations."""
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
    raise ValueError(f"{stage} missing required columns: {missing}")
    if numeric_columns:
        non_numeric = [col for col in numeric_columns if col in df.columns and not pd.api.types.is_numeric_dtype(df[col])]
        if non_numeric:
    raise TypeError(f"{stage} non-numeric columns: {non_numeric}")


def validate_numeric_bounds(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """Check numeric columns are non-negative."""
    cols_to_check = columns or NUMERIC_COLUMNS
    validation: Dict[str, bool] = {}
    for col in cols_to_check:
        if col in df.columns:
            validation[f"{col}_non_negative"] = not (df[col] < 0).any()
    return validation

def validate_percentage_bounds(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """Check percentage columns are between 0 and 100 inclusive."""
    if columns is None:
        columns = [
            c for c in df.columns if 'percent' in c or 'rate' in c or c.endswith('_pct') or c.endswith('_rate')
        ]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            valid = ((df[col] >= 0) & (df[col] <= 100)).all()
            validation[f"{col}_in_0_100"] = valid
    return validation

def safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric, handling currency symbols and commas."""
    if series.dtype == 'object':
        # Regex handles currency symbols ($, €, £, ¥, ₽, ₡), commas, and percentages
        clean = series.astype(str).str.replace(r'[$,€£¥₽₡%]', '', regex=True).str.replace(',', '')
        return pd.to_numeric(clean, errors='coerce')
    return pd.to_numeric(series, errors='coerce')

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
                if (match_type == "exact" and candidate.lower() == col.lower()) or \
                   (match_type == "substring" and candidate.lower() in col.lower()):
                    return col
    return None

def validate_iso8601_dates(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Check that all values in the specified columns are valid ISO 8601 dates (YYYY-MM-DD or full ISO format).
    Returns a dict mapping column name to True/False.
    """
    if columns is None:
        # Heuristic: columns with 'date' in the name
        columns = [c for c in df.columns if 'date' in c.lower() or c.lower().endswith('_at')]
    validation: Dict[str, bool] = {}
    iso8601_regex = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$")
    for col in columns:
        if col in df.columns:
            # Accept both string and datetime types
            valid = True
            for val in df[col]:
                if pd.isnull(val):
                    continue
                if isinstance(val, datetime):
                    continue
                if not isinstance(val, str) or not iso8601_regex.match(val):
                    valid = False
                    break
            validation[f"{col}_iso8601"] = valid
    return validation

def validate_monotonic_increasing(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """
    Check that specified columns are monotonically increasing (non-decreasing).
    Returns a dict mapping column name to True/False.
    """
    if columns is None:
        # Heuristic: columns with 'count', 'total', or 'cumulative' in the name
        columns = [c for c in df.columns if any(x in c.lower() for x in ["count", "total", "cumulative"])]
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
        from python.validation import REQUIRED_ANALYTICS_COLUMNS, NUMERIC_COLUMNS
        columns = list(set(REQUIRED_ANALYTICS_COLUMNS + NUMERIC_COLUMNS))
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            validation[f"{col}_no_nulls"] = not df[col].isnull().any()
    return validation
