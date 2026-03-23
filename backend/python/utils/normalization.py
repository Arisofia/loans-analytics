from __future__ import annotations
import pandas as pd

def clean_numeric(series: pd.Series) -> pd.Series:
    if series.dtype == 'object':
        sample = series.dropna().astype(str).head(50)
        cleaned = sample.str.replace('[$,€%₡,]', '', regex=True)
        numeric_ratio = pd.to_numeric(cleaned, errors='coerce').notna().mean()
        if numeric_ratio >= 0.6:
            series = pd.to_numeric(series.astype(str).str.replace('[$,€%₡,]', '', regex=True), errors='coerce')
    return series

def normalize_dataframe_complete(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    normalized.columns = normalized.columns.astype(str).str.lower().str.strip().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)
    for column in normalized.columns:
        normalized[column] = clean_numeric(normalized[column])
    return normalized
