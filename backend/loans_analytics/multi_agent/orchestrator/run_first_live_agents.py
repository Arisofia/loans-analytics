from __future__ import annotations

from typing import Any

import pandas as pd


from backend.loans_analytics.multi_agent.agents.data_quality_agent import DataQualityAgent
from backend.loans_analytics.multi_agent.agents.pricing_agent import PricingAgent
from backend.loans_analytics.multi_agent.agents.risk_agent import RiskAgent
from backend.loans_analytics.multi_agent.agents.sales_agent import SalesAgent
from backend.loans_analytics.multi_agent.agents.segmentation_agent import SegmentationAgent
from backend.loans_analytics.multi_agent.agents.decision_agent_base import AgentContext
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
        ctx = AgentContext(
            marts=marts,
            metrics=metrics,
            features=features,
            scenarios=[],  # TODO: pass real scenarios if available
            business_params={},  # TODO: pass real business_params if available
            as_of_date=None
        )
        output = agent.run(ctx)
        outputs.append(output)
    return outputs
