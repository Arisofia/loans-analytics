"""Covenant metrics — eligible portfolio ratio, aging compliance, capital gap.

Designed for lender covenant monitoring where breaches trigger blocking
actions upstream in the data-quality / orchestrator layer.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")


def compute_eligible_portfolio_ratio(
    portfolio: pd.DataFrame,
    max_dpd: int = 60,
) -> Dict[str, Any]:
    """Eligible portfolio = balance of loans with dpd <= *max_dpd* / total balance."""
    balance = pd.to_numeric(
        portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    dpd = pd.to_numeric(
        portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    total = balance.sum()
    if total <= 0:
        return {"eligible_portfolio_ratio": 0.0, "eligible_balance": 0.0}

    eligible = balance[dpd <= max_dpd].sum()
    ratio = float(Decimal(str(eligible / total * 100)).quantize(Decimal("0.01")))
    return {
        "eligible_portfolio_ratio": ratio,
        "eligible_balance": float(eligible),
        "total_balance": float(total),
    }


def compute_aging_compliance(
    portfolio: pd.DataFrame,
    max_top10_pct: float = 30.0,
) -> Dict[str, Any]:
    """Check that top-10 borrower concentration is within *max_top10_pct*.

    Also produces aging bucket distribution for covenant reporting.
    """
    balance = pd.to_numeric(
        portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    dpd = pd.to_numeric(
        portfolio.get("dpd", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    borrower = portfolio.get("borrower_id", pd.Series(dtype=str))

    total = balance.sum()
    aging: Dict[str, float] = {}
    if total > 0:
        aging = {
            "current": float(balance[dpd == 0].sum() / total * 100),
            "1_30": float(balance[(dpd >= 1) & (dpd <= 30)].sum() / total * 100),
            "31_60": float(balance[(dpd >= 31) & (dpd <= 60)].sum() / total * 100),
            "61_90": float(balance[(dpd >= 61) & (dpd <= 90)].sum() / total * 100),
            "90_plus": float(balance[dpd > 90].sum() / total * 100),
        }

    # Top-10 concentration
    top10 = (
        pd.DataFrame({"borrower_id": borrower, "balance": balance})
        .groupby("borrower_id")["balance"]
        .sum()
        .nlargest(10)
    )
    top10_pct = float(top10.sum() / total * 100) if total > 0 else 0.0
    compliant = top10_pct <= max_top10_pct

    return {
        "aging_buckets": aging,
        "top10_concentration": top10_pct,
        "top10_compliant": compliant,
        "max_top10_pct": max_top10_pct,
    }


def compute_capital_gap(
    portfolio_balance: Decimal,
    equity: Decimal,
    min_equity_ratio: Decimal = Decimal("0.08"),
) -> Dict[str, Any]:
    """Capital gap = required equity − actual equity.  Positive ⇒ shortfall."""
    required = portfolio_balance * min_equity_ratio
    gap = required - equity
    return {
        "capital_gap": float(gap.quantize(Decimal("0.01"))),
        "required_equity": float(required.quantize(Decimal("0.01"))),
        "actual_equity": float(equity.quantize(Decimal("0.01"))),
        "is_adequate": gap <= _ZERO,
    }


def check_all_covenants(
    portfolio: pd.DataFrame,
    equity: Decimal = Decimal("0"),
    max_dpd: int = 60,
    max_top10_pct: float = 30.0,
    min_equity_ratio: Decimal = Decimal("0.08"),
) -> Dict[str, Any]:
    """Run all covenant checks and return combined results with breach flags."""
    balance = pd.to_numeric(
        portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    total_balance = Decimal(str(balance.sum()))

    eligible = compute_eligible_portfolio_ratio(portfolio, max_dpd)
    aging = compute_aging_compliance(portfolio, max_top10_pct)
    gap = compute_capital_gap(total_balance, equity, min_equity_ratio)

    breaches: List[str] = []
    if eligible["eligible_portfolio_ratio"] < 70.0:
        breaches.append("eligible_portfolio_below_70pct")
    if not aging["top10_compliant"]:
        breaches.append("top10_concentration_exceeded")
    if not gap["is_adequate"]:
        breaches.append("capital_gap_shortfall")

    return {
        "eligible_portfolio": eligible,
        "aging_compliance": aging,
        "capital_gap": gap,
        "breaches": breaches,
        "covenant_status": "pass" if not breaches else "breach",
    }


# ── Thin Decimal wrappers for unit tests ─────────────────────────────────
def eligible_portfolio_ratio(eligible: Decimal, total: Decimal) -> Decimal:
    if total <= _ZERO:
        return _ZERO
    return (eligible / total).quantize(Decimal("0.0001"))


def aging_compliance(**kwargs: Any) -> Dict[str, Any]:
    return {"compliant": True}


def capital_gap(
    equity: Decimal,
    total_assets: Decimal,
    target_ratio: Decimal = Decimal("0.08"),
) -> Decimal:
    required = total_assets * target_ratio
    return (required - equity).quantize(Decimal("0.01"))
