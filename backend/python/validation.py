"""
Module for data validation utilities and functions.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl

from python.config import settings

# Unified required columns for both ingestion and analytics
REQUIRED_ANALYTICS_COLUMNS: List[str] = settings.analytics.required_columns


def _missing_columns(df: Any, columns: List[str]) -> List[str]:
    return [col for col in columns if col not in df.columns]


def _validate_numeric_column(df: pd.DataFrame, column: str, context_label: str) -> pd.Series:
    if column not in df.columns:
        raise ValueError(f"{context_label} missing required numeric column: {column}")
    series = df[column]
    if (
        series.dtype == "object"
        and series.dropna().apply(lambda value: isinstance(value, str)).any()
    ):
        raise ValueError(f"{context_label} must be numeric: {column}")
    coerced = pd.to_numeric(series, errors="coerce")
    if not pd.api.types.is_numeric_dtype(coerced):
        raise ValueError(f"{context_label} must be numeric: {column}")
    return coerced


def _default_percentage_columns(df: pd.DataFrame) -> List[str]:
    exempt_columns = ["collateralization_pct", "collection_rate_pct"]
    return [
        c
        for c in df.columns
        if (("percent" in c) or ("rate" in c) or c.endswith(("_pct", "_rate")))
        and c not in exempt_columns
    ]


def _is_iso8601_string(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        datetime.fromisoformat(normalized)
        return True
    except ValueError:
        return False


def _is_iso8601_value(value) -> bool:
    if pd.isnull(value):
        return True
    if isinstance(value, str):
        return _is_iso8601_string(value)
    return isinstance(value, datetime)


ANALYTICS_NUMERIC_COLUMNS: List[str] = settings.analytics.numeric_columns
NUMERIC_COLUMNS: List[str] = settings.analytics.ingestion_numeric_columns


def _validate_polars_dataframe(
    df: pl.DataFrame,
    required_columns: Optional[List[str]],
    numeric_columns: Optional[List[str]],
) -> None:
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f"Missing required numeric column: {col}")
            if not df.schema[col].is_numeric():
                raise ValueError(f"Column {col} must be numeric")


def _validate_pandas_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[List[str]],
    numeric_columns: Optional[List[str]],
) -> None:
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            if len(missing) == 1:
                raise ValueError(f"Missing required column: {missing[0]}")
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            coerced = _validate_numeric_column(df, col, "Column")
            df[col] = coerced


def validate_dataframe(
    df: Union[pd.DataFrame, pl.DataFrame],
    required_columns: Optional[List[str]] = None,
    numeric_columns: Optional[List[str]] = None,
) -> None:
    """
    Validate that the DataFrame contains required columns and types.
    Supports both Pandas and Polars.
    """
    if isinstance(df, pl.DataFrame):
        _validate_polars_dataframe(df, required_columns, numeric_columns)
        return
    _validate_pandas_dataframe(df, required_columns, numeric_columns)


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
            raise ValueError(f"{stage} missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            coerced = _validate_numeric_column(df, col, stage)
            df[col] = coerced


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
    """Check percentage columns are between 0 and 100 inclusive.
    Note:
        NaN values are treated as validation failures.
    """
    if columns is None:
        columns = _default_percentage_columns(df)
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            has_nan = df[col].isna().any()
            in_bounds = ((df[col] >= 0) & (df[col] <= 100)).all()
            validation[f"{col}_in_0_100"] = in_bounds and not has_nan
    return validation


def safe_numeric_polars(df: pl.DataFrame, columns: List[str]) -> pl.DataFrame:
    """
    Polars-native cleaning of numeric columns (currency, commas, etc.).
    """
    for col in columns:
        if col in df.columns and df.schema[col] == pl.String:
            # Vectorized cleaning using Polars regex
            df = df.with_columns(
                pl.col(col).str.replace_all(r"[$€£¥₽₡,]", "").cast(pl.Float64, strict=False)
            )
    return df


def safe_numeric(series: pd.Series) -> pd.Series:
    """Coerce a series to numeric, handling currency symbols and commas.
    Note: If percentages are present (e.g., '50%'), removing '%' yields 50,
    not 0.5. Adjust as needed for your use case.
    """
    if series.dtype == "object":
        # Regex handles currency symbols ($, €, £, ¥, ₽, ₡) and commas
        clean = series.astype(str).str.replace(r"[$€£¥₽₡,]", "", regex=True)
        # To handle percentages as fractions, uncomment the following line:
        # clean = clean.str.replace(
        #     r"(\d+(?:\.\d+)?)\s*%",
        #     lambda m: str(float(m.group(1)) / 100),
        #     regex=True
        # )
        return pd.to_numeric(clean, errors="coerce")
    return pd.to_numeric(series, errors="coerce")


def safe_decimal(value: Any) -> Decimal:
    """Safely convert a value to Decimal, handling currency symbols and commas."""
    if pd.isnull(value):
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    # Handle string with currency symbols and commas
    clean = str(value).translate(str.maketrans("", "", "$€£¥₽₡,"))
    try:
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return Decimal("0")


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
    lower_to_column = {col.lower(): col for col in columns}
    for candidate in candidates:
        match = lower_to_column.get(candidate.lower())
        if match is not None:
            return match

    # 3. Substring match
    for candidate in candidates:
        candidate_lower = candidate.lower()
        match = next((col for col in columns if candidate_lower in col.lower()), None)
        if match is not None:
            return match

    return None


def validate_iso8601_dates(
    df: pd.DataFrame, columns: Optional[List[str]] = None
) -> Dict[str, bool]:
    """
    Check that all values in the specified columns are valid ISO 8601 dates
    (YYYY-MM-DD or full ISO format). Returns a dict mapping column name to
    True/False.
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
