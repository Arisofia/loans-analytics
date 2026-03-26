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
