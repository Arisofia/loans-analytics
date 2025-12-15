"""
Module for data validation utilities and functions.
"""
from typing import List, Optional, Dict
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
