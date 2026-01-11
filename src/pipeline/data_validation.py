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

ISO8601_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$")


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
        """Find matching column from candidates."""
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
        lower_cands = [c.lower() for c in candidates]
        return [self.columns_lower[lc] for lc in lower_cands if lc in self.columns_lower]

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
    """Validate that the DataFrame contains required columns and types."""
    if required_columns:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            if len(missing) == 1:
                raise ValueError(f"Missing required column: {missing[0]}")
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required numeric column: {col}")
            if df[col].dtype == "object":
                for x in df[col]:
                    if isinstance(x, str):
                        raise ValueError(f"Column '{col}' must be numeric: {col}")
            df[col] = pd.to_numeric(df[col], errors="coerce")
            if not pd.api.types.is_numeric_dtype(df[col]):
                raise ValueError(f"Column '{col}' must be numeric: {col}")

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
        msg = str(e)
        if msg.startswith("Missing required column:"):
            msg = msg.replace("Missing required column:", "missing required columns:")
        elif msg.startswith("Missing required columns:"):
            msg = msg.replace("Missing required columns:", "missing required columns:")
        if (
            "must be numeric" in msg
            or msg.startswith("Missing required numeric column:")
            or msg.startswith("Missing required numeric columns:")
        ):
            msg = f"non-numeric columns: {msg}"
        raise AssertionError(f"{stage} schema validation failed: {msg}") from e


def safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric, handling currency symbols and commas."""
    if series.dtype == "object":
        clean = series.astype(str).str.replace(r"[$€£¥₽₡,%]", "", regex=True).str.strip()
        return pd.to_numeric(clean, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def validate_numeric_bounds(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check numeric columns are non-negative."""
    cols_to_check = columns or NUMERIC_COLUMNS
    validation: Dict[str, bool] = {}
    for col in cols_to_check:
        if col in df.columns:
            has_nan = df[col].isna().any()
            has_negative = (df[col] < 0).any()
            validation[f"{col}_non_negative"] = not (has_nan or has_negative)
    return validation


def validate_percentage_bounds(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check percentage columns are between 0 and 100 inclusive."""
    if columns is None:
        exempt_columns = ["collateralization_pct", "collection_rate_pct"]
        columns = [
            c
            for c in df.columns
            if ("percent" in c or "rate" in c or c.endswith("_pct") or c.endswith("_rate"))
            and c not in exempt_columns
        ]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            valid = ((df[col] >= 0) & (df[col] <= 100)).all()
            validation[f"{col}_in_0_100"] = valid
    return validation


def validate_iso8601_dates(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check that all values are valid ISO 8601 dates."""
    if columns is None:
        columns = [c for c in df.columns if "date" in c.lower() or c.lower().endswith("_at")]
    validation: Dict[str, bool] = {}
    iso8601_regex = re.compile(
        r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
    )
    for col in columns:
        if col in df.columns:
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


def validate_monotonic_increasing(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """Check that specified columns are monotonically increasing."""
    if columns is None:
        columns = [
            c for c in df.columns if any(x in c.lower() for x in ["count", "total", "cumulative"])
        ]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            series = df[col].dropna()
            valid = series.is_monotonic_increasing
            validation[f"{col}_monotonic_increasing"] = valid
    return validation


def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, bool]:
    """Check that specified columns have no null values."""
    if columns is None:
        columns = list(set(REQUIRED_ANALYTICS_COLUMNS + NUMERIC_COLUMNS))
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            validation[f"{col}_no_nulls"] = not df[col].isnull().any()
    return validation
