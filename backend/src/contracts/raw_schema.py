"""Raw schema contracts — fields as they arrive from Google Sheets DESEMBOLSOS tab.

These models document the canonical field names AFTER ingestion coercion
(loan_id, amount, status, borrower_id are always present).  All other
fields are optional because Google Sheets columns evolve over time.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class RawLoanRecord(BaseModel):
    """Single loan record after ingestion coercion (Phase 1 output)."""

    # --- Required identifiers (enforced by ingestion) ---
    loan_id: str = Field(..., description="Unique loan identifier (NumeroInterno / NumeroQuedan)")
    borrower_id: str = Field(..., description="Borrower identifier (CodCliente)")
    amount: Decimal = Field(..., description="Approved / disbursed amount (ValorAprobado / MontoDesembolsado)")
    status: str = Field(..., description="Normalized status: active | delinquent | defaulted | closed")

    # --- Financial fields ---
    approved_value: Optional[Decimal] = Field(None, description="Original approved value")
    current_balance: Optional[Decimal] = Field(None, description="Outstanding principal balance")
    interest_rate: Optional[Decimal] = Field(None, description="Annual interest rate")
    tpv: Optional[Decimal] = Field(None, description="Total payment value / revenue per disbursement")
    credit_line: Optional[str] = Field(None, description="Credit line identifier")
    credit_line_range: Optional[str] = Field(None, description="Credit line range bucket")
    guarantee_retained: Optional[Decimal] = Field(None, description="Retained guarantee amount")

    # --- Dates ---
    origination_date: Optional[date] = Field(None, description="Disbursement date (FechaDesembolso)")
    due_date: Optional[date] = Field(None, description="Scheduled payment date (FechaPagoProgramado)")
    last_payment_date: Optional[date] = Field(None, description="Last actual payment date")
    application_date: Optional[date] = Field(None, description="Application / request date")
    as_of_date: Optional[date] = Field(None, description="Cut-off / reporting date (Fecha actual)")

    # --- Delinquency / Risk ---
    dpd: Optional[int] = Field(None, description="Days past due (Dias vencido / mora_en_dias)")
    delinquency_definition: Optional[str] = Field(None, description="Delinquency definition label")
    delinquency_bucket_raw: Optional[str] = Field(None, description="Delinquency bucket string (rango_m)")

    # --- Payments / Collections ---
    last_payment_amount: Optional[Decimal] = Field(None, description="Last payment received")
    total_payment_received: Optional[Decimal] = Field(None, description="Total amount paid to date")
    capital_collected: Optional[Decimal] = Field(None, description="Capital recovered (capitalcobrado)")
    total_scheduled: Optional[Decimal] = Field(None, description="Total amount scheduled for payment")
    recovery_value: Optional[Decimal] = Field(None, description="Recovery value post-default")

    # --- Operational / Segment ---
    kam_hunter: Optional[str] = Field(None, description="KAM Hunter code")
    kam_farmer: Optional[str] = Field(None, description="KAM Farmer code")
    advisory_channel: Optional[str] = Field(None, description="Advisory channel (asesoriadigital)")
    utilization_pct: Optional[Decimal] = Field(None, description="Line utilization percentage")
    collections_eligible: Optional[str] = Field(None, description="Collections flag (Y/N)")
    government_sector: Optional[str] = Field(None, description="GOES flag")
    gov: Optional[str] = Field(None, description="Ministry / government entity")
    mdsc_posted: Optional[str] = Field(None, description="MDSC posted flag (1/0)")

    # --- Derived ---
    loan_uid: Optional[str] = Field(None, description="Composite key: loan_id + origination_date")
    negotiation_days: Optional[int] = Field(None, description="Negotiation days (diasnegociacion)")
    days_to_pay: Optional[int] = Field(None, description="Average days to pay")
    disbursement_count: Optional[int] = Field(None, description="Number of disbursements")
    term_months: Optional[int] = Field(None, description="Loan term in months")

    model_config = {"from_attributes": True}
