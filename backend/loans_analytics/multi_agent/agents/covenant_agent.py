"""Covenant Agent — Layer 3 compliance.

Validates all fund/lender covenant thresholds against current metrics.
When a breach is detected, blocks growth agents (sales, marketing)
to prevent further exposure growth.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class CovenantAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "covenant"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "liquidity"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        guardrails = ctx.business_params.get("financial_guardrails", {})
        m = ctx.metrics  # aggregated from upstream agents
        alerts = []
        actions = []
        blocked: List[str] = []

        metrics: Dict[str, Any] = {"covenants_checked": 0, "breaches": 0}

        checks = [
            ("collection_rate", m.get("collection_rate"), guardrails.get("min_collection_rate", 0.985), ">="),
            ("par_30", m.get("par_30"), guardrails.get("repline_30d_max_pct", 0.45), "<="),
            ("par_60", m.get("par_60"), guardrails.get("repline_60d_max_pct", 0.35), "<="),
            ("par_90", m.get("par_90"), guardrails.get("repline_90d_max_pct", 0.20), "<="),
            ("default_rate", m.get("default_rate"), guardrails.get("max_default_rate", 0.04), "<="),
            ("top_10_concentration", m.get("top_10_pct"), guardrails.get("max_top_10_concentration", 0.30), "<="),
            ("liquidity_ratio", m.get("liquidity_ratio"), guardrails.get("min_liquidity_reserve_pct", 0.05), ">="),
        ]

        breach_count = 0
        for name, value, threshold, direction in checks:
            metrics["covenants_checked"] = metrics.get("covenants_checked", 0) + 1
            if value is None:
                continue
            breached = (direction == ">=" and value < threshold) or (direction == "<=" and value > threshold)
            if breached:
                breach_count += 1
                severity = "critical" if name in ("collection_rate", "default_rate", "liquidity_ratio") else "warning"
                alerts.append(self._alert(
                    f"covenant_{name}", severity,
                    f"Covenant breach: {name}",
                    f"Current {value:.4f} {'<' if direction == '>=' else '>'} limit {threshold:.4f}.",
                    metric_id=name,
                    current_value=value,
                    threshold=threshold,
                ))

        metrics["breaches"] = breach_count

        if breach_count > 0:
            blocked = ["sales", "marketing"]
            actions.append(self._action(
                "freeze_growth", "Freeze growth activities",
                owner="compliance", urgency="critical", impact="high",
                details=f"{breach_count} covenant breaches — sales and marketing blocked.",
            ))

        return self._build_output(
            summary=f"Covenant: {metrics['covenants_checked']} checked, {breach_count} breaches. {'BLOCKED growth.' if blocked else 'All clear.'}",
            alerts=alerts,
            actions=actions,
            confidence=0.95,
            blocked_by=blocked,
            metrics=metrics,
        )
