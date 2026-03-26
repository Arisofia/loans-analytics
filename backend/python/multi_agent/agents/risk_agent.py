"""Risk Agent — Layer 1 core analytics.

Evaluates PAR, NPL, default rate, expected loss, roll rates, and
cost of risk from real portfolio data.  Issues alerts when thresholds
from business_parameters.yml are breached.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.risk import (
    compute_cost_of_risk,
    compute_cure_rate,
    compute_default_rate,
    compute_expected_loss,
    compute_npl,
    compute_par,
    compute_roll_rates,
)


class RiskAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "risk"

    @property
    def dependencies(self) -> List[str]:
        return ["data_quality"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        collections = ctx.marts.get("collections_mart", pd.DataFrame())
        alerts = []
        recommendations = []
        actions = []
        guardrails = ctx.business_params.get("financial_guardrails", {})
        risk_params = ctx.business_params.get("risk_parameters", {})
        lgd = risk_params.get("loss_given_default", 0.10)

        if portfolio.empty:
            return self._build_output(
                summary="No portfolio data for risk analysis.",
                confidence=0.0,
            )

        # ── Compute metrics ─────────────────────────────────────────────
        par = compute_par(portfolio)
        npl = compute_npl(portfolio)
        default = compute_default_rate(portfolio)
        el = compute_expected_loss(portfolio, lgd)
        rolls = compute_roll_rates(portfolio)
        cor = compute_cost_of_risk(portfolio)
        cure = compute_cure_rate(collections)

        metrics: Dict[str, Any] = {
            **par, **npl, **default, **el, **rolls, **cor, **cure,
        }

        # ── Threshold checks ────────────────────────────────────────────
        max_default = guardrails.get("max_default_rate", 0.04)
        if default.get("default_rate", 0) > max_default:
            alerts.append(self._alert(
                "default_breach", "critical",
                f"Default rate {default['default_rate']:.2%} > {max_default:.0%}",
                "Default rate exceeds guardrail — escalate to collections and liquidity.",
                metric_id="default_rate",
                current_value=default.get("default_rate", 0),
                threshold=max_default,
            ))
            actions.append(self._action(
                "tighten_origination", "Tighten origination criteria",
                owner="risk", urgency="high", impact="high",
                details="Reduce approval rates for high-DPD segments.",
            ))

        # PAR thresholds (repline)
        for bucket, limit_key in [("par_30", "repline_30d_max_pct"),
                                   ("par_60", "repline_60d_max_pct"),
                                   ("par_90", "repline_90d_max_pct")]:
            limit = guardrails.get(limit_key, 1.0)
            val = par.get(bucket, 0)
            if val > limit:
                alerts.append(self._alert(
                    f"{bucket}_breach", "warning",
                    f"{bucket.upper()} {val:.2%} > {limit:.0%}",
                    f"PAR bucket exceeds repline covenant limit.",
                    metric_id=bucket, current_value=val, threshold=limit,
                ))

        # ── Recommendations ─────────────────────────────────────────────
        if par.get("par_30", 0) > 0.10:
            recommendations.append(self._recommendation(
                "early_collection", "Intensify early-stage collections",
                rationale=f"PAR30 at {par['par_30']:.2%} — early intervention reduces roll.",
                expected_impact="Reduce PAR30 by 2-5pp",
            ))

        if cure.get("cure_rate", 0) < 0.50:
            recommendations.append(self._recommendation(
                "restructure_program", "Launch restructuring program",
                rationale=f"Cure rate only {cure.get('cure_rate', 0):.2%} — delinquent loans not curing.",
                expected_impact="Improve cure rate to 60%+",
            ))

        return self._build_output(
            summary=(
                f"Risk: PAR30={par.get('par_30', 0):.2%}, NPL={npl.get('npl_ratio', 0):.2%}, "
                f"Default={default.get('default_rate', 0):.2%}, EL={el.get('expected_loss_pct', 0):.4%}. "
                f"{len(alerts)} alerts."
            ),
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.95,
            metrics=metrics,
        )
