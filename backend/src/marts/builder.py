"""Mart builder — constructs all domain marts from the canonical portfolio DataFrame.

Marts are the ONLY approved inputs for the KPI engine and agent layer.
All fields come from real Google Sheets data after transformation phase.
No mock data, no fabricated columns.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict

import pandas as pd

logger = logging.getLogger(__name__)

# Columns that MUST exist after transformation (homologated from DESEMBOLSOS)
_REQUIRED_COLUMNS = {"loan_id", "borrower_id", "amount", "status"}

# Safe numeric coercion
def _safe_decimal(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _col_or_zero(df: pd.DataFrame, col: str) -> pd.Series:
    """Return column as numeric or zero-filled series."""
    if col in df.columns:
        return _safe_decimal(df[col])
    return pd.Series(0.0, index=df.index)


def _col_or_none(df: pd.DataFrame, col: str) -> pd.Series:
    """Return column as-is or None-filled series."""
    if col in df.columns:
        return df[col]
    return pd.Series(None, index=df.index, dtype="object")


def build_all_marts(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Build all domain marts from the canonical transformed DataFrame.

    Returns dict keyed by mart name → DataFrame.
    """
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Canonical DataFrame missing required columns: {missing}")

    logger.info("Building data marts from %d records, %d columns", len(df), len(df.columns))

    marts = {
        "portfolio_mart": _build_portfolio_mart(df),
        "finance_mart": _build_finance_mart(df),
        "sales_mart": _build_sales_mart(df),
        "collections_mart": _build_collections_mart(df),
        "treasury_mart": _build_treasury_mart(df),
        "marketing_mart": _build_marketing_mart(df),
    }

    for name, mart_df in marts.items():
        logger.info("  %s: %d rows, %d columns", name, len(mart_df), len(mart_df.columns))

    return marts


def _build_portfolio_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Core portfolio fact — one row per loan with risk and balance fields."""
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


def _build_finance_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Finance / P&L mart — revenue, cost, margin per loan."""
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


def _build_sales_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Sales / CRM mart — origination funnel and seller performance."""
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


def _build_collections_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Collections mart — delinquent accounts for recovery management."""
    # Include all loans (not just delinquent) so agents can analyze transitions
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


def _build_treasury_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Treasury mart — aggregate cash & liquidity metrics (single row)."""
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
        "as_of_date": datetime.now().strftime("%Y-%m-%d"),
    }
    return pd.DataFrame([row])


def _build_marketing_mart(df: pd.DataFrame) -> pd.DataFrame:
    """Marketing / acquisition mart — channel performance."""
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
