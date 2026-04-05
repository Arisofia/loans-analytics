"""Cohort & Vintage Agent — Layer 1 core analytics.

Analyses portfolio performance by origination vintage to identify
deteriorating cohorts and underwriting drift.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import (
    AgentContext,
    AgentOutput,
    DecisionAgent,
)


def _compute_vintages(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Compute per-origination-month vintage metrics from portfolio mart.

    Returns a dict with keys:
    - ``vintages``: {YYYY-MM: {loan_count, default_rate, avg_dpd, total_balance}}
    - ``worst_vintage``: the entry with the highest default_rate
    """
    date_col = next(
        (
            c
            for c in ("origination_date", "disbursement_date", "fecha_desembolso")
            if c in portfolio.columns
        ),
        None,
    )
    if date_col is None:
        return {"vintages": {}, "worst_vintage": {}}

    df = portfolio.copy()
    df["_orig_dt"] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=["_orig_dt"])
    if df.empty:
        return {"vintages": {}, "worst_vintage": {}}

    df["_vintage"] = df["_orig_dt"].dt.to_period("M").astype(str)

    dpd_col = next((c for c in ("days_past_due", "dpd") if c in df.columns), None)
    bal_col = next(
        (c for c in ("outstanding_principal", "outstanding_balance", "amount") if c in df.columns),
        None,
    )
    status_col = next(
        (c for c in ("status", "loan_status", "current_status", "estado") if c in df.columns), None
    )

    vintages: Dict[str, Any] = {}
    for vintage, grp in df.groupby("_vintage"):
        count = len(grp)
        avg_dpd = (
            float(pd.to_numeric(grp[dpd_col], errors="coerce").fillna(0).mean()) if dpd_col else 0.0
        )
        total_bal = (
            float(pd.to_numeric(grp[bal_col], errors="coerce").fillna(0).sum()) if bal_col else 0.0
        )
        if status_col:
            default_rate = float(
                (
                    grp[status_col]
                    .astype(str)
                    .str.lower()
                    .isin({"defaulted", "default", "charged_off"})
                ).sum()
            ) / max(count, 1)
        elif dpd_col:
            default_rate = float(
                (pd.to_numeric(grp[dpd_col], errors="coerce").fillna(0) >= 90).sum()
            ) / max(count, 1)
        else:
            default_rate = 0.0
        vintages[str(vintage)] = {
            "vintage": str(vintage),
            "loan_count": count,
            "default_rate": default_rate,
            "avg_dpd": avg_dpd,
            "total_balance": total_bal,
        }

    worst: Dict[str, Any] = (
        max(vintages.values(), key=lambda v: v["default_rate"]) if vintages else {}
    )
    return {"vintages": vintages, "worst_vintage": worst}


class CohortVintageAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "cohort_vintage"

    @property
    def dependencies(self) -> List[str]:
        return ["data_quality"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        alerts = []
        recommendations = []
        metrics: Dict[str, Any] = {}

        if portfolio.empty:
            return self._build_output(
                summary="No portfolio data for cohort analysis.", confidence=0.0
            )

        # ── Vintage analysis ──────────────────────────────────────────────
        cohorts = _compute_vintages(portfolio)
        metrics.update(cohorts)

        # ── Worst vintage analysis ──────────────────────────────────────
        worst = cohorts.get("worst_vintage", {})
        if worst:
            worst_name = worst.get("vintage", "unknown")
            worst_default = worst.get("default_rate", 0)
            if worst_default > 0.10:
                alerts.append(
                    self._alert(
                        "toxic_vintage",
                        "critical",
                        f"Vintage {worst_name}: {worst_default:.1%} default rate",
                        "This vintage has severe underwriting quality issues.",
                        metric_id="vintage_default_rate",
                        current_value=worst_default,
                        threshold=0.10,
                    )
                )
                recommendations.append(
                    self._recommendation(
                        "investigate_vintage",
                        f"Investigate vintage {worst_name}",
                        rationale=f"Default rate {worst_default:.1%} is 2.5x the portfolio target.",
                        expected_impact="Identify underwriting criteria that failed.",
                    )
                )

        # ── Trend detection ─────────────────────────────────────────────
        vintages = cohorts.get("vintages", {})
        if len(vintages) >= 3:
            sorted_vintages = sorted(vintages.items())
            recent_3 = [v[1].get("default_rate", 0) for v in sorted_vintages[-3:]]
            if all(recent_3[i] < recent_3[i + 1] for i in range(len(recent_3) - 1)):
                alerts.append(
                    self._alert(
                        "deteriorating_trend",
                        "warning",
                        "Default rate rising across last 3 vintages",
                        f"Rates: {', '.join(f'{r:.2%}' for r in recent_3)}",
                    )
                )
                recommendations.append(
                    self._recommendation(
                        "tighten_underwriting",
                        "Tighten underwriting standards",
                        rationale="Three consecutive vintages with rising defaults.",
                        expected_impact="Stabilize future vintage performance.",
                    )
                )

        return self._build_output(
            summary=f"Cohort: {len(vintages)} vintages analysed. Worst={worst.get('vintage', 'N/A')}. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            confidence=0.90,
            metrics=metrics,
        )
