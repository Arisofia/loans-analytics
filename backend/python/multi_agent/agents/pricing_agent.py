from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class PricingAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "pricing"

    def run(self, ctx: AgentContext) -> AgentOutput:
        alerts = []
        recs = []

        spread = ctx.metrics.get("spread", 0)
        if isinstance(spread, (int, float)) and spread < 0.05:
            alerts.append(self._alert(
                "spread_low", "warning",
                f"Spread {spread:.2%} below 5%",
                "Pricing does not cover risk.",
                metric_id="spread",
                current_value=float(spread),
                threshold=0.05,
            ))
            recs.append(self._recommendation(
                "raise_rates",
                "Raise rates",
                rationale="Spread below minimum target.",
                expected_impact="Restore positive margin",
            ))

        return self._build_output(
            summary=f"Spread={spread}",
            alerts=alerts,
            recommendations=recs,
            confidence=0.90,
        )
