"""Collections mart — delinquent accounts for recovery management."""

from __future__ import annotations

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build collections mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "borrower_id": df["borrower_id"],
        "status": df["status"],
        "dpd": _col_or_zero(df, "dpd").astype(int),
        "current_balance": _col_or_zero(df, "current_balance"),
        "amount": _safe_decimal(df["amount"]),
        "last_payment_amount": _col_or_zero(df, "last_payment_amount"),
        "total_payment_received": _col_or_zero(df, "total_payment_received"),
        "capital_collected": _col_or_zero(df, "capital_collected"),
        "total_scheduled": _col_or_zero(df, "total_scheduled"),
        "collections_eligible": _col_or_none(df, "collections_eligible"),
        "negotiation_days": _col_or_none(df, "negotiation_days"),
        "last_payment_date": _col_or_none(df, "last_payment_date"),
        "due_date": _col_or_none(df, "due_date"),
        "origination_date": _col_or_none(df, "origination_date"),
    }
    return pd.DataFrame(cols)
