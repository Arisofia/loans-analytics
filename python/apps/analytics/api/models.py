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
    borrower_id: Optional[str] = Field(None, description="Borrower identifier")
    days_past_due: Optional[float] = Field(None, description="Current days past due")
    payment_frequency: Optional[str] = Field(None, description="Payment frequency descriptor")
    term_months: Optional[float] = Field(None, description="Loan term in months")
    origination_date: Optional[datetime] = Field(None, description="Loan origination timestamp")
    origination_fee: Optional[float] = Field(None, description="Origination fee amount")
    origination_fee_taxes: Optional[float] = Field(None, description="Taxes charged over fees")
    total_scheduled: Optional[float] = Field(None, description="Total scheduled collections amount")
    last_payment_amount: Optional[float] = Field(None, description="Last collected payment amount")
    recovery_value: Optional[float] = Field(
        None, description="Recovered amount from defaulted loans"
    )
    credit_score: Optional[float] = Field(None, description="Primary credit bureau score")
    equifax_score: Optional[float] = Field(None, description="Equifax score when available")
    current_balance: Optional[float] = Field(
        None, description="Current balance proxy for cash position"
    )


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
    formula: Optional[str] = Field(None, description="Human-readable calculation formula")
    definition: Optional[str] = Field(None, description="Business definition of the KPI")
    implications: Optional[str] = Field(None, description="Business implications of KPI movement")
    context: KpiContext


class DPDBucketBreakdown(BaseModel):
    bucket: str = Field(..., description="DPD bucket identifier")
    loan_count: int = Field(..., description="Number of loans in the bucket")
    balance: float = Field(..., description="Outstanding balance in the bucket")
    balance_share_pct: float = Field(
        ...,
        description="Bucket outstanding balance as percentage of total outstanding",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "bucket": "90_plus",
                "loan_count": 14,
                "balance": 128450.25,
                "balance_share_pct": 11.82,
            }
        }
    }


class AdvancedRiskResponse(BaseModel):
    par30: float = Field(..., description="Portfolio at Risk over 30 days (%)")
    par60: float = Field(..., description="Portfolio at Risk over 60 days (%)")
    par90: float = Field(..., description="Portfolio at Risk over 90 days (%)")
    default_rate: float = Field(..., description="Defaulted loan count over total loans (%)")
    collections_coverage: float = Field(
        ...,
        description="Observed collections over scheduled collections (%)",
    )
    fee_yield: float = Field(..., description="Fee and fee-tax yield over principal (%)")
    total_yield: float = Field(..., description="Combined interest and fee yield (%)")
    recovery_rate: float = Field(..., description="Recoveries over defaulted balance (%)")
    concentration_hhi: float = Field(..., description="Borrower exposure concentration (HHI)")
    repeat_borrower_rate: float = Field(
        ...,
        description="Borrowers with multiple loans over unique borrowers (%)",
    )
    credit_quality_index: float = Field(
        ...,
        description="Normalized credit quality index from bureau scores (0-100)",
    )
    total_loans: int = Field(..., description="Total loans analyzed")
    dpd_buckets: List[DPDBucketBreakdown] = Field(default_factory=list)

    model_config = {
        "json_schema_extra": {
            "example": {
                "par30": 18.42,
                "par60": 11.77,
                "par90": 6.31,
                "default_rate": 4.82,
                "collections_coverage": 93.44,
                "fee_yield": 1.25,
                "total_yield": 29.81,
                "recovery_rate": 22.17,
                "concentration_hhi": 846.32,
                "repeat_borrower_rate": 27.9,
                "credit_quality_index": 64.55,
                "total_loans": 1247,
                "dpd_buckets": [
                    {
                        "bucket": "current",
                        "loan_count": 1066,
                        "balance": 7421000.54,
                        "balance_share_pct": 83.11,
                    },
                    {
                        "bucket": "90_plus",
                        "loan_count": 31,
                        "balance": 563122.11,
                        "balance_share_pct": 6.31,
                    },
                ],
            }
        }
    }


class KpiResponse(BaseModel):
    PAR30: Optional[KpiSingleResponse] = None
    PAR90: Optional[KpiSingleResponse] = None
    CollectionRate: Optional[KpiSingleResponse] = None
    LossRate: Optional[KpiSingleResponse] = None
    RecoveryRate: Optional[KpiSingleResponse] = None
    CashOnHand: Optional[KpiSingleResponse] = None
    PortfolioHealth: Optional[KpiSingleResponse] = None
    ActiveBorrowers: Optional[KpiSingleResponse] = None
    RepeatBorrowerRate: Optional[KpiSingleResponse] = None
    AutomationRate: Optional[KpiSingleResponse] = None
    AverageLoanSize: Optional[KpiSingleResponse] = None
    ProcessingTimeAvg: Optional[KpiSingleResponse] = None
    DisbursementVolumeMTD: Optional[KpiSingleResponse] = None
    NewLoansCountMTD: Optional[KpiSingleResponse] = None
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
