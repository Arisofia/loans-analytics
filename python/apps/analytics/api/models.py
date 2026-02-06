from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# --- Schemas from openapi.yaml ---

class LoanRecord(BaseModel):
    loan_amount: float = Field(..., description="Original loan amount")
    appraised_value: float = Field(..., description="Appraised value of the collateral property")
    borrower_income: float = Field(..., description="Annual borrower income")
    monthly_debt: float = Field(..., description="Monthly debt obligations")
    loan_status: str = Field(..., description="Current loan status",
                              examples=["current", "30-59 days past due", "90+ days past due"])
    interest_rate: float = Field(..., description="Annual interest rate as decimal (e.g., 0.035 for 3.5%)",
                                 ge=0, le=1)
    principal_balance: float = Field(..., description="Current outstanding principal balance")


class LoanPortfolioRequest(BaseModel):
    loans: List[LoanRecord] = Field(..., min_items=1, max_items=10000,
                                     description="Array of loan records for analysis")
    # Adding loan_ids here for backwards compatibility if needed, but primary input is 'loans'
    # loan_ids: Optional[List[str]] = Field(None, description="Optional list of loan IDs for filtering/context")


class KpiContext(BaseModel):
    metric: Optional[str] = Field(None, description="Name of the KPI metric")
    timestamp: Optional[datetime] = Field(None, description="Calculation timestamp")
    formula: Optional[str] = Field(None, description="Formula used for calculation")
    sample_size: Optional[int] = Field(None, description="Number of records used in calculation")
    period: str
    calculation_date: datetime
    filters: Optional[Dict[str, Any]] = None


class KpiSingleResponse(BaseModel):
    value: float = Field(..., description="Calculated KPI value")
    context: KpiContext


class KpiResponse(BaseModel):
    PAR30: Optional[KpiSingleResponse] = None
    PAR90: Optional[KpiSingleResponse] = None
    CollectionRate: Optional[KpiSingleResponse] = None
    PortfolioHealth: Optional[KpiSingleResponse] = None
    LTV: Optional[KpiSingleResponse] = None
    DTI: Optional[KpiSingleResponse] = None
    PortfolioYield: Optional[KpiSingleResponse] = None
    audit_trail: Optional[List[Dict[str, Any]]] = None # Changed from AuditEntry as it's not defined in this file.


class RiskLoan(BaseModel):
    loan_id: str
    risk_score: float
    alerts: List[str]


class RiskAlertsResponse(BaseModel):
    high_risk_count: Optional[int] = Field(None, description="Number of high-risk loans identified")
    total_loans: Optional[int] = Field(None, description="Total loans analyzed")
    risk_ratio: Optional[float] = Field(None, description="Percentage of portfolio flagged as high-risk")
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

# --- End Schemas from openapi.yaml ---