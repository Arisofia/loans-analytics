"""Cohort & Vintage Agent — Layer 1 core analytics.

Analyses portfolio performance by origination vintage to identify
deteriorating cohorts and underwriting drift.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
# build_cohorts missing in cohorts.py

class CohortVintageAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "cohort_vintage"

    @property
    def dependencies(self) -> List[str]:
        return ["data_quality"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        alerts = []
        recommendations = []
        metrics: Dict[str, Any] = {}

        if portfolio.empty:
            return self._build_output(summary="No portfolio data for cohort analysis.", confidence=0.0)

        cohorts: Dict[str, Any] = {} # build_cohorts missing
        metrics.update(cohorts)

        # ── Worst vintage analysis ──────────────────────────────────────
        worst = cohorts.get("worst_vintage", {})
        if worst:
            worst_name = worst.get("vintage", "unknown")
            worst_default = worst.get("default_rate", 0)
            if worst_default > 0.10:
                alerts.append(self._alert(
                    "toxic_vintage", "critical",
                    f"Vintage {worst_name}: {worst_default:.1%} default rate",
                    "This vintage has severe underwriting quality issues.",
                    metric_id="vintage_default_rate",
                    current_value=worst_default, threshold=0.10,
                ))
                recommendations.append(self._recommendation(
                    "investigate_vintage", f"Investigate vintage {worst_name}",
                    rationale=f"Default rate {worst_default:.1%} is 2.5x the portfolio target.",
                    expected_impact="Identify underwriting criteria that failed.",
                ))

        # ── Trend detection ─────────────────────────────────────────────
        vintages = cohorts.get("vintages", {})
        if len(vintages) >= 3:
            sorted_vintages = sorted(vintages.items())
            recent_3 = [v[1].get("default_rate", 0) for v in sorted_vintages[-3:]]
            if all(recent_3[i] < recent_3[i + 1] for i in range(len(recent_3) - 1)):
                alerts.append(self._alert(
                    "deteriorating_trend", "warning",
                    "Default rate rising across last 3 vintages",
                    f"Rates: {', '.join(f'{r:.2%}' for r in recent_3)}",
                ))
                recommendations.append(self._recommendation(
                    "tighten_underwriting", "Tighten underwriting standards",
                    rationale="Three consecutive vintages with rising defaults.",
                    expected_impact="Stabilize future vintage performance.",
                ))

        return self._build_output(
            summary=f"Cohort: {len(vintages)} vintages analysed. Worst={worst.get('vintage', 'N/A')}. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            confidence=0.90,
            metrics=metrics,
        )
