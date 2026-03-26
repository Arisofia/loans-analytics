"""Pricing Agent — Layer 2 strategy.

Evaluates yield, NIM, and cost of risk to determine if pricing is
adequate for the portfolio's risk profile.  Recommends rate adjustments
when margin compression is detected.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.revenue import compute_nim, compute_yield


class PricingAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "pricing"

    @property
    def dependencies(self) -> List[str]:
        return ["risk"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        finance = ctx.marts.get("finance_mart", pd.DataFrame())
        guardrails = ctx.business_params.get("financial_guardrails", {})
        alerts = []
        recommendations = []
        actions = []

        if finance.empty:
            return self._build_output(summary="No finance mart data for pricing.", confidence=0.0)

        # ── Compute ─────────────────────────────────────────────────────
        yield_data = compute_yield(finance)
        nim_data = compute_nim(finance)
        risk_metrics = ctx.metrics  # from upstream risk agent

        portfolio_yield = yield_data.get("portfolio_yield", 0)
        nim = nim_data.get("net_interest_margin", 0)
        cost_of_risk = risk_metrics.get("cost_of_risk", 0)

        metrics: Dict[str, Any] = {
            **yield_data, **nim_data,
            "cost_of_risk_from_risk_agent": cost_of_risk,
            "risk_adjusted_margin": nim - cost_of_risk if nim and cost_of_risk else None,
        }

        # ── Threshold checks ────────────────────────────────────────────
        target_min = guardrails.get("target_apr_min", 0.34)
        target_max = guardrails.get("target_apr_max", 0.40)

        if portfolio_yield and portfolio_yield < target_min:
            alerts.append(self._alert(
                "yield_below_target", "warning",
                f"Portfolio yield {portfolio_yield:.2%} < target {target_min:.0%}",
                "Yield below minimum target APR.",
                metric_id="portfolio_yield",
                current_value=portfolio_yield, threshold=target_min,
            ))
            actions.append(self._action(
                "raise_rates", "Raise origination rates",
                owner="finance", urgency="medium", impact="high",
                details=f"Current yield {portfolio_yield:.2%} vs target floor {target_min:.0%}.",
            ))

        if portfolio_yield and portfolio_yield > target_max:
            recommendations.append(self._recommendation(
                "competitive_risk", "Yield above ceiling — competitive risk",
                rationale=f"Yield {portfolio_yield:.2%} > {target_max:.0%}. May lose deals to competitors.",
                expected_impact="Adjust rates to stay within band.",
            ))

        # Risk-adjusted margin check
        ram = metrics.get("risk_adjusted_margin")
        if ram is not None and ram < 0.10:
            alerts.append(self._alert(
                "margin_compression", "critical",
                f"Risk-adjusted margin {ram:.2%}",
                "NIM minus cost-of-risk is below 10% — pricing does not cover risk.",
                metric_id="risk_adjusted_margin",
                current_value=ram, threshold=0.10,
            ))

        return self._build_output(
            summary=(
                f"Pricing: Yield={portfolio_yield:.2%}, NIM={nim:.2%}, "
                f"Risk-adj margin={ram:.2%} if {ram is not None} else 'N/A'. "
                f"{len(alerts)} alerts."
            ),
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.90,
            metrics=metrics,
        )
