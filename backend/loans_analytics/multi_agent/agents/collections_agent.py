"""Collections Agent — Layer 3 operations.

Evaluates collection rate, cure rate, and PAR trends.  Generates
prioritized work-lists and escalation actions.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.loans_analytics.multi_agent.agents.decision_agent_base import (
    AgentContext,
    AgentOutput,
    DecisionAgent,
)
from backend.src.kpi_engine.risk import compute_par30
from backend.src.kpi_engine.cohorts import compute_roll_rates


def _compute_collection_rate(collections: pd.DataFrame, portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Compute collection rate from available data.

    Uses collections mart if present; falls back to portfolio payment columns.
    Returns dict with ``collection_rate`` (ratio, 0-1) and supporting numerics.
    """
    # --- collections mart path ---
    if not collections.empty:
        sched_col = next(
            (
                c
                for c in ("total_scheduled", "scheduled_amount", "monto_programado")
                if c in collections.columns
            ),
            None,
        )
        recv_col = next(
            (
                c
                for c in ("last_payment_amount", "payment_amount", "monto_pagado")
                if c in collections.columns
            ),
            None,
        )
        if sched_col and recv_col:
            scheduled = float(
                pd.to_numeric(collections[sched_col], errors="coerce").fillna(0).sum()
            )
            received = float(pd.to_numeric(collections[recv_col], errors="coerce").fillna(0).sum())
            rate = received / scheduled if scheduled > 0 else 0.0
            return {
                "collection_rate": rate,
                "collections_received": received,
                "collections_scheduled": scheduled,
            }

    # --- portfolio mart fallback ---
    if not portfolio.empty:
        sched_col = next(
            (c for c in ("total_scheduled", "scheduled_amount") if c in portfolio.columns), None
        )
        recv_col = next(
            (c for c in ("last_payment_amount", "payment_amount") if c in portfolio.columns), None
        )
        if sched_col and recv_col:
            scheduled = float(pd.to_numeric(portfolio[sched_col], errors="coerce").fillna(0).sum())
            received = float(pd.to_numeric(portfolio[recv_col], errors="coerce").fillna(0).sum())
            rate = received / scheduled if scheduled > 0 else 0.0
            return {
                "collection_rate": rate,
                "collections_received": received,
                "collections_scheduled": scheduled,
            }

    return {}


def _compute_cure_rate(portfolio: pd.DataFrame) -> Dict[str, Any]:
    """Compute cure rate: proportion of previously delinquent loans now current.

    Approximated from the portfolio snapshot: loans with status 'active'/'current'
    that still have a non-zero DPD history (dpd > 0 but status re-normalized).
    Falls back to 0 when no delinquency data is available.
    """
    if portfolio.empty:
        return {}

    status_col = next(
        (
            c
            for c in ("status", "loan_status", "current_status", "estado")
            if c in portfolio.columns
        ),
        None,
    )
    dpd_col = next((c for c in ("days_past_due", "dpd") if c in portfolio.columns), None)

    if status_col is None or dpd_col is None:
        return {}

    status = portfolio[status_col].astype(str).str.lower()
    dpd = pd.to_numeric(portfolio[dpd_col], errors="coerce").fillna(0)

    delinquent_ever = (dpd > 0) | status.isin({"delinquent", "late", "past_due", "mora"})
    cured = delinquent_ever & status.isin({"active", "current", "vigente", "open"})

    total_delinquent = int(delinquent_ever.sum())
    cured_count = int(cured.sum())
    cure_rate = cured_count / total_delinquent if total_delinquent > 0 else 0.0

    return {
        "cure_rate": cure_rate,
        "cured_count": cured_count,
        "total_delinquent": total_delinquent,
    }


class CollectionsAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "collections"

    @property
    def dependencies(self) -> List[str]:
        return ["risk"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        collections = ctx.marts.get("collections_mart", pd.DataFrame())
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        guardrails = ctx.business_params.get("financial_guardrails", {})
        alerts = []
        recommendations = []
        actions = []

        if collections.empty and portfolio.empty:
            return self._build_output(summary="No data for collections analysis.", confidence=0.0)

        # ── Compute ─────────────────────────────────────────────────────
        col_rate = _compute_collection_rate(collections, portfolio)
        cure = _compute_cure_rate(portfolio)
        par = {"par30": compute_par30(portfolio)} if not portfolio.empty else {}
        rolls = compute_roll_rates(portfolio) if not portfolio.empty else {}

        metrics: Dict[str, Any] = {**col_rate, **cure, **par, **rolls}

        # ── Collection rate threshold ───────────────────────────────────
        min_coll = guardrails.get("min_collection_rate", 0.985)
        rate = col_rate.get("collection_rate", 0)
        if rate and rate < min_coll:
            alerts.append(
                self._alert(
                    "collection_below_min",
                    "critical",
                    f"Collection rate {rate:.2%} < {min_coll:.1%}",
                    "Fund covenant requires minimum collection rate.",
                    metric_id="collection_rate",
                    current_value=rate,
                    threshold=min_coll,
                )
            )
            actions.append(
                self._action(
                    "intensify_collections",
                    "Deploy intensive collection campaign",
                    owner="operations",
                    urgency="high",
                    impact="high",
                    details="Focus on 30-60 DPD bucket where cure probability is highest.",
                )
            )

        # ── Cure rate analysis ──────────────────────────────────────────
        cure_val = cure.get("cure_rate", 0)
        if cure_val and cure_val < 0.40:
            recommendations.append(
                self._recommendation(
                    "low_cure",
                    "Cure rate critically low",
                    rationale=f"Only {cure_val:.1%} of delinquent loans are curing.",
                    expected_impact="Consider restructuring or write-off programs.",
                )
            )

        # ── Roll rate analysis ──────────────────────────────────────────
        bucket_90_plus = rolls.get("bucket_90_180", 0) + rolls.get("bucket_180_plus", 0)
        if bucket_90_plus > 0.05:
            alerts.append(
                self._alert(
                    "high_90plus",
                    "warning",
                    f"90+ DPD = {bucket_90_plus:.2%} of portfolio",
                    "High proportion of severely delinquent loans.",
                    current_value=bucket_90_plus,
                    threshold=0.05,
                )
            )

        # ── Priority worklist ───────────────────────────────────────────
        if not collections.empty and "dpd" in collections.columns:
            dpd_col = pd.to_numeric(collections["dpd"], errors="coerce").fillna(0)
            high_priority = int((dpd_col.between(30, 60)).sum())
            medium_priority = int((dpd_col.between(61, 90)).sum())
            metrics["high_priority_count"] = high_priority
            metrics["medium_priority_count"] = medium_priority

        return self._build_output(
            summary=(
                f"Collections: Rate={rate:.2%}, Cure={cure_val:.2%}, "
                f"90+ DPD={bucket_90_plus:.2%}. {len(alerts)} alerts."
            ),
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.90,
            metrics=metrics,
        )
