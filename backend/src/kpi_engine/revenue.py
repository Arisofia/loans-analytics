"""Revenue metrics — AUM, yield, NIM, disbursement volume, collection rate."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

_FUNDING_COST_PCT = 8.0  # Cost of debt from business_parameters.yml


def compute_aum(portfolio: pd.DataFrame) -> Dict[str, float]:
    """Total Assets Under Management (outstanding balance of active+delinquent)."""
    balance = pd.to_numeric(portfolio.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = portfolio.get("status", pd.Series(dtype=str)).str.lower()
    active_mask = status.isin(["active", "delinquent"])
    return {
        "total_aum": round(float(balance[active_mask].sum()), 2),
        "total_balance_all": round(float(balance.sum()), 2),
        "active_count": int(active_mask.sum()),
    }


def compute_yield(finance: pd.DataFrame) -> Dict[str, float]:
    """Portfolio yield = weighted average interest rate on active book."""
    balance = pd.to_numeric(finance.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0)
    rate = pd.to_numeric(finance.get("interest_rate", pd.Series(dtype=float)), errors="coerce").fillna(0)
    status = finance.get("status", pd.Series(dtype=str)).str.lower()

    active = status.isin(["active", "delinquent"])
    active_bal = balance[active]
    active_rate = rate[active]
    total_bal = active_bal.sum()

    if total_bal <= 0:
        return {"portfolio_yield_pct": 0.0}

    weighted = (active_rate * active_bal).sum() / total_bal
    return {"portfolio_yield_pct": round(float(weighted), 4)}


def compute_nim(finance: pd.DataFrame) -> Dict[str, float]:
    """Net Interest Margin = (yield - funding_cost)."""
    y = compute_yield(finance)
    yield_pct = y["portfolio_yield_pct"]
    nim = yield_pct - _FUNDING_COST_PCT
    return {
        "nim_pct": round(nim, 4),
        "yield_pct": yield_pct,
        "funding_cost_pct": _FUNDING_COST_PCT,
    }


def compute_collection_rate(collections: pd.DataFrame) -> Dict[str, float]:
    """Collection rate = total collected / total scheduled."""
    collected = pd.to_numeric(
        collections.get("total_payment_received", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0).sum()
    scheduled = pd.to_numeric(
        collections.get("total_scheduled", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0).sum()

    if scheduled <= 0:
        return {"collection_rate_pct": 0.0}
    return {
        "collection_rate_pct": round(float(collected / scheduled * 100), 2),
        "total_collected": round(float(collected), 2),
        "total_scheduled": round(float(scheduled), 2),
    }


def compute_disbursement_mtd(sales: pd.DataFrame) -> Dict[str, Any]:
    """Disbursement volume for current month."""
    if "origination_date" not in sales.columns:
        return {"disbursement_volume_mtd": 0.0, "new_loans_mtd": 0}

    dates = pd.to_datetime(sales["origination_date"], errors="coerce")
    now = datetime.now()
    mtd_mask = (dates.dt.year == now.year) & (dates.dt.month == now.month)
    amount = pd.to_numeric(sales.get("amount", pd.Series(dtype=float)), errors="coerce").fillna(0)

    return {
        "disbursement_volume_mtd": round(float(amount[mtd_mask].sum()), 2),
        "new_loans_mtd": int(mtd_mask.sum()),
    }


def compute_new_loans_mtd(sales: pd.DataFrame) -> Dict[str, int]:
    """Count of new originations for current month."""
    result = compute_disbursement_mtd(sales)
    return {"new_loans_mtd": result["new_loans_mtd"]}
