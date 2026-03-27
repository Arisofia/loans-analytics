"""Treasury features derived from the treasury mart.

Provides liquidity, cash-flow, and funding-position features for agents.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd


def _d(v) -> Decimal:
    try:
        return Decimal(str(v)) if v is not None and str(v) not in ("", "nan", "None") else Decimal(0)
    except Exception:
        return Decimal(0)


def build_treasury_features(treasury: pd.DataFrame) -> dict:
    """Compute derived treasury features from the treasury mart (single-row).

    Returns a flat dict of feature values (not a DataFrame, since treasury
    is an aggregate single-row mart).
    """
    if treasury.empty:
        return _empty_features()

    row = treasury.iloc[0]

    total_balance = _d(row.get("total_portfolio_balance", 0))
    total_disbursed = _d(row.get("total_disbursed", 0))
    total_collected = _d(row.get("total_collected", 0))
    active_count = int(row.get("active_loan_count", 0))
    delinquent_count = int(row.get("delinquent_loan_count", 0))
    defaulted_count = int(row.get("defaulted_loan_count", 0))
    collection_rate = _d(row.get("collection_rate", 0))

    total_loans = active_count + delinquent_count + defaulted_count

    # Net cash position
    net_cash = total_collected - total_disbursed

    # Collection efficiency gap — shortfall from target (98.5%)
    target_rate = Decimal("98.5")
    collection_gap = target_rate - collection_rate

    # Delinquency ratio by count
    delinquency_ratio = (
        Decimal(str(delinquent_count)) / Decimal(str(total_loans)) * 100
        if total_loans > 0
        else Decimal(0)
    )

    # Deployment ratio — how much of disbursed is still outstanding
    deployment_ratio = (
        total_balance / total_disbursed * 100
        if total_disbursed > 0
        else Decimal(0)
    )

    return {
        "net_cash_position": float(net_cash.quantize(Decimal("0.01"))),
        "collection_gap_pct": float(collection_gap.quantize(Decimal("0.01"))),
        "delinquency_ratio_count": float(delinquency_ratio.quantize(Decimal("0.01"))),
        "deployment_ratio": float(deployment_ratio.quantize(Decimal("0.01"))),
        "total_loan_count": total_loans,
        "active_pct": float(
            Decimal(str(active_count)) / Decimal(str(total_loans)) * 100
            if total_loans > 0 else Decimal(0)
        ),
    }


def _empty_features() -> dict:
    return {
        "net_cash_position": 0.0,
        "collection_gap_pct": 0.0,
        "delinquency_ratio_count": 0.0,
        "deployment_ratio": 0.0,
        "total_loan_count": 0,
        "active_pct": 0.0,
    }
