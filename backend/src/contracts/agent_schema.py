from datetime import datetime, timezone
from typing import Any, Dict, List

from pydantic import BaseModel, Field


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentEvidence(BaseModel):
    label: str
    value: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentAlert(BaseModel):
    severity: str
    title: str
    description: str
    metric_id: str | None = None


class AgentRecommendation(BaseModel):
    title: str
    rationale: str
    expected_impact: str
    confidence: float


class AgentAction(BaseModel):
    action_id: str
    title: str
    owner: str
    urgency: str
    impact: str
    confidence: float
    blocked_by: List[str] = Field(default_factory=list)


class AgentOutput(BaseModel):
    agent_id: str
    status: str
    timestamp: str = Field(default_factory=_utc_now_iso)
    summary: str
    alerts: List[AgentAlert] = Field(default_factory=list)
    recommendations: List[AgentRecommendation] = Field(default_factory=list)
    actions: List[AgentAction] = Field(default_factory=list)
    confidence: float = 0.0
    evidence: List[AgentEvidence] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)
