"""Treasury mart — aggregate cash & liquidity metrics (single row)."""

from __future__ import annotations

import datetime
from decimal import Decimal

import pandas as pd

from backend.src.marts.builder import _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build treasury mart from canonical transformed DataFrame."""
    amount = _safe_decimal(df["amount"])
    balance = _col_or_zero(df, "current_balance")
    collected = _col_or_zero(df, "total_payment_received")
    scheduled = _col_or_zero(df, "total_scheduled")

    active_mask = df["status"].str.lower() == "active"
    delinquent_mask = df["status"].str.lower() == "delinquent"
    defaulted_mask = df["status"].str.lower() == "defaulted"

    total_sched = scheduled.sum()
    total_coll = collected.sum()
    coll_rate = (total_coll / total_sched * 100) if total_sched > 0 else Decimal("0")

    row = {
        "total_portfolio_balance": balance.sum(),
        "total_disbursed": amount.sum(),
        "total_collected": total_coll,
        "cash_on_hand": total_coll - amount.sum(),
        "total_scheduled": total_sched,
        "active_loan_count": int(active_mask.sum()),
        "delinquent_loan_count": int(delinquent_mask.sum()),
        "defaulted_loan_count": int(defaulted_mask.sum()),
        "collection_rate": float(coll_rate),
        "as_of_date": datetime.datetime.now().strftime("%Y-%m-%d"),
    }
    return pd.DataFrame([row])
