from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.base_agent import BaseAgent
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput
from backend.src.data_quality.engine import run_data_quality


class DataQualityAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "data_quality"

    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        loans = marts.get("portfolio_mart", pd.DataFrame())
        dq = run_data_quality(loans)

        alerts: list[AgentAlert] = []
        blocked_by: list[str] = []

        if dq["blocking_issues"]:
            alerts.append(AgentAlert(
                severity="critical",
                title="Data quality gate BLOCKED",
                description=str(dq["blocking_issues"]),
            ))
            blocked_by.append("data_quality")

        for w in dq["warnings"]:
            alerts.append(AgentAlert(severity="warning", title=w, description=w))

        return AgentOutput(
            agent_id=self.agent_id,
            status="blocked" if blocked_by else "ok",
            summary=f"Quality score {dq['quality_score']}",
            alerts=alerts,
            confidence=dq["quality_score"],
            blocked_by=blocked_by,
        )
