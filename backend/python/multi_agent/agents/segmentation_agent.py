from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.decision_agent_base import AgentContext, AgentOutput, DecisionAgent


class SegmentationAgent(DecisionAgent):
    @property
    def agent_id(self) -> str:
        return "segmentation"

    def run(self, ctx: AgentContext) -> AgentOutput:
        seg = ctx.features.get("segment_features", pd.DataFrame())
        alerts = []

        if not seg.empty and "avg_dpd" in seg.columns:
            risky = seg[seg["avg_dpd"] > 30]
            if not risky.empty:
                alerts.append(self._alert(
                    "risky_segments", "warning",
                    f"{len(risky)} high-DPD segments",
                    "Segments with avg DPD > 30 detected.",
                ))

        return self._build_output(
            summary=f"{len(seg)} segments analysed",
            alerts=alerts,
            confidence=0.85,
        )
