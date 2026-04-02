from __future__ import annotations

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.data_quality.engine import run_data_quality


class DataQualityAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "data_quality"

    def run(self, ctx: AgentContext) -> AgentOutput:
        loans = ctx.marts.get("portfolio_mart", pd.DataFrame())
        dq = run_data_quality(loans)

        alerts = []
        blocked_by = []

        if dq["blocking_issues"]:
            alerts.append(self._alert(
                "dq_blocked", "critical",
                "Data quality gate BLOCKED",
                str(dq["blocking_issues"]),
            ))
            blocked_by.append("data_quality")

        for w in dq["warnings"]:
            alerts.append(self._alert("dq_warning", "warning", w, w))

        output = self._build_output(
            summary=f"Quality score {dq['quality_score']}",
            alerts=alerts,
            confidence=dq["quality_score"],
            blocked_by=blocked_by,
        )
        return output
