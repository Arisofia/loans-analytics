"""Customer-level features aggregated from portfolio mart.

Groups loan-level data by borrower_id to produce customer-centric
features consumed by segmentation, retention, and marketing agents.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def build_customer_features(portfolio: pd.DataFrame) -> pd.DataFrame:
    """Aggregate loan records to one row per customer.

    Returns a DataFrame indexed by ``borrower_id``.
    """
    if "borrower_id" not in portfolio.columns:
        return pd.DataFrame()

    df = portfolio.copy()
    amt = pd.to_numeric(df.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0)
    dpd = pd.to_numeric(df.get("dpd", pd.Series(dtype=float)), errors="coerce").fillna(0)
    df["_amount"] = amt
    df["_dpd"] = dpd

    agg: Dict[str, Any] = {
        "_amount": ["sum", "mean", "count"],
        "_dpd": ["max", "mean"],
    }

    grouped = df.groupby("borrower_id").agg(agg)
    grouped.columns = [
        "total_exposure",
        "avg_ticket",
        "loan_count",
        "max_dpd",
        "avg_dpd",
    ]
    grouped["is_repeat"] = grouped["loan_count"] > 1

    # Worst status
    if "status" in df.columns:
        worst = (
            df.groupby("borrower_id")["status"]
            .apply(lambda s: _worst_status(s))
        )
        grouped["worst_status"] = worst

    return grouped.reset_index()


def _worst_status(statuses: pd.Series) -> str:
    """Return the worst status across all loans for a customer."""
    priority = {"defaulted": 0, "delinquent": 1, "active": 2, "closed": 3}
    worst = "closed"
    for s in statuses:
        s_lower = str(s).lower().strip()
        if priority.get(s_lower, 99) < priority.get(worst, 99):
            worst = s_lower
    return worst
