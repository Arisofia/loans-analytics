"""Narrative Agent — Layer 4 executive.

Packages all agent outputs into a board-ready executive narrative.
Pure text synthesis from structured data — no LLM dependency.
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class NarrativeAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "narrative"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "revenue_strategy", "liquidity"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        m = ctx.metrics
        scenarios = ctx.scenarios
        alerts_from_all = []  # Collect critical alerts from upstream
        metrics: Dict[str, Any] = {}

        # ── Headline metrics ────────────────────────────────────────────
        aum = m.get("total_outstanding_balance", 0)
        par30 = m.get("par_30", 0)
        npl = m.get("npl_ratio", 0)
        default = m.get("default_rate", 0)
        collection_rate = m.get("collection_rate", 0)
        nim = m.get("net_interest_margin", 0)
        liq = m.get("liquidity_ratio", 0)
        disb = m.get("disbursement_volume_mtd", 0)

        # ── Build narrative sections ────────────────────────────────────
        sections = []

        # Portfolio overview
        sections.append(
            f"**Portfolio Overview** — AUM ${aum:,.0f}. "
            f"PAR30 {par30:.2%}, NPL {npl:.2%}, Default {default:.2%}."
        )

        # Revenue
        sections.append(
            f"**Revenue** — NIM {nim:.2%}, Collection rate {collection_rate:.2%}. "
            f"MTD disbursements ${disb:,.0f}."
        )

        # Liquidity
        sections.append(f"**Liquidity** — Ratio {liq:.2%}.")

        # Scenario summary
        for sc in scenarios:
            name = sc.get("scenario", "")
            triggers = sc.get("triggers", [])
            if triggers:
                sections.append(f"**Scenario {name.title()}** — {'; '.join(triggers)}.")

        # Covenant status
        breaches = m.get("breaches", 0)
        if breaches:
            sections.append(f"**Covenant** — {breaches} breach(es) detected. Growth activities blocked.")
        else:
            sections.append("**Covenant** — All covenants in compliance.")

        narrative = "\n\n".join(sections)
        metrics["narrative_length"] = len(narrative)
        metrics["generated_at"] = dt.datetime.now(dt.timezone.utc).isoformat()

        return self._build_output(
            summary=narrative,
            alerts=alerts_from_all,
            confidence=0.80,
            metrics=metrics,
            evidence={"sections": sections},
        )
