"""Sales mart — CRM origination funnel and seller performance."""

from __future__ import annotations

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build sales mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "borrower_id": df["borrower_id"],
        "amount": _safe_decimal(df["amount"]),
        "status": df["status"],
        "origination_date": _col_or_none(df, "origination_date"),
        "credit_line": _col_or_none(df, "credit_line"),
        "kam_hunter": _col_or_none(df, "kam_hunter"),
        "kam_farmer": _col_or_none(df, "kam_farmer"),
        "advisory_channel": _col_or_none(df, "advisory_channel"),
        "sector": _col_or_none(df, "government_sector"),
        "dpd": _col_or_zero(df, "dpd").astype(int),
        "interest_rate": _col_or_zero(df, "interest_rate"),
        "approved_value": _col_or_zero(df, "approved_value"),
        "disbursement_count": _col_or_none(df, "disbursement_count"),
    }
    return pd.DataFrame(cols)
