"""Sales Agent — Layer 2 strategy.

Evaluates disbursement velocity, pipeline health, and seller
performance against monthly targets from business_parameters.yml.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent
from backend.src.kpi_engine.revenue import compute_disbursement_mtd, compute_new_loans_mtd
from backend.src.kpi_engine.unit_economics import compute_avg_ticket, compute_repeat_rate


class SalesAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "sales"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "pricing", "segmentation"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        sales = ctx.marts.get("sales_mart", pd.DataFrame())
        alerts = []
        recommendations = []
        actions = []

        if sales.empty:
            return self._build_output(summary="No sales mart data.", confidence=0.0)

        # ── Compute metrics ─────────────────────────────────────────────
        disb = compute_disbursement_mtd(sales)
        new_loans = compute_new_loans_mtd(sales)
        ticket = compute_avg_ticket(sales)
        repeat = compute_repeat_rate(sales)

        metrics: Dict[str, Any] = {**disb, **new_loans, **ticket, **repeat}

        # ── Target comparison ───────────────────────────────────────────
        targets = ctx.business_params.get("portfolio_targets_2026", {})
        month_key = dt.date.today().strftime("%Y-%m")
        target = targets.get(month_key, 0)
        volume = disb.get("disbursement_volume_mtd", 0)

        if target and volume:
            pct_of_target = volume / target
            metrics["target_mtd"] = target
            metrics["pct_of_target"] = round(pct_of_target, 4)

            if pct_of_target < 0.50:
                day_of_month = dt.date.today().day
                if day_of_month > 15:
                    alerts.append(self._alert(
                        "behind_target", "critical",
                        f"Only {pct_of_target:.0%} of monthly target with {day_of_month}d elapsed",
                        "Production is materially behind target — requires acceleration.",
                        metric_id="disbursement_volume_mtd",
                        current_value=volume, threshold=target * 0.5,
                    ))
                    actions.append(self._action(
                        "accelerate_pipeline", "Accelerate pending applications",
                        owner="commercial", urgency="high", impact="high",
                        details="Push approved-not-disbursed pipeline.",
                    ))

        # ── KAM performance ─────────────────────────────────────────────
        if "kam_hunter" in sales.columns:
            hunter_volume = (
                sales.groupby("kam_hunter")
                .agg(vol=pd.NamedAgg(column="amount", aggfunc=lambda x: pd.to_numeric(x, errors="coerce").sum()))
                .sort_values("vol", ascending=False)
            )
            if not hunter_volume.empty:
                top_hunter = hunter_volume.index[0]
                metrics["top_hunter"] = str(top_hunter)
                metrics["top_hunter_volume"] = float(hunter_volume.iloc[0]["vol"])

        return self._build_output(
            summary=(
                f"Sales: Disb MTD ${volume:,.0f}, {new_loans.get('new_loans_count_mtd', 0)} loans, "
                f"Avg ticket ${ticket.get('avg_ticket', 0):,.0f}, "
                f"Repeat {repeat.get('repeat_borrower_rate', 0):.1%}. {len(alerts)} alerts."
            ),
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.90,
            metrics=metrics,
        )
