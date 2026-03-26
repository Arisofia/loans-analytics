"""Modular decision orchestrator — replaces the monolithic version.

Uses the dependency_graph for topological ordering, priority_rules
for conflict resolution, and action_router for dispatching.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, List, Optional

from backend.python.multi_agent.agents.decision_agent_base import (
    AgentContext,
    AgentOutput,
    DecisionAgent,
)
from backend.python.multi_agent.orchestrator.action_router import route_actions
from backend.python.multi_agent.orchestrator.dependency_graph import get_execution_order
from backend.python.multi_agent.orchestrator.priority_rules import priority_rank
from backend.src.contracts.agent_schema import DecisionCenterState

# ── Agent class registry ────────────────────────────────────────────────
from backend.python.multi_agent.agents.cfo_agent import CFOAgent
from backend.python.multi_agent.agents.cohort_vintage_agent import CohortVintageAgent
from backend.python.multi_agent.agents.collections_agent import CollectionsAgent
from backend.python.multi_agent.agents.concentration_agent import ConcentrationAgent
from backend.python.multi_agent.agents.covenant_agent import CovenantAgent
from backend.python.multi_agent.agents.data_quality_agent import DataQualityAgent
from backend.python.multi_agent.agents.liquidity_agent import LiquidityAgent
from backend.python.multi_agent.agents.marketing_agent import MarketingAgent
from backend.python.multi_agent.agents.narrative_agent import NarrativeAgent
from backend.python.multi_agent.agents.pricing_agent import PricingAgent
from backend.python.multi_agent.agents.retention_agent import RetentionAgent
from backend.python.multi_agent.agents.revenue_strategy_agent import RevenueStrategyAgent
from backend.python.multi_agent.agents.risk_agent import RiskAgent
from backend.python.multi_agent.agents.sales_agent import SalesAgent
from backend.python.multi_agent.agents.segmentation_agent import SegmentationAgent

logger = logging.getLogger(__name__)

_AGENT_CLASSES: Dict[str, type] = {
    "data_quality": DataQualityAgent,
    "risk": RiskAgent,
    "cohort_vintage": CohortVintageAgent,
    "concentration": ConcentrationAgent,
    "pricing": PricingAgent,
    "segmentation": SegmentationAgent,
    "sales": SalesAgent,
    "collections": CollectionsAgent,
    "marketing": MarketingAgent,
    "liquidity": LiquidityAgent,
    "covenant": CovenantAgent,
    "revenue_strategy": RevenueStrategyAgent,
    "retention": RetentionAgent,
    "narrative": NarrativeAgent,
    "cfo": CFOAgent,
}


class DecisionOrchestrator:
    """Run all decision agents in dependency order with conflict resolution."""

    def __init__(self) -> None:
        self._order = get_execution_order()
        self._agents: Dict[str, DecisionAgent] = {}
        for aid in self._order:
            cls = _AGENT_CLASSES.get(aid)
            if cls:
                self._agents[aid] = cls()

    def run(
        self,
        marts: Dict[str, Any],
        metrics_seed: Dict[str, Any],
        features: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        business_params: Dict[str, Any],
    ) -> DecisionCenterState:
        accumulated_metrics: Dict[str, Any] = dict(metrics_seed)
        agent_outputs: Dict[str, AgentOutput] = {}
        blocked_agents: set[str] = set()
        all_alerts: list = []
        all_actions: list = []
        all_recommendations: list = []
        agent_statuses: Dict[str, str] = {}

        for aid in self._order:
            agent = self._agents.get(aid)
            if agent is None:
                continue

            if aid in blocked_agents:
                logger.info("Agent %s SKIPPED — blocked", aid)
                agent_statuses[aid] = "blocked"
                continue

            deps_met = all(
                d in agent_outputs for d in agent.dependencies
            )
            if not deps_met:
                logger.warning("Agent %s deps not met", aid)
                agent_statuses[aid] = "skipped"
                continue

            ctx = AgentContext(
                marts=marts,
                metrics=accumulated_metrics,
                features=features,
                scenarios=scenarios,
                business_params=business_params,
            )

            try:
                output = agent.run(ctx)
                agent_outputs[aid] = output
                agent_statuses[aid] = output.status

                if output.metrics:
                    accumulated_metrics.update(output.metrics)

                all_alerts.extend(output.alerts)
                all_actions.extend(output.actions)
                all_recommendations.extend(output.recommendations)

                if output.blocked_by:
                    for blocked_id in output.blocked_by:
                        if blocked_id == "data_quality":
                            blocked_agents.update(
                                a for a in self._order if a != "data_quality"
                            )
                        else:
                            blocked_agents.add(blocked_id)

                logger.info("Agent %s done: %s", aid, output.summary[:120])

            except Exception as exc:
                logger.error("Agent %s FAILED: %s", aid, exc)
                agent_statuses[aid] = "error"

        # ── Rank and route actions ──────────────────────────────────────
        action_dicts = [a.model_dump() for a in all_actions]
        ranked = sorted(action_dicts, key=lambda a: priority_rank(a.get("agent_id", "")))
        routed = route_actions(ranked)

        critical_alerts = [a for a in all_alerts if a.severity == "critical"]

        if any(st == "blocked" for st in agent_statuses.values()):
            state = "data_blocked"
        elif len(critical_alerts) >= 3:
            state = "critical"
        elif len(critical_alerts) >= 1:
            state = "attention"
        else:
            state = "healthy"

        scenario_summary = {}
        for sc in scenarios:
            scenario_summary[sc.get("scenario", "unknown")] = {
                "triggers": sc.get("triggers", []),
                "horizon": sc.get("horizon_months"),
            }

        return DecisionCenterState(
            timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
            business_state=state,
            critical_alerts=[a.model_dump() for a in critical_alerts],
            ranked_actions=routed,
            blocked_actions=[
                a for a in routed
                if a.get("action_id", "").split(".")[0] in blocked_agents
            ],
            opportunities=[r.model_dump() for r in all_recommendations],
            scenario_summary=scenario_summary,
            agent_statuses=agent_statuses,
        )
