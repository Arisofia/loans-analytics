from __future__ import annotations

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.risk import compute_expected_loss, compute_par30


class RiskAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "risk"

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        alerts = []
        recs = []

        par30 = compute_par30(portfolio)
        el = compute_expected_loss(portfolio)

        if par30 > 0.05:
            alerts.append(self._alert(
                "par30_high", "critical",
                f"PAR30 {par30:.2%} exceeds 5%",
                "Portfolio at risk above covenant tolerance.",
                metric_id="par30",
                current_value=par30,
                threshold=0.05,
            ))
            recs.append(self._recommendation(
                "tighten_origination",
                "Tighten origination",
                rationale="PAR30 above threshold — reduce approval rates.",
                expected_impact="Reduce PAR30 2-5pp",
            ))

        return self._build_output(
            summary=f"PAR30={par30:.2%}, EL={el:,.0f}",
            alerts=alerts,
            recommendations=recs,
            confidence=0.95,
        )
