"""CFO agent — executive-level financial summary and capital stewardship.

Synthesizes capital adequacy, covenant status, P&L trajectory, and ROE/ROA
into a board-ready brief.  Depends on risk, revenue_strategy, liquidity,
and covenant agents.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from backend.src.contracts.agent_schema import AgentAction, AgentAlert, AgentOutput, AgentRecommendation
from backend.python.multi_agent.agents.decision_agent_base import AgentContext, DecisionAgent

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
        alerts: List[AgentAlert] = []
        recommendations: List[AgentRecommendation] = []
        actions: List[AgentAction] = []

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
            alerts.append(AgentAlert(
                severity="critical",
                message=f"Covenant breach detected: {', '.join(breaches)}",
                metric_id="covenant_status",
            ))
            actions.append(AgentAction(
                action_type="restrict_growth",
                description="Halt new disbursements until covenant cure",
                priority=1,
            ))

        # ROE/ROA monitoring
        if roe is not None and roe < 8.0:
            alerts.append(AgentAlert(
                severity="warning",
                message=f"ROE at {roe:.1f}% — below 8% target",
                metric_id="roe",
            ))
            recommendations.append(AgentRecommendation(
                recommendation="Review pricing strategy to improve return on equity",
                confidence=0.8,
                impact="medium",
            ))

        # Leverage check
        if d_e is not None and d_e > 4.0:
            alerts.append(AgentAlert(
                severity="warning",
                message=f"D/E ratio at {d_e:.2f} — above 4x threshold",
                metric_id="debt_to_equity",
            ))

        # Liquidity check
        liq = metrics.get("liquidity_ratio")
        if liq is not None and liq < 5.0:
            alerts.append(AgentAlert(
                severity="critical",
                message=f"Liquidity ratio at {liq:.1f}% — below 5% minimum",
                metric_id="liquidity_ratio",
            ))
            actions.append(AgentAction(
                action_type="liquidity_alert",
                description="Escalate to treasury for immediate funding review",
                priority=2,
            ))

        # NPL trend
        npl = metrics.get("npl_ratio")
        if npl is not None:
            evidence["npl_ratio"] = npl
            if npl > 10.0:
                recommendations.append(AgentRecommendation(
                    recommendation="NPL above 10% — recommend provisioning review",
                    confidence=0.85,
                    impact="high",
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
