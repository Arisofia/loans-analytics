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


def compute_kam_concentration(
    portfolio: pd.DataFrame,
    segment: str | None = None,
) -> Dict[str, Any]:
    """HHI concentration by KAM hunter, optionally filtered by customer segment.

    Parameters
    ----------
    portfolio:
        Portfolio mart DataFrame.  Must contain ``outstanding_principal``
        and ``kam_hunter``.  If ``segment`` is provided, also needs a
        ``segment`` column with values like ``'Nimal'``, ``'Gob'``, ``'OC'``,
        ``'Top'``.
    segment:
        When provided, restricts the analysis to loans belonging to that
        segment (case-insensitive).  Pass ``'Nimal'`` to get KAM
        concentration within the Nimal segment only.

    Returns
    -------
    dict with keys:
        ``segment`` – the filter applied (or ``'all'``),
        ``hhi_index`` – 0–10,000 Herfindahl-Hirschman Index,
        ``concentration_level`` – ``'low'`` / ``'moderate'`` / ``'high'``,
        ``total_portfolio`` – total outstanding filtered,
        ``unique_kams`` – number of distinct KAM hunters,
        ``top_kam`` – name of KAM with largest share,
        ``top_kam_pct`` – share of top KAM as a percentage,
        ``by_kam`` – list[dict] with per-KAM breakdown.
    """
    df = portfolio.copy()

    if "outstanding_principal" not in df.columns:
        logger.warning("compute_kam_concentration: 'outstanding_principal' column missing")
        return {"segment": segment or "all", "hhi_index": 0.0, "concentration_level": "unknown"}

    if "kam_hunter" not in df.columns:
        logger.warning("compute_kam_concentration: 'kam_hunter' column missing")
        return {"segment": segment or "all", "hhi_index": 0.0, "concentration_level": "unknown"}

    if segment is not None:
        if "segment" not in df.columns:
            logger.warning(
                "compute_kam_concentration: 'segment' column missing — "
                "cannot filter by segment '%s'",
                segment,
            )
        else:
            df = df[df["segment"].str.lower() == segment.lower()]
            if df.empty:
                return {
                    "segment": segment,
                    "hhi_index": 0.0,
                    "concentration_level": "unknown",
                    "total_portfolio": 0.0,
                    "unique_kams": 0,
                    "top_kam": None,
                    "top_kam_pct": 0.0,
                    "by_kam": [],
                }

    balance = pd.to_numeric(df["outstanding_principal"], errors="coerce").fillna(0)
    kam = df["kam_hunter"].fillna("Unassigned").astype(str)

    kam_totals = balance.groupby(kam).sum().sort_values(ascending=False)
    total = float(kam_totals.sum())

    if total <= 0:
        return {
            "segment": segment or "all",
            "hhi_index": 0.0,
            "concentration_level": "unknown",
            "total_portfolio": 0.0,
            "unique_kams": int(len(kam_totals)),
            "top_kam": None,
            "top_kam_pct": 0.0,
            "by_kam": [],
        }

    shares = kam_totals / total
    hhi = float((shares ** 2).sum() * 10_000)

    level = "low"
    if hhi >= 2500:
        level = "high"
    elif hhi >= 1500:
        level = "moderate"

    top_kam = str(kam_totals.index[0])
    top_kam_pct = round(float(shares.iloc[0] * 100), 2)

    by_kam = [
        {
            "kam": str(k),
            "outstanding": round(float(v), 2),
            "share_pct": round(float(shares[k] * 100), 2),
        }
        for k, v in kam_totals.items()
    ]

    return {
        "segment": segment or "all",
        "hhi_index": round(hhi, 2),
        "concentration_level": level,
        "total_portfolio": round(total, 2),
        "unique_kams": int(len(kam_totals)),
        "top_kam": top_kam,
        "top_kam_pct": top_kam_pct,
        "by_kam": by_kam,
    }
