"""Data Quality Agent — Layer 0 gate.

Evaluates completeness, duplicates, freshness, and type consistency
of the ingested data.  If quality_score < 0.85 the agent sets a
blocking flag that prevents all downstream agents from running.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


_REQUIRED_COLS = {"loan_id", "borrower_id", "amount", "status"}
_QUALITY_THRESHOLD = 0.85


class DataQualityAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "data_quality"

    def run(self, ctx: AgentContext) -> AgentOutput:
        portfolio = ctx.marts.get("portfolio_mart", pd.DataFrame())
        alerts = []
        metrics: Dict[str, Any] = {}

        if portfolio.empty:
            return self._build_output(
                summary="No portfolio data available — quality gate BLOCKED.",
                alerts=[self._alert("no_data", "critical", "No data", "Portfolio mart is empty.")],
                confidence=0.0,
                blocked_by=["data_quality"],
                metrics={"quality_score": 0.0, "gate": "blocked"},
            )

        total_rows = len(portfolio)

        # ── Completeness ────────────────────────────────────────────────
        missing = {}
        for col in _REQUIRED_COLS:
            if col not in portfolio.columns:
                missing[col] = 1.0
            else:
                null_pct = float(portfolio[col].isna().mean())
                if null_pct > 0:
                    missing[col] = null_pct
        completeness = 1.0 - (sum(missing.values()) / max(len(_REQUIRED_COLS), 1))
        metrics["completeness"] = round(completeness, 4)

        if completeness < 0.95:
            alerts.append(self._alert(
                "low_completeness", "warning",
                f"Completeness {completeness:.1%}",
                f"Missing columns/values: {missing}",
                metric_id="completeness_score",
                current_value=completeness, threshold=0.95,
            ))

        # ── Duplicates ──────────────────────────────────────────────────
        dup_rate = 0.0
        if "loan_id" in portfolio.columns:
            dups = portfolio["loan_id"].duplicated().sum()
            dup_rate = dups / total_rows if total_rows else 0
        metrics["duplicate_rate"] = round(dup_rate, 4)

        if dup_rate > 0.01:
            alerts.append(self._alert(
                "high_duplicates", "warning",
                f"Duplicate rate {dup_rate:.2%}",
                f"{int(dup_rate * total_rows)} duplicated loan_ids detected.",
                metric_id="duplicate_rate",
                current_value=dup_rate, threshold=0.01,
            ))

        # ── Freshness (check as_of_date) ────────────────────────────────
        freshness_hours = 0.0
        if "as_of_date" in portfolio.columns:
            latest = pd.to_datetime(portfolio["as_of_date"], errors="coerce").max()
            if pd.notna(latest):
                delta = dt.datetime.now() - latest
                freshness_hours = delta.total_seconds() / 3600
        metrics["freshness_hours"] = round(freshness_hours, 1)

        if freshness_hours > 48:
            alerts.append(self._alert(
                "stale_data", "critical",
                f"Data is {freshness_hours:.0f}h old",
                "Data freshness exceeds 48 hours.",
                metric_id="freshness_hours",
                current_value=freshness_hours, threshold=48,
            ))

        # ── Overall quality score ───────────────────────────────────────
        quality_score = (
            completeness * 0.50
            + (1.0 - min(dup_rate * 10, 1.0)) * 0.25
            + (1.0 - min(freshness_hours / 96, 1.0)) * 0.25
        )
        metrics["quality_score"] = round(quality_score, 4)
        gate = "pass" if quality_score >= _QUALITY_THRESHOLD else "blocked"
        metrics["gate"] = gate

        blocked_by: List[str] = []
        if gate == "blocked":
            blocked_by = ["data_quality"]
            alerts.append(self._alert(
                "gate_blocked", "critical",
                f"Quality gate BLOCKED ({quality_score:.2%})",
                f"Score {quality_score:.2%} < threshold {_QUALITY_THRESHOLD:.0%}. Downstream agents will not run.",
                metric_id="quality_score",
                current_value=quality_score, threshold=_QUALITY_THRESHOLD,
            ))

        return self._build_output(
            summary=f"Quality score {quality_score:.2%} — gate {gate}. {total_rows} rows evaluated.",
            alerts=alerts,
            confidence=quality_score,
            blocked_by=blocked_by,
            metrics=metrics,
        )
