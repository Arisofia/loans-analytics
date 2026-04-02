"""Revenue Strategy Agent — Layer 4 executive.

Cross-cuts pricing, sales, and collections to align revenue strategy.
Identifies margin compression, production gaps, and collection drag.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class RevenueStrategyAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "revenue_strategy"

    @property
    def dependencies(self) -> List[str]:
        return ["pricing", "sales", "collections"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        m = ctx.metrics
        alerts = []
        recommendations = []
        actions = []
        metrics: Dict[str, Any] = {}

        # ── Revenue health check ────────────────────────────────────────
        nim = m.get("net_interest_margin")
        portfolio_yield = m.get("portfolio_yield")
        collection_rate = m.get("collection_rate")

        if nim is not None:
            metrics["net_interest_margin"] = nim
            if nim < 0.15:
                alerts.append(self._alert(
                    "thin_margin", "warning",
                    f"NIM {nim:.2%} approaching break-even",
                    "Net interest margin too thin for sustainable operations.",
                    metric_id="net_interest_margin",
                    current_value=nim, threshold=0.15,
                ))

        # ── Revenue leakage from collections ────────────────────────────
        if collection_rate is not None and collection_rate < 0.95:
            leakage_est = m.get("total_outstanding_balance", 0) * (1 - collection_rate)
            metrics["estimated_revenue_leakage"] = leakage_est
            alerts.append(self._alert(
                "collection_drag", "warning",
                f"Collection rate {collection_rate:.2%} — est. leakage ${leakage_est:,.0f}",
                "Low collection directly reduces realized revenue.",
            ))
            actions.append(self._action(
                "plug_leakage", "Address collection-to-revenue gap",
                owner="finance", urgency="high", impact="high",
                details=f"Estimated ${leakage_est:,.0f} revenue at risk from uncollected balances.",
            ))

        # ── Cross-agent revenue maximization ────────────────────────────
        disb = m.get("disbursement_volume_mtd", 0)
        avg_ticket = m.get("avg_ticket", 0)
        if disb and avg_ticket and portfolio_yield:
            projected_annual_revenue = disb * 12 * portfolio_yield
            metrics["projected_annual_revenue"] = round(projected_annual_revenue, 2)

        # ── Strategy recommendations ────────────────────────────────────
        if portfolio_yield and nim and portfolio_yield > 0.35 and nim > 0.20:
            recommendations.append(self._recommendation(
                "healthy_margins", "Margins support growth",
                rationale=f"Yield {portfolio_yield:.2%}, NIM {nim:.2%} — room to invest in origination.",
                expected_impact="Accelerate production without margin compression.",
            ))

        return self._build_output(
            summary=f"Revenue Strategy: NIM={nim}, Yield={portfolio_yield}. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.85,
            metrics=metrics,
        )
