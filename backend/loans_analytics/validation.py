from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import polars as pl
from backend.loans_analytics.config import settings

def _missing_columns(df: Any, columns: List[str]) -> List[str]:
    return [col for col in columns if col not in df.columns]

def _validate_numeric_column(df: pd.DataFrame, column: str, context_label: str) -> pd.Series:
    if column not in df.columns:
        raise ValueError(f'{context_label} missing required numeric column: {column}')
    series = df[column]
    if series.dtype == 'object' and series.dropna().apply(lambda value: isinstance(value, str)).any():
        raise ValueError(f'{context_label} must be numeric: {column}')
    coerced = pd.to_numeric(series, errors='coerce')
    if not pd.api.types.is_numeric_dtype(coerced):
        raise ValueError(f'{context_label} must be numeric: {column}')
    return coerced

def _default_percentage_columns(df: pd.DataFrame) -> List[str]:
    exempt_columns = ['collateralization_pct', 'collection_rate_pct']
    return [c for c in df.columns if ('percent' in c or 'rate' in c or c.endswith(('_pct', '_rate'))) and c not in exempt_columns]

def _is_iso8601_string(value: str) -> bool:
    normalized = value.strip()
    if not normalized:
        return False
    if normalized.endswith('Z'):
        normalized = f'{normalized[:-1]}+00:00'
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
NUMERIC_COLUMNS: List[str] = settings.analytics.ingestion_numeric_columns

def _validate_polars_dataframe(df: pl.DataFrame, required_columns: Optional[List[str]], numeric_columns: Optional[List[str]]) -> None:
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            if col not in df.columns:
                raise ValueError(f'Missing required numeric column: {col}')
            if not df.schema[col].is_numeric():
                raise ValueError(f'Column {col} must be numeric')

def _validate_pandas_dataframe(df: pd.DataFrame, required_columns: Optional[List[str]], numeric_columns: Optional[List[str]]) -> None:
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            if len(missing) == 1:
                raise ValueError(f'Missing required column: {missing[0]}')
            raise ValueError(f"Missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            coerced = _validate_numeric_column(df, col, 'Column')
            df[col] = coerced

def validate_dataframe(df: Union[pd.DataFrame, pl.DataFrame], required_columns: Optional[List[str]]=None, numeric_columns: Optional[List[str]]=None) -> None:
    if isinstance(df, pl.DataFrame):
        _validate_polars_dataframe(df, required_columns, numeric_columns)
        return
    _validate_pandas_dataframe(df, required_columns, numeric_columns)

def assert_dataframe_schema(df: pd.DataFrame, *, required_columns: Optional[List[str]]=None, numeric_columns: Optional[List[str]]=None, stage: str='DataFrame') -> None:
    if required_columns:
        missing = _missing_columns(df, required_columns)
        if missing:
            raise ValueError(f"{stage} missing required columns: {', '.join(missing)}")
    if numeric_columns:
        for col in numeric_columns:
            coerced = _validate_numeric_column(df, col, stage)
            df[col] = coerced

def validate_numeric_bounds(df: pd.DataFrame, columns: Optional[List[str]]=None) -> Dict[str, bool]:
    cols_to_check = columns or NUMERIC_COLUMNS
    validation: Dict[str, bool] = {}
    for col in cols_to_check:
        if col in df.columns:
            has_nan = df[col].isna().any()
            has_negative = (df[col] < 0).any()
            validation[f'{col}_no_nulls'] = not has_nan
            validation[f'{col}_non_negative'] = not has_negative
    return validation

def validate_percentage_bounds(df: pd.DataFrame, columns: Optional[List[str]]=None) -> Dict[str, bool]:
    if columns is None:
        columns = _default_percentage_columns(df)
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            has_nan = df[col].isna().any()
            in_bounds = ((df[col] >= 0) & (df[col] <= 100)).all()
            validation[f'{col}_in_0_100'] = in_bounds and (not has_nan)
    return validation

def safe_numeric_polars(df: pl.DataFrame, columns: List[str]) -> pl.DataFrame:
    for col in columns:
        if col in df.columns and df.schema[col] == pl.String:
            df = df.with_columns(pl.col(col).str.replace_all('[$€£¥₽₡,]', '').cast(pl.Float64, strict=False))
    return df

def safe_numeric(series: pd.Series) -> pd.Series:
    if series.dtype == 'object':
        clean = series.astype(str).str.replace('[$€£¥₽₡,]', '', regex=True)
        return pd.to_numeric(clean, errors='coerce')
    return pd.to_numeric(series, errors='coerce')

def safe_decimal(value: Any) -> Decimal:
    if pd.isnull(value):
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    clean = str(value).translate(str.maketrans('', '', '$€£¥₽₡,'))
    if clean.startswith('(') and clean.endswith(')'):
        clean = '-' + clean[1:-1]
    try:
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return Decimal('0')

def find_column(df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
    columns = list(df.columns)
    for candidate in candidates:
        if candidate in columns:
            return candidate
    lower_to_column = {col.lower(): col for col in columns}
    for candidate in candidates:
        match = lower_to_column.get(candidate.lower())
        if match is not None:
            return match
    for candidate in candidates:
        candidate_lower = candidate.lower()
        match = next((col for col in columns if candidate_lower in col.lower()), None)
        if match is not None:
            return match
    return None

def validate_iso8601_dates(df: pd.DataFrame, columns: Optional[List[str]]=None) -> Dict[str, bool]:
    if columns is None:
        columns = [c for c in df.columns if 'date' in c.lower() or c.lower().endswith('_at')]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                validation[f'{col}_iso8601'] = True
                continue
            coerced = pd.to_datetime(df[col], errors='coerce', format='mixed')
            orig_null_mask = df[col].isna()
            validation[f'{col}_iso8601'] = not (coerced.isna() & ~orig_null_mask).any()
    return validation

def validate_monotonic_increasing(df: pd.DataFrame, columns: Optional[List[str]]=None) -> Dict[str, bool]:
    if columns is None:
        columns = [c for c in df.columns if any((x in c.lower() for x in ['count', 'total', 'cumulative']))]
    validation: Dict[str, bool] = {}
    for col in columns:
        if col in df.columns:
            series = df[col].dropna()
            valid = series.is_monotonic_increasing
            validation[f'{col}_monotonic_increasing'] = valid
    return validation
