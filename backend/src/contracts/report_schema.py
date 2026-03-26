"""Report payload schemas.

Defines Pydantic models for structured report outputs consumed
by the narrative agent, API endpoints, and investor-facing surfaces.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """One logical section inside a report."""

    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None  # critical | warning | info


class ExecutiveBrief(BaseModel):
    """Board-grade executive summary produced after each pipeline run."""

    report_type: str = "executive_brief"
    generated_at: datetime
    as_of_date: date
    business_state: str  # healthy | attention | critical | data_blocked
    sections: List[ReportSection] = Field(default_factory=list)
    critical_alerts: List[str] = Field(default_factory=list)
    ranked_actions: List[str] = Field(default_factory=list)
    kpi_snapshot: Dict[str, Any] = Field(default_factory=dict)


class InvestorSummary(BaseModel):
    """Investor-facing portfolio summary."""

    report_type: str = "investor_summary"
    generated_at: datetime
    as_of_date: date
    portfolio_size: float = 0.0
    par30: Optional[float] = None
    par60: Optional[float] = None
    par90: Optional[float] = None
    expected_loss_rate: Optional[float] = None
    net_yield: Optional[float] = None
    concentration_hhi: Optional[float] = None
    covenant_status: Dict[str, Any] = Field(default_factory=dict)
    sections: List[ReportSection] = Field(default_factory=list)


class LenderPack(BaseModel):
    """Compliance-oriented pack sent to lenders / credit facilities."""

    report_type: str = "lender_pack"
    generated_at: datetime
    as_of_date: date
    eligible_portfolio: float = 0.0
    aging_distribution: Dict[str, float] = Field(default_factory=dict)
    covenant_metrics: Dict[str, Any] = Field(default_factory=dict)
    concentration_summary: Dict[str, Any] = Field(default_factory=dict)
    sections: List[ReportSection] = Field(default_factory=list)


class WeeklyOperatingMemo(BaseModel):
    """Internal weekly operating memo highlighting key changes."""

    report_type: str = "weekly_operating_memo"
    generated_at: datetime
    week_ending: date
    highlights: List[str] = Field(default_factory=list)
    risk_changes: List[str] = Field(default_factory=list)
    sales_pipeline_summary: Dict[str, Any] = Field(default_factory=dict)
    collection_summary: Dict[str, Any] = Field(default_factory=dict)
    action_items: List[str] = Field(default_factory=list)
    sections: List[ReportSection] = Field(default_factory=list)
