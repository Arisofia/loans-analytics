"""CFO agent — executive-level financial summary and capital stewardship.

Synthesizes capital adequacy, covenant status, P&L trajectory, and ROE/ROA
into a board-ready brief.  Depends on risk, revenue_strategy, liquidity,
and covenant agents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.src.contracts.agent_schema import AgentOutput
from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, DecisionAgent

logger = logging.getLogger(__name__)


class CFOAgent(DecisionAgent):
    """Layer 4 executive agent — capital & P&L stewardship."""

    @property
    def agent_id(self) -> str:
        return "cfo"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "revenue_strategy", "liquidity", "covenant"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        metrics = ctx.metrics
        alerts = []
        recommendations = []
        actions = []

        # ── Capital adequacy ─────────────────────────────────────────────
        roe = metrics.get("roe")
        roa = metrics.get("roa")
        d_e = metrics.get("debt_to_equity")
        covenant_status = metrics.get("covenant_status", "pass")
        breaches = metrics.get("covenant_breaches", [])

        evidence: Dict[str, Any] = {
            "roe": roe,
            "roa": roa,
            "debt_to_equity": d_e,
            "covenant_status": covenant_status,
        }

        # Covenant breach alert
        if covenant_status == "breach":
            alerts.append(self._alert(
                "covenant_breach", "critical",
                f"Covenant breach detected: {', '.join(breaches)}",
                "Active covenant breach requires immediate action.",
                metric_id="covenant_status",
            ))
            actions.append(self._action(
                "restrict_growth",
                "Halt new disbursements until covenant cure",
                owner="treasury",
                urgency="critical",
                impact="high",
            ))

        # ROE/ROA monitoring
        if roe is not None and roe < 8.0:
            alerts.append(self._alert(
                "low_roe", "warning",
                f"ROE at {roe:.1f}% — below 8% target",
                "Return on equity is below the minimum board-approved threshold.",
                metric_id="roe",
                current_value=roe,
                threshold=8.0,
            ))
            recommendations.append(self._recommendation(
                "improve_roe",
                "Review pricing strategy to improve return on equity",
                rationale="ROE below 8% target erodes shareholder value.",
                expected_impact="Restore ROE above target within 2 quarters",
                confidence=0.8,
            ))

        # Leverage check
        if d_e is not None and d_e > 4.0:
            alerts.append(self._alert(
                "high_leverage", "warning",
                f"D/E ratio at {d_e:.2f} — above 4x threshold",
                "Leverage exceeds prudential limit.",
                metric_id="debt_to_equity",
                current_value=d_e,
                threshold=4.0,
            ))

        # Liquidity check
        liq = metrics.get("liquidity_ratio")
        if liq is not None and liq < 5.0:
            alerts.append(self._alert(
                "low_liquidity", "critical",
                f"Liquidity ratio at {liq:.1f}% — below 5% minimum",
                "Liquidity ratio is critically low — escalation required.",
                metric_id="liquidity_ratio",
                current_value=liq,
                threshold=5.0,
            ))
            actions.append(self._action(
                "liquidity_alert",
                "Escalate to treasury for immediate funding review",
                owner="treasury",
                urgency="high",
                impact="high",
            ))

        # NPL trend
        npl = metrics.get("npl_ratio")
        if npl is not None:
            evidence["npl_ratio"] = npl
            if npl > 10.0:
                recommendations.append(self._recommendation(
                    "npl_provision",
                    "NPL above 10% — recommend provisioning review",
                    rationale=f"NPL ratio at {npl:.1f}% exceeds 10% threshold.",
                    expected_impact="Adequate provisioning protects capital base",
                    confidence=0.85,
                ))

        # Summary
        summary_parts = [f"ROE {roe:.1f}%" if roe else "ROE n/a"]
        summary_parts.append(f"ROA {roa:.1f}%" if roa else "ROA n/a")
        summary_parts.append(f"D/E {d_e:.2f}" if d_e else "D/E n/a")
        summary_parts.append(f"Covenant: {covenant_status}")
        summary = "CFO Brief — " + " | ".join(summary_parts)

        confidence = 0.9 if covenant_status == "pass" else 0.7

        return self._build_output(
            summary=summary,
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=confidence,
            evidence=evidence,
        )
