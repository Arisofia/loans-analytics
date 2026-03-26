from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.base_agent import BaseAgent
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput


class SalesAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "sales"

    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        sales = marts.get("sales_mart", pd.DataFrame())
        alerts: list[AgentAlert] = []

        win_rate = metrics.get("win_rate", 0)
        if isinstance(win_rate, (int, float)) and win_rate < 0.20:
            alerts.append(AgentAlert(
                severity="warning",
                title=f"Win rate {win_rate:.0%} below 20%",
                description="Pipeline conversion is low.",
                metric_id="win_rate",
            ))

        return AgentOutput(
            agent_id=self.agent_id,
            status="ok",
            summary=f"Win rate={win_rate}, {len(sales)} leads",
            alerts=alerts,
            confidence=0.85,
        )
