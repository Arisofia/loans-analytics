from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# --- Schemas from openapi.yaml ---


class LoanRecord(BaseModel):
    id: Optional[str] = Field(None, description="Loan identifier")
    loan_amount: float = Field(..., description="Original loan amount")
    appraised_value: float = Field(
        ...,
        description="Appraised value of the collateral property",
    )
    borrower_income: float = Field(..., description="Annual borrower income")
    monthly_debt: float = Field(..., description="Monthly debt obligations")
    loan_status: str = Field(
        ...,
        description="Current loan status",
        examples=["current", "30-59 days past due", "90+ days past due"],
    )
    interest_rate: float = Field(
        ...,
        description="Annual interest rate as decimal (e.g., 0.035 for 3.5%)",
        ge=0,
        le=1,
    )
    principal_balance: float = Field(..., description="Current outstanding principal balance")


class LoanPortfolioRequest(BaseModel):
    loans: Optional[List[LoanRecord]] = Field(
        None,
        min_items=0,
        max_items=10000,
        description="Array of loan records for analysis",
    )
    ltv_threshold: Optional[float] = Field(
        80.0,
        description="LTV threshold for risk alerts (default: 80.0)",
    )
    dti_threshold: Optional[float] = Field(
        50.0,
        description="DTI threshold for risk alerts (default: 50.0)",
    )
    # Adding loan_ids here for backwards compatibility if needed.
    # Primary input remains 'loans'.
    # loan_ids: Optional[List[str]] = Field(
    #     None,
    #     description="Optional list of loan IDs for filtering/context",
    # )


class KpiContext(BaseModel):
    metric: Optional[str] = Field(None, description="Name of the KPI metric")
    timestamp: Optional[datetime] = Field(None, description="Calculation timestamp")
    formula: Optional[str] = Field(None, description="Formula used for calculation")
    sample_size: Optional[int] = Field(None, description="Number of records used in calculation")
    period: str
    calculation_date: datetime
    filters: Optional[Dict[str, Any]] = None


class KpiSingleResponse(BaseModel):
    id: Optional[str] = Field(None, description="KPI identifier")
    name: Optional[str] = Field(None, description="KPI display name")
    value: float = Field(..., description="Calculated KPI value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    context: KpiContext


class KpiResponse(BaseModel):
    PAR30: Optional[KpiSingleResponse] = None
    PAR90: Optional[KpiSingleResponse] = None
    CollectionRate: Optional[KpiSingleResponse] = None
    PortfolioHealth: Optional[KpiSingleResponse] = None
    LTV: Optional[KpiSingleResponse] = None
    DTI: Optional[KpiSingleResponse] = None
    PortfolioYield: Optional[KpiSingleResponse] = None
    # Changed from AuditEntry as it's not defined in this file.
    audit_trail: Optional[List[Dict[str, Any]]] = None


class RiskLoan(BaseModel):
    loan_id: str
    risk_score: float
    alerts: List[str]


class RiskAlertsResponse(BaseModel):
    high_risk_count: Optional[int] = Field(
        None,
        description="Number of high-risk loans identified",
    )
    total_loans: Optional[int] = Field(
        None,
        description="Total loans analyzed",
    )
    risk_ratio: Optional[float] = Field(
        None,
        description="Percentage of portfolio flagged as high-risk",
    )
    high_risk_loans: List[RiskLoan] = Field(..., description="List of high-risk loans")


class FullAnalysisResponse(BaseModel):
    analysis_id: str
    summary: str
    recommendations: List[str]
    risk_assessment: RiskAlertsResponse


class DataQualityResponse(BaseModel):
    duplicate_ratio: Optional[float] = None
    average_null_ratio: Optional[float] = None
    invalid_numeric_ratio: Optional[float] = None
    data_quality_score: Optional[float] = Field(None, ge=0, le=100)


class ValidationErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: List[ValidationErrorDetail]


class ValidationResponse(BaseModel):
    valid: bool
    message: Optional[str] = None
    columns_present: Optional[List[str]] = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class DefaultPredictionRequest(BaseModel):
    """Request body for the /predict/default endpoint."""

    loan_amount: float = Field(..., description="Loan principal amount")
    interest_rate: float = Field(..., description="Annual interest rate (percentage)")
    term_months: int = Field(..., description="Loan term in months")
    ltv_ratio: float = Field(0.0, description="Loan-to-Value ratio")
    dti_ratio: float = Field(0.0, description="Debt-to-Income ratio")
    credit_score: float = Field(0.0, description="Borrower credit score")
    days_past_due: int = Field(0, description="Current days past due")
    monthly_income: float = Field(0.0, description="Borrower monthly income")
    employment_length_years: float = Field(0.0, description="Years of employment")
    num_open_accounts: int = Field(0, description="Number of open credit accounts")


class DefaultPredictionResponse(BaseModel):
    """Response body for the /predict/default endpoint."""

    probability: float = Field(..., description="Default probability (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high, critical")
    model_version: str = Field(..., description="Model version identifier")
