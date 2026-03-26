"""Segmentation Agent — Layer 2 strategy.

Analyses customer/loan segments from the feature store and recommends
differentiated strategies per segment.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class SegmentationAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "segmentation"

    @property
    def dependencies(self) -> List[str]:
        return ["risk", "concentration"]

    def run(self, ctx: AgentContext) -> AgentOutput:
        seg_profiles = ctx.features.get("segment_profiles", {})
        segments: List[Dict[str, Any]] = seg_profiles.get("segments", [])
        total_customers = seg_profiles.get("total_customers", 0)
        alerts = []
        recommendations = []

        metrics: Dict[str, Any] = {
            "total_customers": total_customers,
            "segment_count": len(segments),
        }

        if not segments:
            return self._build_output(
                summary="No segment data available.",
                confidence=0.0,
                metrics=metrics,
            )

        # ── Analyse each segment ────────────────────────────────────────
        for seg in segments:
            name = seg.get("segment", "unknown")
            count = seg.get("count", 0)

            # Warn on heavy-risk segments
            if name.startswith("risk_defaulted") and count > 0:
                pct = count / max(total_customers, 1)
                alerts.append(self._alert(
                    f"defaulted_segment_{name}", "warning",
                    f"{count} defaulted customers ({pct:.1%})",
                    "Defaulted customer segment requires exclusion from growth campaigns.",
                    current_value=pct,
                ))

            # Opportunity in repeat borrowers
            if "repeat_pct" in seg and seg["repeat_pct"] > 0.40:
                recommendations.append(self._recommendation(
                    f"repeat_{name}", f"High repeat rate in {name}",
                    rationale=f"Repeat rate {seg['repeat_pct']:.0%} — upsell opportunity.",
                    expected_impact="Increase AUM via line increases.",
                ))

        # ── Concentration by segment ────────────────────────────────────
        ticket_segments = [s for s in segments if s["segment"].startswith("ticket_")]
        if ticket_segments:
            largest = max(ticket_segments, key=lambda s: s.get("total_exposure", 0))
            largest_pct = largest.get("total_exposure", 0) / max(
                sum(s.get("total_exposure", 0) for s in ticket_segments), 1,
            )
            metrics["largest_segment"] = largest["segment"]
            metrics["largest_segment_pct"] = round(largest_pct, 4)
            if largest_pct > 0.60:
                alerts.append(self._alert(
                    "segment_concentration", "warning",
                    f"Segment {largest['segment']} = {largest_pct:.0%} of exposure",
                    "Over-concentration in a single segment increases systemic risk.",
                ))

        return self._build_output(
            summary=f"Segmentation: {len(segments)} segments, {total_customers} customers. {len(alerts)} alerts.",
            alerts=alerts,
            recommendations=recommendations,
            confidence=0.85,
            metrics=metrics,
        )
