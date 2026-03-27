from __future__ import annotations

from typing import Any

from backend.src.contracts.agent_schema import AgentOutput


class DecisionOrchestrator:
    def __init__(
        self,
        agent_outputs: list[AgentOutput],
        metrics: dict[str, Any],
    ) -> None:
        self.agent_outputs = agent_outputs
        self.metrics = metrics

    def run(self) -> dict[str, Any]:
        all_alerts = []
        all_actions = []
        all_opportunities = []

        for out in self.agent_outputs:
            all_alerts.extend(out.alerts)
            all_actions.extend(out.actions)
            all_opportunities.extend(out.recommendations)

        ranked_actions = sorted(
            [a.model_dump() for a in all_actions],
            key=lambda x: x.get("confidence", 0),
            reverse=True,
        )
        ranked_alerts = sorted(
            [a.model_dump() for a in all_alerts],
            key=lambda x: {"critical": 0, "warning": 1, "info": 2}.get(
                x.get("severity", "info"), 9
            ),
        )

        return {
            "ranked_alerts": ranked_alerts,
            "ranked_actions": ranked_actions,
            "opportunities": [r.model_dump() for r in all_opportunities],
            "agent_statuses": {
                out.agent_id: out.status for out in self.agent_outputs
            },
        }
