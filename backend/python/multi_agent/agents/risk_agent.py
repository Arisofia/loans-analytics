from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.base_agent import BaseAgent
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput, AgentRecommendation
from backend.src.kpi_engine.risk import compute_expected_loss, compute_par30


class RiskAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "risk"

    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        portfolio = marts.get("portfolio_mart", pd.DataFrame())
        alerts: list[AgentAlert] = []
        recs: list[AgentRecommendation] = []

        par30 = compute_par30(portfolio)
        el = compute_expected_loss(portfolio)

        if par30 > 0.10:
            alerts.append(AgentAlert(
                severity="critical",
                title=f"PAR30 {par30:.2%} exceeds 10%",
                description="Portfolio at risk above tolerance.",
                metric_id="par30",
            ))
            recs.append(AgentRecommendation(
                title="Tighten origination",
                rationale="PAR30 above threshold — reduce approval rates.",
                expected_impact="Reduce PAR30 2-5pp",
            ))

        return AgentOutput(
            agent_id=self.agent_id,
            status="ok",
            summary=f"PAR30={par30:.2%}, EL={el:,.0f}",
            alerts=alerts,
            recommendations=recs,
            confidence=0.95,
        )
