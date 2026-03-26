"""Portfolio mart — core portfolio fact table, one row per loan."""

from __future__ import annotations

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build portfolio mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "loan_uid": _col_or_none(df, "loan_uid"),
        "borrower_id": df["borrower_id"],
        "status": df["status"],
        "amount": _safe_decimal(df["amount"]),
        "current_balance": _col_or_zero(df, "current_balance"),
        "interest_rate": _col_or_zero(df, "interest_rate"),
        "dpd": _col_or_zero(df, "dpd").astype(int),
        "origination_date": _col_or_none(df, "origination_date"),
        "due_date": _col_or_none(df, "due_date"),
        "term_months": _col_or_none(df, "term_months"),
        "credit_line": _col_or_none(df, "credit_line"),
        "sector": _col_or_none(df, "government_sector"),
        "country": pd.Series("SV", index=df.index),
    }
    return pd.DataFrame(cols)
