"""Shared DataFrame column-lookup and heuristic DPD helpers.

Single source of truth for column-resolution and status-based DPD
estimation used by ``unit_economics`` and ``advanced_risk``.
"""

from __future__ import annotations

import pandas as pd


def first_matching_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Return the first column name from *candidates* that exists in *df*."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """Coerce *series* to float, filling non-numeric values with 0.0."""
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def resolve_dpd_heuristic(df: pd.DataFrame) -> pd.Series:
    """Estimate DPD from a flat loan-tape DataFrame.

    1. If a ``days_past_due`` / ``dpd`` / ``dpd_days`` column exists,
       return it clipped to >= 0.
    2. Otherwise, derive synthetic DPD from ``loan_status`` using
       regex-based bucket mapping.
    3. Falls back to a zero series if no usable column is found.
    """
    dpd_col = first_matching_column(df, ["days_past_due", "dpd", "dpd_days"])
    if dpd_col:
        return to_numeric_safe(df[dpd_col]).clip(lower=0)

    status_col = first_matching_column(df, ["loan_status", "status", "current_status"])
    if not status_col:
        return pd.Series([0.0] * len(df), index=df.index, dtype=float)

    status = df[status_col].astype(str).str.lower()
    dpd = pd.Series([0.0] * len(df), index=df.index, dtype=float)
    dpd = dpd.mask(status.str.contains(r"90\+|default|charged", regex=True, na=False), 100.0)
    dpd = dpd.mask(status.str.contains(r"60-89|60\+", regex=True, na=False), 75.0)
    dpd = dpd.mask(status.str.contains(r"30-59|30\+", regex=True, na=False), 45.0)
    return dpd
