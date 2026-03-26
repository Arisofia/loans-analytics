"""Concentration metrics — HHI, top-N obligor exposure."""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

_MAX_TOP10_CONCENTRATION = 0.30  # 30% from business_parameters.yml


def compute_hhi(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Herfindahl-Hirschman Index by borrower."""
    balance = pd.to_numeric(
        portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    borrower = portfolio.get("borrower_id", pd.Series(dtype=str))

    borrower_totals = balance.groupby(borrower).sum()
    total = borrower_totals.sum()
    if total <= 0:
        return {"hhi_index": 0.0, "concentration_level": "unknown"}

    shares = borrower_totals / total
    hhi = float((shares ** 2).sum() * 10000)

    level = "low"
    if hhi >= 2500:
        level = "high"
    elif hhi >= 1500:
        level = "moderate"

    return {
        "hhi_index": round(hhi, 2),
        "concentration_level": level,
        "unique_borrowers": int(len(borrower_totals)),
    }


def compute_top_n(portfolio: pd.DataFrame) -> Dict[str, float]:
    """Top-N obligor concentration (1, 5, 10, 20)."""
    balance = pd.to_numeric(
        portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    borrower = portfolio.get("borrower_id", pd.Series(dtype=str))

    borrower_totals = balance.groupby(borrower).sum().sort_values(ascending=False)
    total = borrower_totals.sum()
    if total <= 0:
        return {"top_1_pct": 0.0, "top_5_pct": 0.0, "top_10_pct": 0.0, "top_20_pct": 0.0}

    def _top(n: int) -> float:
        return round(float(borrower_totals.head(n).sum() / total * 100), 2)

    top10 = _top(10)
    return {
        "top_1_pct": _top(1),
        "top_5_pct": _top(5),
        "top_10_pct": top10,
        "top_20_pct": _top(20),
        "exceeds_limit": top10 > (_MAX_TOP10_CONCENTRATION * 100),
    }
