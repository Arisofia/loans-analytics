"""Unit economics — avg ticket, repeat rate, contribution margin."""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


def compute_avg_ticket(sales: pd.DataFrame) -> Dict[str, float]:
    """Average ticket (loan amount) across all originations."""
    amount = pd.to_numeric(sales.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0)
    return {"avg_ticket": round(float(amount.mean()), 2) if len(amount) > 0 else 0.0}


def compute_repeat_rate(sales: pd.DataFrame) -> Dict[str, float]:
    """Repeat borrower rate: borrowers with >1 loan / total borrowers."""
    borrowers = sales.get("borrower_id", pd.Series(dtype=str))
    counts = borrowers.value_counts()
    total = len(counts)
    if total == 0:
        return {"repeat_borrower_rate_pct": 0.0}
    repeats = (counts > 1).sum()
    return {
        "repeat_borrower_rate_pct": round(float(repeats / total * 100), 2),
        "repeat_borrowers": int(repeats),
        "total_unique_borrowers": total,
    }


def compute_contribution_margin(finance: pd.DataFrame) -> Dict[str, float]:
    """Contribution margin = total revenue - total cost proxy."""
    tpv = pd.to_numeric(finance.get("tpv", pd.Series(dtype=float)), errors="coerce").fillna(0)
    amount = pd.to_numeric(finance.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0)
    total_revenue = float(tpv.sum())
    total_cost = float(amount.sum()) * 0.08  # funding cost proxy

    return {
        "total_revenue": round(total_revenue, 2),
        "total_cost_proxy": round(total_cost, 2),
        "contribution_margin": round(total_revenue - total_cost, 2),
    }
