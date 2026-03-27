from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CanonicalLoanRecord(BaseModel):
    loan_id: str
    customer_id: str
    origination_date: date
    due_date: Optional[date] = None
    funded_amount: float = Field(ge=0)
    outstanding_principal: float = Field(ge=0)
    apr: float = Field(ge=0)
    term_days: int = Field(gt=0)
    days_past_due: int = Field(ge=0)
    country: Optional[str] = None
    sector: Optional[str] = None
    originator: Optional[str] = None
    source_channel: Optional[str] = None
    default_flag: bool = False

    @field_validator("loan_id", "customer_id")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Required identifier is empty")
        return value.strip()


class CanonicalPaymentRecord(BaseModel):
    loan_id: str
    payment_date: date
    payment_amount: float = Field(ge=0)
    principal_component: Optional[float] = Field(default=None, ge=0)
    interest_component: Optional[float] = Field(default=None, ge=0)


class CanonicalLeadRecord(BaseModel):
    lead_id: str
    created_at: datetime
    owner: Optional[str] = None
    stage: str
    requested_ticket: Optional[float] = Field(default=None, ge=0)
    approved_ticket: Optional[float] = Field(default=None, ge=0)
    funded_flag: bool = False
    source_channel: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None


class CanonicalAdSpendRecord(BaseModel):
    """Canonical contract for a single Meta Ads (Facebook/Instagram) daily ad record.

    One row = one ad × one day of delivery data. Aggregation to campaign/adset/account
    level happens in the marketing mart, not here.
    """

    date_start: date
    date_stop: date
    account_id: str
    campaign_id: str
    campaign_name: str
    adset_id: Optional[str] = None
    adset_name: Optional[str] = None
    ad_id: Optional[str] = None
    ad_name: Optional[str] = None
    # Delivery metrics
    impressions: int = Field(ge=0)
    reach: int = Field(ge=0)
    clicks: int = Field(ge=0)
    spend: float = Field(ge=0, description="Ad spend in account currency (USD)")
    # Conversion metrics — sourced from Meta pixel / lead objective
    leads: int = Field(default=0, ge=0, description="Lead form completions reported by Meta")
    # Derived ratios — populated by adapter, not API
    ctr: Optional[float] = Field(default=None, ge=0, description="clicks / impressions")
    cpl: Optional[float] = Field(default=None, ge=0, description="spend / leads; None when leads == 0")
    cpc: Optional[float] = Field(default=None, ge=0, description="spend / clicks; None when clicks == 0")

    @field_validator("account_id", "campaign_id", "campaign_name")
    @classmethod
    def validate_non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Required identifier is empty")
        return value.strip()
