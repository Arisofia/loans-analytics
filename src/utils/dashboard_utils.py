"""Small helpers for the dashboard that are safe to import in tests.

Keep UI-free logic here so unit tests don't need to import `streamlit`.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


def compute_cat_agg(
    df: pd.DataFrame,
    category_col: str = "categoria",
    value_col: str = "outstanding_loan_value",
) -> pd.DataFrame:
    """Return a DataFrame aggregated by category and summed values.

    If either the category or value column is missing, return an empty DataFrame
    with the expected columns (so callers can safely check emptiness).
    """
    if category_col not in df.columns or value_col not in df.columns:
        return pd.DataFrame(columns=[category_col, value_col])
    temp_df = df.copy()
    temp_df[value_col] = pd.to_numeric(temp_df[value_col], errors="coerce").fillna(0)
    return temp_df.groupby(category_col)[value_col].sum().reset_index()


def format_percent(value: float) -> str:
    """Format a float as a percentage string."""
    if abs(value) <= 1:
        return f"{value:.2%}"
    return f"{value:.2f}%"


def format_kpi_value(name: str, value: Any) -> str:
    """Format a KPI value based on its name and type."""
    if value is None or pd.isna(value):
        return "—"
    if isinstance(value, str):
        return value

    name_lower = name.lower()
    if name_lower in {"ltv_cac_ratio", "rotation"}:
        return f"{value:.2f}x"

    percent_hints = (
        "pct",
        "rate",
        "ratio",
        "yield",
        "apr",
        "penetration",
        "recurrence",
    )
    currency_hints = (
        "usd",
        "revenue",
        "outstanding",
        "disbursement",
        "fee",
        "interest",
        "aum",
        "capital",
        "payment",
        "received",
        "sched",
    )
    count_hints = (
        "clients",
        "customers",
        "loans",
        "count",
        "early",
        "late",
        "on_time",
        "fte",
    )

    if any(hint in name_lower for hint in percent_hints):
        return format_percent(float(value))
    if any(hint in name_lower for hint in currency_hints):
        return f"${float(value):,.2f}"
    if any(hint in name_lower for hint in count_hints):
        return f"{float(value):,.0f}"

    return f"{float(value):,.2f}"


KPI_LABEL_OVERRIDES = {
    "total_aum_usd": "Total AUM (USD)",
    "ltv_cac_ratio": "LTV / CAC",
    "par_90_ratio_pct": "PAR 90 Ratio",
    "mom_growth_pct": "MoM Growth",
    "yoy_growth_pct": "YoY Growth",
}


def kpi_label(name: str) -> str:
    """Get a human-readable label for a KPI name."""
    return KPI_LABEL_OVERRIDES.get(name, name.replace("_", " ").title())
