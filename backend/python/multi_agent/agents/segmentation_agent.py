from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.base_agent import BaseAgent
from backend.src.contracts.agent_schema import AgentAlert, AgentOutput


class SegmentationAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "segmentation"

    def run(
        self,
        marts: dict[str, pd.DataFrame],
        metrics: dict[str, Any],
        features: dict[str, pd.DataFrame],
        quality: dict[str, Any],
    ) -> AgentOutput:
        seg = features.get("segment_features", pd.DataFrame())
        alerts: list[AgentAlert] = []

        if not seg.empty and "avg_dpd" in seg.columns:
            risky = seg[seg["avg_dpd"] > 30]
            if not risky.empty:
                alerts.append(AgentAlert(
                    severity="warning",
                    title=f"{len(risky)} high-DPD segments",
                    description="Segments with avg DPD > 30 detected.",
                ))

        return AgentOutput(
            agent_id=self.agent_id,
            status="ok",
            summary=f"{len(seg)} segments analysed",
            alerts=alerts,
            confidence=0.85,
        )
