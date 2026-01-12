"""Utilities for normalizing dataframes for KPI calculation."""

import logging
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from src.utils.numeric import safe_numeric

logger = logging.getLogger(__name__)


def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Lowercase, strip, replace spaces with underscores, and remove special characters from column names.
    """
    df = df.copy()
    df.columns = [
        re.sub(r"[^a-z0-9_]", "", str(col).lower().strip().replace(" ", "_")) for col in df.columns
    ]
    return df


def normalize_dataframe_complete(
    df: pd.DataFrame, extra_mapping: Optional[Dict[str, List[str]]] = None
) -> pd.DataFrame:
    """
    Perform complete normalization: sanitize names, map columns, and convert to numeric.
    """
    if df is None or df.empty:
        return df

    # 1. Sanitize column names
    df = sanitize_column_names(df)

    # 2. Map columns
    df = normalize_columns(df, extra_mapping=extra_mapping)

    # 3. Convert all columns to numeric where possible
    for col in df.columns:
        df[col] = safe_numeric(df[col])

    return df


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
COL_OUTSTANDING_AMOUNT = "outstanding_loan_value"  # Aligned with app.py
COL_APPROVED_AMOUNT = "approved_limit"
COL_PAYMENT_DATE = "payment_date"
COL_DAYS_PAST_DUE = "days_past_due"
COL_LOAN_AMOUNT = "loan_amount"
COL_APPRAISED_VALUE = "appraised_value"
COL_BORROWER_INCOME = "borrower_income"
COL_MONTHLY_DEBT = "monthly_debt"
COL_LOAN_STATUS = "loan_status"
COL_INTEREST_RATE = "interest_rate_apr"  # Aligned with app.py
COL_PRINCIPAL_BALANCE = "principal_balance"
COL_LOAN_ID = "loan_id"
COL_SALES_AGENT = "sales_agent"
COL_CATEGORIA = "categoria"
COL_DPD_30_60 = "dpd_30_60_usd"
COL_DPD_60_90 = "dpd_60_90_usd"
COL_DPD_90_PLUS = "dpd_90_plus_usd"

# Mapping from common external names to internal names
COLUMN_MAPPING = {
    COL_ORIGINATION_DATE: ["Origination Date", "measurement_date", "date", "orig_date"],
    COL_CUSTOMER_ID: ["Customer ID", "client_id", "customer_number", "id_cliente", "borrower_id"],
    COL_CLIENT_SEGMENT: ["Client Segment", "segment", "classification"],
    COL_OUTSTANDING_AMOUNT: [
        "Outstanding Amount",
        "outstanding_amount",
        "outstanding_principal",
        "current_outstanding_principal",
        "total_pendiente",
        "saldo_pendiente",
        "current_balance",
        "outstanding_balance",
        "outstanding_balance_usd",
        "aum",
        "balance",
    ],
    COL_APPROVED_AMOUNT: ["Approved Amount", "approved_amount", "loan_limit"],
    COL_PAYMENT_DATE: ["Payment Date", "last_payment_date"],
    COL_DAYS_PAST_DUE: ["Days Past Due", "dpd", "days_overdue"],
    COL_LOAN_AMOUNT: ["Loan Amount", "principal", "amount"],
    COL_APPRAISED_VALUE: ["Appraised Value", "collateral_value", "property_value"],
    COL_BORROWER_INCOME: ["Borrower Income", "annual_income", "income"],
    COL_MONTHLY_DEBT: ["Monthly Debt", "debt_payments", "obligations"],
    COL_LOAN_STATUS: ["Loan Status", "status", "estado", "loan_state", "state"],
    COL_INTEREST_RATE: ["Interest Rate", "rate", "apr", "tasa_interes", "annual_percentage_rate"],
    COL_PRINCIPAL_BALANCE: ["Principal Balance", "current_principal"],
    COL_LOAN_ID: ["id", "loan_number", "contrato", "loan_id_raw", "loan_id"],
    COL_SALES_AGENT: ["agent", "vendedor", "kam", "sales_person", "sales_agent"],
    COL_CATEGORIA: [
        "category",
        "segment",
        "segmento",
        "product_category",
        "product_type",
        "categoria",
    ],
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
