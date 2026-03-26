from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.base_agent import BaseAgent
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput, AgentRecommendation


class PricingAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "pricing"

    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        alerts: list[AgentAlert] = []
        recs: list[AgentRecommendation] = []

        spread = metrics.get("spread", 0)
        if isinstance(spread, (int, float)) and spread < 0.05:
            alerts.append(AgentAlert(
                severity="warning",
                title=f"Spread {spread:.2%} below 5%",
                description="Pricing does not cover risk.",
                metric_id="spread",
            ))
            recs.append(AgentRecommendation(
                title="Raise rates",
                rationale="Spread below minimum target.",
                expected_impact="Restore positive margin",
            ))

        return AgentOutput(
            agent_id=self.agent_id,
            status="ok",
            summary=f"Spread={spread}",
            alerts=alerts,
            recommendations=recs,
            confidence=0.90,
        )
