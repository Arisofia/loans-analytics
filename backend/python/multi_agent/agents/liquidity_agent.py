"""Liquidity Agent — Layer 3 operations.

Monitors cash position, funding utilization, and scenario projections
to ensure liquidity adequacy per business_parameters.yml thresholds.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.liquidity import compute_funding_utilization, compute_liquidity_ratio


class LiquidityAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "liquidity"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "collections"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        treasury = ctx.marts.get("treasury_mart", pd.DataFrame())
        guardrails = ctx.business_params.get("financial_guardrails", {})
        alerts = []
        recommendations = []
        actions = []

        if treasury.empty:
            return self._build_output(summary="No treasury data for liquidity.", confidence=0.0)

        # ── Compute ─────────────────────────────────────────────────────
        liq = compute_liquidity_ratio(treasury)
        util = compute_funding_utilization(treasury)
        metrics: Dict[str, Any] = {**liq, **util}

        ratio = liq.get("liquidity_ratio", 0)
        status = liq.get("status", "unknown")

        # ── Threshold checks ────────────────────────────────────────────
        if status == "critical":
            alerts.append(self._alert(
                "liquidity_critical", "critical",
                f"Liquidity ratio {ratio:.2%} — CRITICAL",
                "Below minimum reserve. Halt new disbursements until remediated.",
                metric_id="liquidity_ratio",
                current_value=ratio,
                threshold=guardrails.get("min_liquidity_reserve_pct", 0.05),
            ))
            actions.append(self._action(
                "halt_disbursements", "Halt new disbursements",
                owner="treasury", urgency="critical", impact="critical",
                details="Liquidity below floor — no new origination until restored.",
            ))

        elif status == "warning":
            alerts.append(self._alert(
                "liquidity_warning", "warning",
                f"Liquidity ratio {ratio:.2%} — below target",
                "Approaching minimum threshold.",
                metric_id="liquidity_ratio",
                current_value=ratio,
                threshold=guardrails.get("target_liquidity_reserve_pct", 0.08),
            ))

        # ── Utilization check ───────────────────────────────────────────
        util_pct = util.get("funding_utilization", 0)
        util_max = guardrails.get("utilization_max", 0.90)
        if util_pct and util_pct > util_max:
            alerts.append(self._alert(
                "over_utilized", "warning",
                f"Funding utilization {util_pct:.2%} > {util_max:.0%}",
                "Near credit facility ceiling — request line increase.",
                metric_id="funding_utilization",
                current_value=util_pct, threshold=util_max,
            ))

        # ── Scenario stress check ───────────────────────────────────────
        for scenario in ctx.scenarios:
            if scenario.get("scenario") == "stress":
                stress_liq = scenario.get("projected", {}).get("liquidity_ratio")
                if stress_liq is not None and stress_liq < 0.03:
                    alerts.append(self._alert(
                        "stress_insolvency", "critical",
                        f"Stress scenario liquidity {stress_liq:.2%}",
                        "Under stress conditions, liquidity falls below survival threshold.",
                    ))

        return self._build_output(
            summary=f"Liquidity: ratio={ratio:.2%} ({status}), utilization={util_pct:.2%}. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.92,
            metrics=metrics,
        )
