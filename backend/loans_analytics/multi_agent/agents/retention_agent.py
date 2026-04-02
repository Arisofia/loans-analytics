"""Retention Agent — Layer 4 executive.

Analyses repeat borrower behaviour and payment patterns to identify
at-risk customers and recommend retention strategies.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class RetentionAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "retention"

    @property
    def dependencies(self) -> List[str]:
        return ["segmentation", "collections"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        cust_features = ctx.features.get("customer_features", pd.DataFrame())
        alerts = []
        recommendations = []
        actions = []
        metrics: Dict[str, Any] = {}

        if isinstance(cust_features, pd.DataFrame) and cust_features.empty:
            return self._build_output(summary="No customer data for retention.", confidence=0.0)

        total = len(cust_features)
        metrics["total_customers"] = total

        # ── Repeat rate ─────────────────────────────────────────────────
        if "is_repeat" in cust_features.columns:
            repeat_pct = float(cust_features["is_repeat"].mean())
            metrics["repeat_rate"] = round(repeat_pct, 4)
            if repeat_pct < 0.25:
                alerts.append(self._alert(
                    "low_repeat", "warning",
                    f"Repeat rate {repeat_pct:.0%}",
                    "Most customers are one-time — retention risk.",
                ))
                actions.append(self._action(
                    "retention_program", "Design customer retention program",
                    owner="commercial", urgency="medium", impact="high",
                    details="Target high-value first-time customers for renewal.",
                ))

        # ── At-risk customers (good history, now delinquent) ────────────
        if "worst_status" in cust_features.columns and "loan_count" in cust_features.columns:
            at_risk = cust_features[
                (cust_features["loan_count"] > 1) &
                (cust_features["worst_status"] == "delinquent")
            ]
            metrics["at_risk_repeat_customers"] = len(at_risk)
            if len(at_risk) > 0:
                exposure = float(at_risk["total_exposure"].sum()) if "total_exposure" in at_risk.columns else 0
                metrics["at_risk_exposure"] = exposure
                alerts.append(self._alert(
                    "repeat_delinquent", "warning",
                    f"{len(at_risk)} repeat customers now delinquent (${exposure:,.0f})",
                    "Loyal customers deteriorating — outreach needed.",
                ))
                recommendations.append(self._recommendation(
                    "save_repeats", "Priority outreach to delinquent repeat customers",
                    rationale=f"{len(at_risk)} loyal customers with ${exposure:,.0f} at risk.",
                    expected_impact="Recover relationships and reduce churn.",
                ))

        return self._build_output(
            summary=f"Retention: {total} customers, {metrics.get('repeat_rate', 0):.0%} repeat. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.82,
            metrics=metrics,
        )
