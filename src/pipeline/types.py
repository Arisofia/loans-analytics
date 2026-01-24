from __future__ import annotations

from typing import TypedDict


class ParRow(TypedDict, total=False):
    """TypedDict for a  PAR row (partial keys are allowed)."""

    reporting_date: str
    outstanding_balance_usd: float
    par_0_balance_usd: float
    par_7_balance_usd: float
    par_30_balance_usd: float
    par_60_balance_usd: float
    par_90_balance_usd: float


class FinancialsRow(TypedDict, total=False):
    """TypedDict for /EFF financials row."""

    reporting_date: str
    cash_balance_usd: float
    total_assets_usd: float
    total_liabilities_usd: float
    net_worth_usd: float
    net_income_usd: float


def validate_par_row(row: ParRow) -> bool:  # pragma: no cover - trivial helper
    """Lightweight runtime validation of a ParRow.

    This helper exists primarily to give a clear annotation surface for static
    analysis (mypy). It intentionally keeps runtime checks minimal so it can
    be kept in the pipeline without heavy runtime cost.
    """
    # Minimal runtime check to detect obvious mistakes
    if "reporting_date" in row and not isinstance(row["reporting_date"], str):
        return False
    return True
