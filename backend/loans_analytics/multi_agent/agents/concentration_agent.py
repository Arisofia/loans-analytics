"""Concentration Agent — Layer 1 core analytics.

Measures portfolio concentration by borrower (HHI) and top-N exposure.
Flags breaches of the 30% top-10 concentration limit and single-obligor
cap from business_parameters.yml.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.concentration import compute_hhi, compute_top_n


class ConcentrationAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "concentration"

    @property
    def dependencies(self) -> List[str]:
        return ["data_quality"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        guardrails = ctx.business_params.get("financial_guardrails", {})
        alerts: list[Any] = []
        recommendations: list[Any] = []
        actions = []
        metrics: Dict[str, Any] = {}

        if portfolio.empty:
            return self._build_output(summary="No portfolio data for concentration.", confidence=0.0)

        # ── Compute ─────────────────────────────────────────────────────
        hhi = compute_hhi(portfolio)
        top_n = compute_top_n(portfolio)
        metrics.update(hhi)
        metrics.update(top_n)

        # ── HHI thresholds ──────────────────────────────────────────────
        hhi_val = hhi.get("hhi_index", 0)
        hhi_level = hhi.get("hhi_level", "unknown")
        if hhi_level == "high":
            alerts.append(self._alert(
                "hhi_high", "critical",
                f"HHI {hhi_val:.0f} — highly concentrated",
                "Portfolio is over-concentrated by borrower.",
                metric_id="hhi_index",
                current_value=hhi_val, threshold=2500,
            ))
            actions.append(self._action(
                "diversify", "Diversify borrower base",
                owner="commercial", urgency="high", impact="high",
                details="Originate smaller tickets across more borrowers.",
            ))
        elif hhi_level == "moderate":
            alerts.append(self._alert(
                "hhi_moderate", "warning",
                f"HHI {hhi_val:.0f} — moderate concentration",
                "Approaching high concentration zone.",
                metric_id="hhi_index",
                current_value=hhi_val, threshold=1500,
            ))

        # ── Top-10 concentration ────────────────────────────────────────
        max_top10 = guardrails.get("max_top_10_concentration", 0.30)
        top10 = top_n.get("top_10_pct", 0)
        if top10 > max_top10:
            alerts.append(self._alert(
                "top10_breach", "critical",
                f"Top-10 = {top10:.1%} > {max_top10:.0%} limit",
                "Fund covenant breach on single-name concentration.",
                metric_id="top_10_concentration",
                current_value=top10, threshold=max_top10,
            ))

        # ── Single obligor cap ──────────────────────────────────────────
        max_single = guardrails.get("max_single_obligor_concentration", 0.04)
        top1 = top_n.get("top_1_pct", 0)
        if top1 > max_single:
            alerts.append(self._alert(
                "single_obligor", "critical",
                f"Largest borrower = {top1:.1%} > {max_single:.0%} limit",
                "Single obligor exceeds cap — reduce exposure.",
                metric_id="top_1_concentration",
                current_value=top1, threshold=max_single,
            ))

        return self._build_output(
            summary=f"Concentration: HHI={hhi_val:.0f} ({hhi_level}), Top10={top10:.1%}. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.95,
            metrics=metrics,
        )
