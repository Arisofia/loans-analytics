from __future__ import annotations
import pandas as pd

def first_matching_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    return next((col for col in candidates if col in df.columns), None)

# Canonical short alias used throughout the kpis package.
_col = first_matching_column

def to_numeric_safe(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors='coerce').fillna(0.0)

def resolve_dpd_heuristic(df: pd.DataFrame) -> pd.Series:
    if (dpd_col := first_matching_column(df, ['days_past_due', 'dpd', 'dpd_days'])):
        return to_numeric_safe(df[dpd_col]).clip(lower=0)
    status_col = first_matching_column(df, ['loan_status', 'status', 'current_status'])
    if not status_col:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)
    status = df[status_col].astype(str).str.lower()
    dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
    dpd = dpd.mask(status.str.contains('90\\+|default|charged', regex=True, na=False), 100.0)
    dpd = dpd.mask(status.str.contains('60-89|60\\+', regex=True, na=False), 75.0)
    dpd = dpd.mask(status.str.contains('30-59|30\\+', regex=True, na=False), 45.0)
    return dpd
