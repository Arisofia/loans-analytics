from __future__ import annotations

from typing import Any

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class SalesAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "sales"

    def run(self, ctx: AgentContext) -> AgentOutput:
        sales = ctx.marts.get("sales_mart", pd.DataFrame())
        alerts = []

        win_rate = ctx.metrics.get("win_rate", 0)
        if isinstance(win_rate, (int, float)) and win_rate < 0.20:
            alerts.append(self._alert(
                "low_win_rate", "warning",
                f"Win rate {win_rate:.0%} below 20%",
                "Pipeline conversion is low.",
                metric_id="win_rate",
                current_value=float(win_rate),
                threshold=0.20,
            ))

        return self._build_output(
            summary=f"Win rate={win_rate}, {len(sales)} leads",
            alerts=alerts,
            confidence=0.85,
        )
