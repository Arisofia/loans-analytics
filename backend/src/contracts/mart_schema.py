from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class PortfolioMartRow(BaseModel):
    loan_id: str
    customer_id: str
    origination_date: date
    origination_month: str
    cohort: str
    vintage: str
    funded_amount: Decimal = Field(ge=Decimal("0"))
    outstanding_principal: Decimal = Field(ge=Decimal("0"))
    apr: float = Field(ge=0)
    term_days: int = Field(gt=0)
    days_past_due: int = Field(ge=0)
    dpd_bucket: str
    default_flag: bool
    country: Optional[str] = None
    sector: Optional[str] = None
    originator: Optional[str] = None
    source_channel: Optional[str] = None


class FinanceMartRow(BaseModel):
    as_of_month: str
    interest_income: Decimal
    fee_income: Decimal
    funding_cost: Decimal
    gross_margin: Decimal
    provision_expense: Decimal
    ebitda_proxy: Decimal
    debt_balance: Decimal
    equity_balance: Decimal


class SalesMartRow(BaseModel):
    lead_id: str
    lead_created_at: str
    owner: Optional[str] = None
    stage: str
    source_channel: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    requested_ticket: Optional[Decimal] = None
    approved_ticket: Optional[Decimal] = None
    funded_flag: bool
    days_to_close: Optional[int] = None
