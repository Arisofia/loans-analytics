"""Shared KPI formatting helpers for dashboards."""

from __future__ import annotations

from typing import Any

import pandas as pd

KPI_LABEL_OVERRIDES = {
    "total_aum_usd": "Total AUM (USD)",
    "ltv_cac_ratio": "LTV / CAC",
    "par_90_ratio_pct": "PAR 90 Ratio",
    "mom_growth_pct": "MoM Growth",
    "yoy_growth_pct": "YoY Growth",
}


def format_percent(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "—"
    if abs(value) <= 1:
        return f"{value:.2%}"
    return f"{value:.2f}%"


def format_kpi_value(name: str, value: Any) -> str:
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


def kpi_label(name: str) -> str:
    return KPI_LABEL_OVERRIDES.get(name, name.replace("_", " ").title())


def compute_cat_agg(frame: pd.DataFrame) -> pd.DataFrame:
    """Aggregate outstanding loan values by category."""
    if "categoria" not in frame.columns or "outstanding_loan_value" not in frame.columns:
        return pd.DataFrame()
    category_totals = (
        frame.groupby("categoria", dropna=False)["outstanding_loan_value"].sum().reset_index()
    )
    return category_totals
