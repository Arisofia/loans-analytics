"""Tests for DecisionOrchestrator — first live slice."""

from __future__ import annotations

from backend.python.multi_agent.orchestrator.decision_orchestrator import (
    DecisionOrchestrator,
)
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput
from backend.src.contracts.metric_schema import MetricResult


def _make_output(agent_id: str, *, blocked: bool = False) -> AgentOutput:
    alerts = []
    if blocked:
        alerts.append(
            AgentAlert(
                severity="critical",
                title=f"{agent_id} alert",
                description="test",
                metric_id="par30",
            )
        )
    return AgentOutput(
        agent_id=agent_id,
        status="blocked" if blocked else "ok",
        summary="test",
        alerts=alerts,
        blocked_by=["data_quality"] if blocked else [],
    )


def _make_metric(name: str, value: float) -> MetricResult:
    return MetricResult(
        metric_id=name,
        metric_name=name,
        value=value,
        unit="ratio",
        source_mart="portfolio",
        owner="risk",
        as_of_date="2024-01-01",
    )


def test_orchestrator_collects_alerts() -> None:
    outputs = [
        _make_output("risk", blocked=True),
        _make_output("pricing"),
    ]
    metrics = [_make_metric("par30", 0.15)]
    orch = DecisionOrchestrator(outputs, metrics)
    result = orch.run()

    assert "ranked_alerts" in result
    assert len(result["ranked_alerts"]) == 1
    assert result["agent_statuses"]["risk"] == "blocked"
    assert result["agent_statuses"]["pricing"] == "ok"


def test_orchestrator_empty() -> None:
    orch = DecisionOrchestrator([], [])
    result = orch.run()
    assert result["ranked_alerts"] == []
    assert result["ranked_actions"] == []
