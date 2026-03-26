from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PortfolioMartRow(BaseModel):
    loan_id: str
    customer_id: str
    origination_date: date
    origination_month: str
    cohort: str
    vintage: str
    funded_amount: float = Field(ge=0)
    outstanding_principal: float = Field(ge=0)
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
    interest_income: float
    fee_income: float
    funding_cost: float
    gross_margin: float
    provision_expense: float
    ebitda_proxy: float
    debt_balance: float
    equity_balance: float


class SalesMartRow(BaseModel):
    lead_id: str
    lead_created_at: str
    owner: Optional[str] = None
    stage: str
    source_channel: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    requested_ticket: Optional[float] = None
    approved_ticket: Optional[float] = None
    funded_flag: bool
    days_to_close: Optional[int] = None
