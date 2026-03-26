"""Base class for decision-grade agents.

Every decision agent receives a standard ``AgentContext`` (marts, metrics,
features, scenarios) and must return an ``AgentOutput`` envelope.  No LLM
dependency — pure analytical logic grounded on real portfolio data.
"""

from __future__ import annotations

import abc
import datetime as dt
import logging
from typing import Any, Dict, List, Optional

from backend.src.contracts.agent_schema import AgentAction, AgentAlert, AgentOutput, AgentRecommendation

logger = logging.getLogger(__name__)


class AgentContext:
    """Read-only bag of data available to every decision agent."""

    __slots__ = (
        "marts", "metrics", "features", "scenarios",
        "business_params", "as_of_date",
    )

    def __init__(
        self,
        marts: Dict[str, Any],
        metrics: Dict[str, Any],
        features: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        business_params: Dict[str, Any],
        as_of_date: Optional[str] = None,
    ):
        self.marts = marts
        self.metrics = metrics
        self.features = features
        self.scenarios = scenarios
        self.business_params = business_params
        self.as_of_date = as_of_date or dt.date.today().isoformat()


class DecisionAgent(abc.ABC):
    """Abstract base for all decision agents.

    Sub-classes must implement ``agent_id``, ``run(ctx)`` and optionally
    ``dependencies``.
    """

    @property
    @abc.abstractmethod
    def agent_id(self) -> str:
        """Unique identifier matching the registry."""

    @property
    def dependencies(self) -> List[str]:
        """Agent IDs that must run before this one."""
        return []

    @abc.abstractmethod
    def run(self, ctx: AgentContext) -> AgentOutput:
        """Execute analysis and return structured output."""

    # ── helpers for sub-classes ──────────────────────────────────────────
    def _build_output(
        self,
        *,
        summary: str,
        alerts: Optional[List[AgentAlert]] = None,
        recommendations: Optional[List[AgentRecommendation]] = None,
        actions: Optional[List[AgentAction]] = None,
        confidence: float = 1.0,
        evidence: Optional[Dict[str, Any]] = None,
        blocked_by: Optional[List[str]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> AgentOutput:
        return AgentOutput(
            agent_id=self.agent_id,
            status="ok",
            timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
            summary=summary,
            alerts=alerts or [],
            recommendations=recommendations or [],
            actions=actions or [],
            confidence=confidence,
            evidence=evidence or {},
            blocked_by=blocked_by or [],
            metrics=metrics or {},
        )

    def _alert(
        self,
        alert_id: str,
        severity: str,
        title: str,
        description: str,
        metric_id: str = "",
        current_value: float = 0.0,
        threshold: float = 0.0,
    ) -> AgentAlert:
        return AgentAlert(
            alert_id=f"{self.agent_id}.{alert_id}",
            severity=severity,
            title=title,
            description=description,
            metric_id=metric_id,
            current_value=current_value,
            threshold=threshold,
        )

    def _recommendation(
        self, rec_id: str, title: str, rationale: str,
        expected_impact: str = "", confidence: float = 0.8,
    ) -> AgentRecommendation:
        return AgentRecommendation(
            rec_id=f"{self.agent_id}.{rec_id}",
            title=title,
            rationale=rationale,
            expected_impact=expected_impact,
            confidence=confidence,
        )

    def _action(
        self, action_id: str, title: str, owner: str,
        urgency: str = "medium", impact: str = "medium",
        confidence: float = 0.8, details: str = "",
    ) -> AgentAction:
        return AgentAction(
            action_id=f"{self.agent_id}.{action_id}",
            title=title,
            owner=owner,
            urgency=urgency,
            impact=impact,
            confidence=confidence,
            details=details,
        )
