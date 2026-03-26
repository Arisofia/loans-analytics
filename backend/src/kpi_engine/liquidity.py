"""Liquidity metrics — cash position, reserve coverage, funding stress."""

from __future__ import annotations

import logging
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)

# From business_parameters.yml
_MIN_LIQUIDITY_RESERVE_PCT = 0.05
_TARGET_LIQUIDITY_RESERVE_PCT = 0.08
_MIN_LIQUIDITY_FLOOR_USD = 200_000


def compute_liquidity_ratio(treasury: pd.DataFrame) -> Dict[str, Any]:
    """Liquidity ratio = total_collected / total_portfolio_balance."""
    if treasury.empty:
        return {"liquidity_ratio": 0.0, "status": "no_data"}

    row = treasury.iloc[0]
    portfolio = float(row.get("total_portfolio_balance", 0) or 0)
    collected = float(row.get("total_collected", 0) or 0)

    ratio = collected / portfolio if portfolio > 0 else 0.0
    reserve_required = portfolio * _MIN_LIQUIDITY_RESERVE_PCT
    reserve_gap = max(0, reserve_required - collected)

    status = "healthy"
    if ratio < _MIN_LIQUIDITY_RESERVE_PCT:
        status = "critical"
    elif ratio < _TARGET_LIQUIDITY_RESERVE_PCT:
        status = "warning"

    return {
        "liquidity_ratio": round(ratio, 4),
        "total_collected": round(collected, 2),
        "total_portfolio_balance": round(portfolio, 2),
        "reserve_required_usd": round(reserve_required, 2),
        "reserve_gap_usd": round(reserve_gap, 2),
        "min_floor_usd": _MIN_LIQUIDITY_FLOOR_USD,
        "status": status,
    }


def compute_funding_utilization(treasury: pd.DataFrame) -> Dict[str, float]:
    """Funding line utilization = disbursed / portfolio balance."""
    if treasury.empty:
        return {"utilization_pct": 0.0}

    row = treasury.iloc[0]
    disbursed = float(row.get("total_disbursed", 0) or 0)
    portfolio = float(row.get("total_portfolio_balance", 0) or 0)

    return {
        "utilization_pct": round((disbursed / portfolio * 100) if portfolio > 0 else 0, 2),
    }
