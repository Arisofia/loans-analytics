"""Finance mart — P&L, revenue, cost, margin per loan."""

from __future__ import annotations

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build finance mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "borrower_id": df["borrower_id"],
        "amount": _safe_decimal(df["amount"]),
        "current_balance": _col_or_zero(df, "current_balance"),
        "interest_rate": _col_or_zero(df, "interest_rate"),
        "tpv": _col_or_zero(df, "tpv"),
        "total_payment_received": _col_or_zero(df, "total_payment_received"),
        "total_scheduled": _col_or_zero(df, "total_scheduled"),
        "origination_date": _col_or_none(df, "origination_date"),
        "term_months": _col_or_none(df, "term_months"),
        "status": df["status"],
    }
    return pd.DataFrame(cols)
