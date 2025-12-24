"""Module for data validation utilities and functions."""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

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

ISO8601_REGEX = re.compile(
    r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)


class ColumnValidator:
    """Validate columns with specific type/format constraints."""
    
    @staticmethod
    def is_numeric(df: pd.DataFrame, col: str) -> bool:
        """Check if column is numeric."""
        return pd.api.types.is_numeric_dtype(df[col])
    
    @staticmethod
    def is_iso8601(val: Any) -> bool:
        """Check if value is ISO 8601 date."""
        if pd.isnull(val):
            return True
        if isinstance(val, (pd.Timestamp, datetime)):
            return True
        return isinstance(val, str) and ISO8601_REGEX.fullmatch(val) is not None
    
    @staticmethod
    def coerce_numeric(df: pd.DataFrame, col: str) -> None:
        """Coerce column to numeric, filling errors with NaN."""
        df[col] = pd.to_numeric(df[col], errors="coerce")


class ColumnFinder:
    """Find columns by exact match, case-insensitive, or substring."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.columns = list(df.columns)
        self.columns_lower = {col.lower(): col for col in self.columns}
    
    def find(self, candidates: List[str]) -> Optional[str]:
        """Find first matching column from candidates."""
        for col in self._exact_match(candidates):
            return col
        for col in self._case_insensitive_match(candidates):
            return col
        for col in self._substring_match(candidates):
            return col
        return None
    
    def _exact_match(self, candidates: List[str]) -> List[str]:
        """Get exact matches from candidates."""
        return [c for c in candidates if c in self.columns]
    
    def _case_insensitive_match(self, candidates: List[str]) -> List[str]:
        """Get case-insensitive matches."""
        return [self.columns_lower[c.lower()] for c in candidates if c.lower() in self.columns_lower]
    
    def _substring_match(self, candidates: List[str]) -> List[str]:
        """Get substring matches (case-insensitive)."""
        result = []
        for candidate in candidates:
            for col in self.columns:
                if candidate.lower() in col.lower():
                    result.append(col)
                    break
        return result


def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    """Find column in DataFrame matching one of the candidates."""
    finder = ColumnFinder(df)
    return finder.find(candidates)


def is_missing_columns(df: pd.DataFrame, required: Optional[List[str]]) -> List[str]:
    """Get list of missing required columns."""
    if not required:
        return []
    return [col for col in required if col not in df.columns]


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    date_columns: Optional[List[str]] = None,
) -> None:
    """Validate DataFrame schema and column types."""
    missing = is_missing_columns(df, required_columns)
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")

    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required numeric column: {col}")
            ColumnValidator.coerce_numeric(df, col)
            if not ColumnValidator.is_numeric(df, col):
                raise ValueError(f"Column '{col}' must be numeric")

    if date_columns:
        for col in date_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required date column: {col}")
            if not all(ColumnValidator.is_iso8601(val) for val in df[col]):
                raise ValueError(f"Column '{col}' must contain ISO 8601 dates")


def assert_dataframe_schema(
    df: pd.DataFrame,
    *,
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
    date_columns: Optional[List[str]] = None,
    stage: str = "DataFrame",
) -> None:
    """Raise AssertionError if schema validation fails."""
    try:
        validate_dataframe(
            df,
            required_columns=required_columns,
            numeric_columns=numeric_columns,
            date_columns=date_columns,
        )
    except ValueError as e:
        raise AssertionError(f"{stage} schema validation failed: {e}")
