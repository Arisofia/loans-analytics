"""Utilities for normalizing dataframes for KPI calculation."""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class SimpleColumnFinder:
    """Find columns by exact match or case-insensitive match."""

    def __init__(self, df: pd.DataFrame):
        self.columns = list(df.columns)
        self.columns_lower = {col.lower(): col for col in self.columns}

    def find(self, candidates: List[str]) -> Optional[str]:
        for cand in candidates:
            # Exact match
            if cand in self.columns:
                return cand
            # Case-insensitive
            cand_lower = cand.lower()
            if cand_lower in self.columns_lower:
                return self.columns_lower[cand_lower]
        return None


# Standard internal column names
COL_ORIGINATION_DATE = "origination_date"
COL_CUSTOMER_ID = "customer_id"
COL_CLIENT_SEGMENT = "client_segment"
COL_OUTSTANDING_AMOUNT = "total_receivable_usd"
COL_APPROVED_AMOUNT = "approved_limit"
COL_PAYMENT_DATE = "payment_date"
COL_DAYS_PAST_DUE = "days_past_due"
COL_LOAN_AMOUNT = "loan_amount"
COL_APPRAISED_VALUE = "appraised_value"
COL_BORROWER_INCOME = "borrower_income"
COL_MONTHLY_DEBT = "monthly_debt"
COL_LOAN_STATUS = "loan_status"
COL_INTEREST_RATE = "interest_rate"
COL_PRINCIPAL_BALANCE = "principal_balance"
COL_DPD_30_60 = "dpd_30_60_usd"
COL_DPD_60_90 = "dpd_60_90_usd"
COL_DPD_90_PLUS = "dpd_90_plus_usd"

# Mapping from common external names to internal names
COLUMN_MAPPING = {
    COL_ORIGINATION_DATE: ["Origination Date", "measurement_date", "date", "orig_date"],
    COL_CUSTOMER_ID: ["Customer ID", "loan_id", "client_id", "borrower_id"],
    COL_CLIENT_SEGMENT: ["Client Segment", "segment", "classification"],
    COL_OUTSTANDING_AMOUNT: [
        "Outstanding Amount",
        "outstanding_amount",
        "outstanding",
        "balance",
    ],
    COL_APPROVED_AMOUNT: ["Approved Amount", "approved_amount", "loan_limit"],
    COL_PAYMENT_DATE: ["Payment Date", "last_payment_date"],
    COL_DAYS_PAST_DUE: ["Days Past Due", "dpd", "days_overdue"],
    COL_LOAN_AMOUNT: ["Loan Amount", "principal", "amount"],
    COL_APPRAISED_VALUE: ["Appraised Value", "collateral_value", "property_value"],
    COL_BORROWER_INCOME: ["Borrower Income", "annual_income", "income"],
    COL_MONTHLY_DEBT: ["Monthly Debt", "debt_payments", "obligations"],
    COL_LOAN_STATUS: ["Loan Status", "status", "state"],
    COL_INTEREST_RATE: ["Interest Rate", "rate", "apr"],
    COL_PRINCIPAL_BALANCE: ["Principal Balance", "current_principal"],
    COL_DPD_30_60: ["dpd_30_60", "dpd30"],
    COL_DPD_60_90: ["dpd_60_90", "dpd60"],
    COL_DPD_90_PLUS: ["dpd_90_plus", "dpd90"],
}


def normalize_columns(
    df: pd.DataFrame, extra_mapping: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Map various column name variations to standard internal names.

    Args:
        df: Input DataFrame.
        extra_mapping: Optional additional mappings.

    Returns:
        DataFrame with normalized column names.
    """
    if df is None or df.empty:
        return df

    working_df = df.copy()
    mapping = COLUMN_MAPPING.copy()
    if extra_mapping:
        mapping.update(extra_mapping)

    finder = SimpleColumnFinder(working_df)

    renames = {}
    for internal_name, candidates in mapping.items():
        if internal_name in working_df.columns:
            continue

        found = finder.find(candidates)
        if found:
            renames[found] = internal_name

    if renames:
        logger.debug(f"Renaming columns for normalization: {renames}")
        working_df = working_df.rename(columns=renames)

    return working_df


def ensure_columns(
    df: pd.DataFrame, required: List[str], defaults: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Ensure required columns exist, applying normalization first.

    Args:
        df: Input DataFrame.
        required: List of required internal column names.
        defaults: Optional default values for missing columns.

    Returns:
        DataFrame with required columns.
    """
    df = normalize_columns(df)

    working_df = df.copy()
    defaults = defaults or {}

    for col in required:
        if col not in working_df.columns:
            default_val = defaults.get(col, 0.0)
            logger.warning(f"Missing required column '{col}', using default: {default_val}")
            working_df[col] = default_val

    return working_df
