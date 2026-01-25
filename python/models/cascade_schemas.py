"""Pydantic models describing Cascade API responses used by the pipeline."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RiskLoanRecord(BaseModel):
    """Single loan record from the Cascade risk analytics endpoint."""

    loan_id: str = Field(..., description="Unique loan identifier in Cascade.")
    client_id: str = Field(..., description="Client identifier owning the loan.")
    principal: Decimal = Field(..., description="Outstanding principal amount.")
    dpd: int = Field(..., description="Days past due.")
    status: Optional[str] = Field(default=None, description="Operational status in Cascade.")


class RiskAnalyticsResponse(BaseModel):
    """Top-level response for the risk analytics endpoint."""

    as_of: datetime = Field(..., description="Timestamp of the snapshot in Cascade.")
    loans: list[RiskLoanRecord] = Field(..., description="List of loan-level risk attributes.")


class CollectionRateRecord(BaseModel):
    """Collection rate payload from Cascade."""

    period_start: datetime = Field(..., description="Window start date for the collection metric.")
    period_end: datetime = Field(..., description="Window end date for the collection metric.")
    scheduled: Decimal = Field(..., description="Amount scheduled to be collected in the window.")
    collected: Decimal = Field(..., description="Amount actually collected in the window.")


class CollectionResponse(BaseModel):
    """Collections endpoint response."""

    as_of: datetime = Field(..., description="Timestamp of the collection extract.")
    items: list[CollectionRateRecord]
