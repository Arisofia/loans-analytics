"""Capital-adequacy metrics — D/E, D/EBITDA, leverage, ROE, ROA, ROCE.

All computations use Decimal for financial precision.
Inputs come from the finance mart and treasury mart (real data only).
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")


def compute_debt_to_equity(
    total_debt: Decimal,
    total_equity: Decimal,
) -> Dict[str, Any]:
    """D/E ratio.  Returns NaN-safe dict."""
    if total_equity <= _ZERO:
        return {"debt_to_equity": None, "status": "equity_zero"}
    ratio = total_debt / total_equity
    return {"debt_to_equity": float(ratio.quantize(Decimal("0.0001")))}


def compute_debt_to_ebitda(
    total_debt: Decimal,
    ebitda: Decimal,
) -> Dict[str, Any]:
    """D/EBITDA ratio."""
    if ebitda <= _ZERO:
        return {"debt_to_ebitda": None, "status": "ebitda_zero"}
    ratio = total_debt / ebitda
    return {"debt_to_ebitda": float(ratio.quantize(Decimal("0.0001")))}


def compute_leverage_ratio(
    total_assets: Decimal,
    total_equity: Decimal,
) -> Dict[str, Any]:
    """Leverage = Total Assets / Equity."""
    if total_equity <= _ZERO:
        return {"leverage_ratio": None, "status": "equity_zero"}
    ratio = total_assets / total_equity
    return {"leverage_ratio": float(ratio.quantize(Decimal("0.0001")))}


def compute_roe(
    net_income: Decimal,
    total_equity: Decimal,
) -> Dict[str, Any]:
    """Return on Equity = Net Income / Equity."""
    if total_equity <= _ZERO:
        return {"roe": None}
    ratio = (net_income / total_equity) * Decimal("100")
    return {"roe": float(ratio.quantize(Decimal("0.01")))}


def compute_roa(
    net_income: Decimal,
    total_assets: Decimal,
) -> Dict[str, Any]:
    """Return on Assets = Net Income / Total Assets."""
    if total_assets <= _ZERO:
        return {"roa": None}
    ratio = (net_income / total_assets) * Decimal("100")
    return {"roa": float(ratio.quantize(Decimal("0.01")))}


def compute_roce(
    ebit: Decimal,
    capital_employed: Decimal,
) -> Dict[str, Any]:
    """Return on Capital Employed = EBIT / Capital Employed."""
    if capital_employed <= _ZERO:
        return {"roce": None}
    ratio = (ebit / capital_employed) * Decimal("100")
    return {"roce": float(ratio.quantize(Decimal("0.01")))}


def compute_capital_metrics(
    finance_mart: pd.DataFrame,
    treasury_mart: pd.DataFrame,
    equity: Optional[Decimal] = None,
    debt: Optional[Decimal] = None,
) -> Dict[str, Any]:
    """Aggregate capital metrics from mart data.

    When explicit equity/debt are not provided, derive proxies from the
    treasury mart's total_disbursed and total_collected.
    """
    total_disbursed = Decimal(str(treasury_mart["total_disbursed"].iloc[0]))
    total_collected = Decimal(str(treasury_mart["total_collected"].iloc[0]))
    portfolio_balance = Decimal(str(treasury_mart["total_portfolio_balance"].iloc[0]))

    _debt = debt if debt is not None else total_disbursed
    _equity = equity if equity is not None else max(total_collected - total_disbursed, Decimal("1"))

    net_interest = Decimal(str(
        pd.to_numeric(finance_mart.get("interest_rate", pd.Series(dtype=float)), errors="coerce")
        .fillna(0)
        .mul(pd.to_numeric(finance_mart.get("current_balance", pd.Series(dtype=float)), errors="coerce").fillna(0))
        .sum()
    ))

    results: Dict[str, Any] = {}
    results.update(compute_debt_to_equity(_debt, _equity))
    results.update(compute_leverage_ratio(portfolio_balance, _equity))
    results.update(compute_roe(net_interest, _equity))
    results.update(compute_roa(net_interest, portfolio_balance))
    return results
