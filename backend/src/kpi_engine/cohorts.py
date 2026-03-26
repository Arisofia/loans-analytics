"""Cohort builder — vintage curves and month-on-book analysis."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


def build_cohorts(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Build cohort table by origination month with default and delinquency rates."""
    if "origination_date" not in portfolio.columns:
        return {"cohorts": [], "summary": "No origination_date column"}

    df = portfolio.copy()
    df["origination_date"] = pd.to_datetime(df["origination_date"], errors="coerce")
    df = df.dropna(subset=["origination_date"])
    if df.empty:
        return {"cohorts": [], "summary": "No valid dates"}

    df["cohort"] = df["origination_date"].dt.to_period("M").astype(str)
    dpd = pd.to_numeric(df.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = df.get("status", pd.Series(dtype=str)).str.lower()
    balance = pd.to_numeric(df.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)

    cohorts: List[Dict[str, Any]] = []
    for cohort_name, group in df.groupby("cohort"):
        g_dpd = pd.to_numeric(group.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
        g_status = group.get("status", pd.Series(dtype=str)).str.lower()
        g_bal = pd.to_numeric(group.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
        n = len(group)
        defaulted = (g_status == "defaulted").sum()
        delinquent = (g_status == "delinquent").sum()
        par30 = (g_dpd >= 30).sum()

        cohorts.append({
            "cohort": str(cohort_name),
            "loan_count": n,
            "total_balance": round(float(g_bal.sum()), 2),
            "default_rate_pct": round(float(defaulted / n * 100), 2) if n > 0 else 0,
            "delinquency_rate_pct": round(float(delinquent / n * 100), 2) if n > 0 else 0,
            "par30_rate_pct": round(float(par30 / n * 100), 2) if n > 0 else 0,
            "avg_dpd": round(float(g_dpd.mean()), 1),
        })

    # Identify best/worst cohorts
    if cohorts:
        sorted_by_default = sorted(cohorts, key=lambda c: c["default_rate_pct"])
        best = sorted_by_default[0]["cohort"]
        worst = sorted_by_default[-1]["cohort"]
    else:
        best = worst = "N/A"

    return {
        "cohorts": cohorts,
        "cohort_count": len(cohorts),
        "best_vintage": best,
        "worst_vintage": worst,
    }
