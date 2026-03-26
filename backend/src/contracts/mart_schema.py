"""Mart-level schemas — decision-grade tables consumed by KPI engine and agents.

Each mart represents a logical domain table built from the canonical
portfolio DataFrame after transformation.  Marts are the ONLY approved
inputs for the KPI engine and agent layer.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class PortfolioMartRecord(BaseModel):
    """Core portfolio fact record — one row per active/delinquent/defaulted loan."""

    loan_id: str
    loan_uid: Optional[str] = None
    borrower_id: str
    status: str  # active | delinquent | defaulted | closed
    amount: Decimal
    current_balance: Decimal = Decimal("0")
    interest_rate: Decimal = Decimal("0")
    dpd: int = 0
    origination_date: Optional[date] = None
    due_date: Optional[date] = None
    term_months: Optional[int] = None
    credit_line: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = "SV"

    model_config = {"from_attributes": True}


class FinanceMartRecord(BaseModel):
    """Finance / P&L record per loan — revenue, cost, margin."""

    loan_id: str
    borrower_id: str
    amount: Decimal
    current_balance: Decimal = Decimal("0")
    interest_rate: Decimal = Decimal("0")
    tpv: Decimal = Decimal("0")
    total_payment_received: Decimal = Decimal("0")
    total_scheduled: Decimal = Decimal("0")
    origination_date: Optional[date] = None
    term_months: Optional[int] = None
    status: str = "active"

    model_config = {"from_attributes": True}


class SalesMartRecord(BaseModel):
    """Sales / CRM record — lead & origination funnel."""

    loan_id: str
    borrower_id: str
    amount: Decimal
    status: str
    origination_date: Optional[date] = None
    credit_line: Optional[str] = None
    kam_hunter: Optional[str] = None
    kam_farmer: Optional[str] = None
    advisory_channel: Optional[str] = None
    sector: Optional[str] = None
    dpd: int = 0
    interest_rate: Decimal = Decimal("0")
    approved_value: Optional[Decimal] = None
    disbursement_count: Optional[int] = None

    model_config = {"from_attributes": True}


class CollectionsMartRecord(BaseModel):
    """Collections record — delinquent account for recovery management."""

    loan_id: str
    borrower_id: str
    status: str
    dpd: int = 0
    current_balance: Decimal = Decimal("0")
    amount: Decimal = Decimal("0")
    last_payment_amount: Decimal = Decimal("0")
    total_payment_received: Decimal = Decimal("0")
    capital_collected: Decimal = Decimal("0")
    total_scheduled: Decimal = Decimal("0")
    collections_eligible: Optional[str] = None
    negotiation_days: Optional[int] = None
    last_payment_date: Optional[date] = None
    due_date: Optional[date] = None
    origination_date: Optional[date] = None

    model_config = {"from_attributes": True}


class TreasuryMartRecord(BaseModel):
    """Treasury / liquidity record — cash position and funding."""

    total_portfolio_balance: Decimal = Decimal("0")
    total_disbursed: Decimal = Decimal("0")
    total_collected: Decimal = Decimal("0")
    total_scheduled: Decimal = Decimal("0")
    active_loan_count: int = 0
    delinquent_loan_count: int = 0
    defaulted_loan_count: int = 0
    collection_rate: Decimal = Decimal("0")
    as_of_date: Optional[date] = None

    model_config = {"from_attributes": True}


class MarketingMartRecord(BaseModel):
    """Marketing / acquisition record — channel performance by cohort."""

    loan_id: str
    borrower_id: str
    amount: Decimal
    status: str
    origination_date: Optional[date] = None
    advisory_channel: Optional[str] = None
    kam_hunter: Optional[str] = None
    credit_line: Optional[str] = None
    dpd: int = 0
    interest_rate: Decimal = Decimal("0")
    tpv: Decimal = Decimal("0")

    model_config = {"from_attributes": True}
