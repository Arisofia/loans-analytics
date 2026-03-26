"""Marketing mart — acquisition channel performance and cohort analysis."""

from __future__ import annotations

import pandas as pd

from backend.src.marts.builder import _col_or_none, _col_or_zero, _safe_decimal


def build(df: pd.DataFrame) -> pd.DataFrame:
    """Build marketing mart from canonical transformed DataFrame."""
    cols = {
        "loan_id": df["loan_id"],
        "borrower_id": df["borrower_id"],
        "amount": _safe_decimal(df["amount"]),
        "status": df["status"],
        "origination_date": _col_or_none(df, "origination_date"),
        "advisory_channel": _col_or_none(df, "advisory_channel"),
        "kam_hunter": _col_or_none(df, "kam_hunter"),
        "credit_line": _col_or_none(df, "credit_line"),
        "dpd": _col_or_zero(df, "dpd").astype(int),
        "interest_rate": _col_or_zero(df, "interest_rate"),
        "tpv": _col_or_zero(df, "tpv"),
    }
    return pd.DataFrame(cols)
