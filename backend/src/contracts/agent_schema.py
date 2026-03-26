"""Agent output schema — standardised envelope returned by every decision agent.

Every agent MUST return an AgentOutput so the Decision Orchestrator can
rank, block, and surface actions consistently.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    """One actionable recommendation from an agent."""

    action_id: str
    title: str
    owner: str = Field(..., description="Team responsible: risk | sales | marketing | treasury | cfo")
    urgency: str = Field("medium", description="critical | high | medium | low")
    impact: str = Field("medium", description="high | medium | low")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    blocked_by: List[str] = Field(default_factory=list)
    details: Optional[str] = None


class AgentAlert(BaseModel):
    """A risk or operational alert surfaced by an agent."""

    alert_id: str
    severity: str = Field("warning", description="critical | warning | info")
    title: str
    description: str = ""
    metric_id: Optional[str] = None
    current_value: Optional[float] = None
    threshold: Optional[float] = None


class AgentRecommendation(BaseModel):
    """A strategic recommendation (longer-term than an action)."""

    rec_id: str
    title: str
    rationale: str = ""
    expected_impact: Optional[str] = None
    confidence: float = 0.5


class AgentOutput(BaseModel):
    """Standard envelope returned by every agent.  Used by the Decision Orchestrator."""

    agent_id: str
    status: str = Field("ok", description="ok | degraded | error | blocked")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    summary: str = ""
    alerts: List[AgentAlert] = Field(default_factory=list)
    recommendations: List[AgentRecommendation] = Field(default_factory=list)
    actions: List[AgentAction] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    blocked_by: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class DecisionCenterState(BaseModel):
    """Aggregated state consumed by the AI Decision Center frontend."""

    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    business_state: Dict[str, Any] = Field(default_factory=dict)
    critical_alerts: List[AgentAlert] = Field(default_factory=list)
    ranked_actions: List[AgentAction] = Field(default_factory=list)
    blocked_actions: List[AgentAction] = Field(default_factory=list)
    opportunities: List[AgentRecommendation] = Field(default_factory=list)
    scenario_summary: Dict[str, Any] = Field(default_factory=dict)
    agent_statuses: Dict[str, str] = Field(default_factory=dict)
