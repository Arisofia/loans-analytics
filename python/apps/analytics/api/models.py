from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DrilldownStatusResponse(BaseModel):
    id: str
    status: str
    created_at: datetime


class LoanRecord(BaseModel):
    id: str
    amount: Decimal
    status: str
    disbursed_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class LoanPortfolioRequest(BaseModel):
    loan_ids: List[str]
    context: Optional[Dict[str, Any]] = None


class KpiContext(BaseModel):
    period: str
    calculation_date: datetime
    filters: Optional[Dict[str, Any]] = None


class KpiSingleResponse(BaseModel):
    id: str
    name: str
    value: float
    unit: str
    context: KpiContext


class KpiResponse(BaseModel):
    kpis: List[KpiSingleResponse]


class AuditEntry(BaseModel):
    timestamp: datetime
    user_id: str
    action: str
    details: Dict[str, Any]


class RiskLoan(BaseModel):
    loan_id: str
    risk_score: float
    alerts: List[str]


class RiskAlertsResponse(BaseModel):
    risk_level: str
    high_risk_loans: List[RiskLoan]


class FullAnalysisResponse(BaseModel):
    analysis_id: str
    summary: str
    recommendations: List[str]
    risk_assessment: RiskAlertsResponse


class DataQualityResponse(BaseModel):
    score: float
    issues: List[str]


class ValidationResponse(BaseModel):
    valid: bool
    errors: Optional[List[str]] = None


class ValidationErrorDetail(BaseModel):
    loc: List[str]
    msg: str
    type: str


class ValidationErrorResponse(BaseModel):
    detail: List[ValidationErrorDetail]


class ErrorResponse(BaseModel):
    code: str
    message: str
