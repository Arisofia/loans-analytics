from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# --- Schemas from openapi.yaml ---


class LoanRecord(BaseModel):
    """Loan record compatible with both real Abaco data and generic portfolio analysis.

    Required fields: loan_amount, loan_status, interest_rate, principal_balance
    Optional fields: appraised_value, borrower_income, monthly_debt (not present in
    invoice factoring datasets — defaults provided for LTV/DTI calculations).
    """

    id: Optional[str] = Field(None, description="Loan identifier")
    loan_amount: float = Field(..., description="Original loan amount")
    appraised_value: Optional[float] = Field(
        None,
        description=(
            "Appraised value of the collateral. "
            "Optional for invoice factoring; defaults to collateral_value if available."
        ),
    )
    borrower_income: Optional[float] = Field(
        None,
        description=(
            "Annual borrower income. Optional for invoice factoring (not typically available)."
        ),
    )
    monthly_debt: Optional[float] = Field(
        None,
        description=(
            "Monthly debt obligations. Optional for invoice factoring (not typically available)."
        ),
    )
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
        min_length=0,
        max_length=10000,
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
    formula: Optional[str] = Field("", description="Formula used for calculation")
    sample_size: Optional[int] = Field(0, description="Number of records used in calculation")
    period: str = Field(..., description="Reporting period (e.g. 'daily', 'on-demand')")
    calculation_date: datetime = Field(..., description="Date/time of calculation")
    filters: Optional[Dict[str, Any]] = None


class KpiSingleResponse(BaseModel):
    id: Optional[str] = Field(None, description="KPI identifier")
    name: Optional[str] = Field(None, description="KPI display name")
    value: float = Field(..., description="Calculated KPI value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    definition: Optional[str] = Field(None, description="Business definition of the KPI")
    implications: Optional[str] = Field(None, description="Business implications of KPI movement")
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
    kpis: List[KpiSingleResponse] = Field(
        default_factory=list,
        description="KPI snapshot used by the analysis, including formulas and implications",
    )


class KpiCoverageResponse(BaseModel):
    """Coverage report between configured KPI catalog and API-supported KPIs."""

    catalog_total: int
    implemented_total: int
    catalog_kpis: List[str] = Field(default_factory=list)
    implemented_catalog_kpis: List[str] = Field(default_factory=list)
    missing_catalog_kpis: List[str] = Field(default_factory=list)
    exposed_aliases: Dict[str, List[str]] = Field(default_factory=dict)


class DataQualityResponse(BaseModel):
    duplicate_ratio: Optional[float] = None
    average_null_ratio: Optional[float] = None
    invalid_numeric_ratio: Optional[float] = None
    data_quality_score: Optional[float] = Field(None, ge=0, le=100)
    issues: List[str] = Field(default_factory=list)


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
    errors: List[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class ExecutiveAnalyticsRequest(BaseModel):
    """Request body for strategic executive analytics."""

    loans: List[LoanRecord] = Field(
        ...,
        min_length=1,
        description="Loan-level portfolio records",
    )
    payments: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional payment events for realized revenue and churn",
    )
    customers: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional customer master records for CAC and governance",
    )
    schedule: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional payment schedule rows",
    )


class ExecutiveAnalyticsResponse(BaseModel):
    """Executive analytics response with confirmations and strategic tables."""

    strategic_confirmations: Dict[str, Any] = Field(default_factory=dict)
    executive_strip: Dict[str, Any] = Field(default_factory=dict)
    churn_90d_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    unit_economics: List[Dict[str, Any]] = Field(default_factory=list)
    pricing_analytics: Dict[str, Any] = Field(default_factory=dict)
    revenue_forecast_6m: List[Dict[str, Any]] = Field(default_factory=list)
    opportunity_prioritization: List[Dict[str, Any]] = Field(default_factory=list)
    data_governance: Dict[str, Any] = Field(default_factory=dict)


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
