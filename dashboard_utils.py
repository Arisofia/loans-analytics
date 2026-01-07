"""Small helpers for the dashboard that are safe to import in tests.

Keep UI-free logic here so unit tests don't need to import `streamlit`.
"""
from __future__ import annotations

import pandas as pd


def compute_cat_agg(df: pd.DataFrame, category_col: str = "categoria", value_col: str = "outstanding_loan_value") -> pd.DataFrame:
    """Return a DataFrame aggregated by category and summed values.

    If either the category or value column is missing, return an empty DataFrame
    with the expected columns (so callers can safely check emptiness).
    """
    if category_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=[category_col, value_col])
    temp_df = df.copy()
    temp_df[value_col] = pd.to_numeric(temp_df[value_col], errors="coerce").fillna(0)
    return temp_df.groupby(category_col)[value_col].sum().reset_index()
