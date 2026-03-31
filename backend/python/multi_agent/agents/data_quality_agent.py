from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.data_quality.engine import run_data_quality


class DataQualityAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "data_quality"

    def run(self, *, marts=None, metrics=None, features=None, quality=None, ctx: AgentContext = None, **kwargs) -> AgentOutput:
        # Support both context object and direct kwargs for compatibility
        if ctx is not None:
            loans = ctx.marts.get("portfolio_mart", pd.DataFrame())
        elif marts is not None:
            loans = marts.get("portfolio_mart", pd.DataFrame())
        else:
            loans = pd.DataFrame()
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
