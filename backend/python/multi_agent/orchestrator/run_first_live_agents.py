from __future__ import annotations

from typing import Any

import pandas as pd

from backend.python.multi_agent.agents.data_quality_agent import DataQualityAgent
from backend.python.multi_agent.agents.pricing_agent import PricingAgent
from backend.python.multi_agent.agents.risk_agent import RiskAgent
from backend.python.multi_agent.agents.sales_agent import SalesAgent
from backend.python.multi_agent.agents.segmentation_agent import SegmentationAgent
from backend.src.contracts.agent_schema import AgentOutput


def run_first_live_agents(
    marts: dict[str, pd.DataFrame],
    metrics: dict[str, Any],
    features: dict[str, pd.DataFrame],
    quality: dict[str, Any],
) -> list[AgentOutput]:
    agents = [
        DataQualityAgent(),
        RiskAgent(),
        PricingAgent(),
        SegmentationAgent(),
        SalesAgent(),
    ]
    outputs: list[AgentOutput] = []
    for agent in agents:
        output = agent.run(marts, metrics, features, quality)
        outputs.append(output)
    return outputs
