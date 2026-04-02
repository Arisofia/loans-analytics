"""Report generation routes — executive brief, investor summary, etc."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision/reports", tags=["reports"])


class ReportRequest(BaseModel):
    metrics: Dict[str, Any] = Field(..., description="KPI/metric bundle.")
    scenarios: List[Dict[str, Any]] = Field(
        default_factory=list, description="Scenario results."
    )
    alerts: List[str] = Field(default_factory=list)
    actions: List[Dict[str, Any]] = Field(default_factory=list)


class ReportSection(BaseModel):
    title: str
    body: str


class ReportResponse(BaseModel):
    report_type: str
    sections: List[ReportSection] = Field(default_factory=list)


def _build_sections(
    req: ReportRequest,
    report_type: str,
) -> List[ReportSection]:
    """Build generic report sections from the request payload."""
    sections: List[ReportSection] = []

    # KPI summary
    if req.metrics:
        lines = [f"- **{k}**: {v}" for k, v in req.metrics.items()]
        sections.append(
            ReportSection(title="Key Metrics", body="\n".join(lines))
        )

    # Alerts
    if req.alerts:
        sections.append(
            ReportSection(
                title="Alerts",
                body="\n".join(f"- {a}" for a in req.alerts),
            )
        )

    # Actions
    if req.actions:
        action_lines = [
            f"- [{a.get('priority', '-')}] {a.get('action', 'N/A')} "
            f"(agent: {a.get('agent', '?')})"
            for a in req.actions
        ]
        sections.append(
            ReportSection(title="Action Items", body="\n".join(action_lines))
        )

    # Scenarios
    if req.scenarios:
        for sc in req.scenarios:
            sections.append(
                ReportSection(
                    title=f"Scenario: {sc.get('scenario', 'unknown')}",
                    body=sc.get("narrative", "No narrative."),
                )
            )

    return sections


@router.post("/executive-brief", response_model=ReportResponse)
async def executive_brief(req: ReportRequest):
    """Generate an executive brief report."""
    try:
        return ReportResponse(
            report_type="executive_brief",
            sections=_build_sections(req, "executive_brief"),
        )
    except Exception as exc:
        logger.error("Executive brief error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/investor-summary", response_model=ReportResponse)
async def investor_summary(req: ReportRequest):
    """Generate an investor summary report."""
    try:
        return ReportResponse(
            report_type="investor_summary",
            sections=_build_sections(req, "investor_summary"),
        )
    except Exception as exc:
        logger.error("Investor summary error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/lender-pack", response_model=ReportResponse)
async def lender_pack(req: ReportRequest):
    """Generate a lender pack report."""
    try:
        return ReportResponse(
            report_type="lender_pack",
            sections=_build_sections(req, "lender_pack"),
        )
    except Exception as exc:
        logger.error("Lender pack error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/weekly-memo", response_model=ReportResponse)
async def weekly_memo(req: ReportRequest):
    """Generate a weekly operating memo."""
    try:
        return ReportResponse(
            report_type="weekly_memo",
            sections=_build_sections(req, "weekly_memo"),
        )
    except Exception as exc:
        logger.error("Weekly memo error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
