"""Marketing Agent — Layer 3 operations.

Evaluates channel performance, repeat-borrower mix, and segment
opportunities to recommend campaign actions.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class MarketingAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "marketing"

    @property
    def dependencies(self) -> List[str]:
        return ["segmentation", "sales"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        marketing = ctx.marts.get("marketing_mart", pd.DataFrame())
        seg_profiles = ctx.features.get("segment_profiles", {})
        alerts: list[Any] = []
        recommendations: list[Any] = []
        actions = []
        metrics: Dict[str, Any] = {}

        # ── Channel analysis ────────────────────────────────────────────
        if not marketing.empty and "advisory_channel" in marketing.columns:
            channel_dist = marketing.groupby("advisory_channel").size()
            metrics["channel_distribution"] = channel_dist.to_dict()
            digital_pct = 0.0
            for ch, ct in channel_dist.items():
                if str(ch).lower() in ("digital", "online", "app"):
                    digital_pct += ct
            if channel_dist.sum() > 0:
                digital_pct /= channel_dist.sum()
            metrics["digital_pct"] = round(digital_pct, 4)

            if digital_pct < 0.20:
                recommendations.append(self._recommendation(
                    "increase_digital", "Low digital channel penetration",
                    rationale=f"Only {digital_pct:.0%} digital — growth opportunity.",
                    expected_impact="Reduce CAC and improve scalability.",
                ))

        # ── Repeat vs new mix ───────────────────────────────────────────
        repeat_rate = ctx.metrics.get("repeat_borrower_rate", 0)
        metrics["repeat_borrower_rate"] = repeat_rate
        if repeat_rate and repeat_rate < 0.30:
            recommendations.append(self._recommendation(
                "retention_campaign", "Launch retention campaign",
                rationale=f"Repeat rate {repeat_rate:.0%} — loyalty program needed.",
                expected_impact="Increase repeat rate to 40%+.",
            ))
            actions.append(self._action(
                "launch_loyalty", "Design loyalty/referral program",
                owner="commercial", urgency="medium", impact="medium",
            ))

        # ── Segment targeting ───────────────────────────────────────────
        segments = seg_profiles.get("segments", [])
        for seg in segments:
            if seg.get("segment", "").startswith("ticket_micro") and seg.get("count", 0) > 0:
                recommendations.append(self._recommendation(
                    "micro_digital", "Target micro segment via digital",
                    rationale="Micro segment is cost-sensitive — digital-only servicing.",
                    expected_impact="Lower CAC for micro segment.",
                ))
                break

        return self._build_output(
            summary=f"Marketing: {len(recommendations)} recommendations, {len(actions)} actions.",
            alerts=alerts,
            recommendations=recommendations,
            actions=actions,
            confidence=0.80,
            metrics=metrics,
        )
