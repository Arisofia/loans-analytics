"""Decision Orchestrator — runs all agents in dependency order.

Collects actions from every agent, resolves conflicts using the
priority hierarchy (data_integrity > regulatory > liquidity > risk >
margin > growth > expansion), and produces a final
``DecisionCenterState`` consumed by the frontend.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Dict, List

from backend.loans_analytics.multi_agent.agents.decision_agent_base import (
    AgentContext,
    AgentOutput,
    DecisionAgent,
)
from backend.src.contracts.agent_schema import DecisionCenterState

# ── agent imports ────────────────────────────────────────────────────────
from backend.loans_analytics.multi_agent.agents.data_quality_agent import DataQualityAgent
from backend.loans_analytics.multi_agent.agents.risk_agent import RiskAgent
from backend.loans_analytics.multi_agent.agents.cohort_vintage_agent import CohortVintageAgent
from backend.loans_analytics.multi_agent.agents.concentration_agent import ConcentrationAgent
from backend.loans_analytics.multi_agent.agents.pricing_agent import PricingAgent
from backend.loans_analytics.multi_agent.agents.segmentation_agent import SegmentationAgent
from backend.loans_analytics.multi_agent.agents.sales_agent import SalesAgent
from backend.loans_analytics.multi_agent.agents.collections_agent import CollectionsAgent
from backend.loans_analytics.multi_agent.agents.marketing_agent import MarketingAgent
from backend.loans_analytics.multi_agent.agents.liquidity_agent import LiquidityAgent
from backend.loans_analytics.multi_agent.agents.covenant_agent import CovenantAgent
from backend.loans_analytics.multi_agent.agents.revenue_strategy_agent import RevenueStrategyAgent
from backend.loans_analytics.multi_agent.agents.retention_agent import RetentionAgent
from backend.loans_analytics.multi_agent.agents.narrative_agent import NarrativeAgent

logger = logging.getLogger(__name__)

# ── Priority hierarchy for conflict resolution ─────────────────────────
_PRIORITY_MAP = {
    "data_quality": 0,
    "covenant": 1,
    "liquidity": 2,
    "risk": 3,
    "collections": 4,
    "pricing": 5,
    "revenue_strategy": 6,
    "sales": 7,
    "segmentation": 8,
    "marketing": 9,
    "retention": 10,
    "cohort_vintage": 11,
    "concentration": 12,
    "narrative": 13,
}


def _build_run_order() -> List[DecisionAgent]:
    """Return agents in topological dependency order."""
    return [
        DataQualityAgent(),       # Layer 0
        RiskAgent(),              # Layer 1
        CohortVintageAgent(),     # Layer 1
        ConcentrationAgent(),     # Layer 1
        PricingAgent(),           # Layer 2
        SegmentationAgent(),      # Layer 2
        SalesAgent(),             # Layer 2
        CollectionsAgent(),       # Layer 3
        MarketingAgent(),         # Layer 3
        LiquidityAgent(),         # Layer 3
        CovenantAgent(),          # Layer 3
        RevenueStrategyAgent(),   # Layer 4
        RetentionAgent(),         # Layer 4
        NarrativeAgent(),         # Layer 4
    ]


class DecisionOrchestrator:
    """Run all decision agents and produce a DecisionCenterState."""

    def __init__(self) -> None:
        self._agents = _build_run_order()

    def run(
        self,
        marts: Dict[str, Any],
        metrics_seed: Dict[str, Any],
        features: Dict[str, Any],
        scenarios: List[Dict[str, Any]],
        business_params: Dict[str, Any],
    ) -> DecisionCenterState:
        """Execute the full agent pipeline.

        Parameters
        ----------
        marts : dict of DataFrames from ``build_all_marts``
        metrics_seed : initial metric values (e.g. from KPI engine)
        features : output of ``build_all_features``
        scenarios : list of ScenarioResult dicts
        business_params : loaded ``business_parameters.yml``
        """
        accumulated_metrics: Dict[str, Any] = dict(metrics_seed)
        agent_outputs: Dict[str, AgentOutput] = {}
        blocked_agents: set[str] = set()
        all_alerts = []
        all_actions = []
        all_recommendations = []
        agent_statuses: Dict[str, str] = {}

        for agent in self._agents:
            aid = agent.agent_id

            # ── Check if blocked ────────────────────────────────────────
            if aid in blocked_agents:
                logger.info("Agent %s SKIPPED — blocked by upstream.", aid)
                agent_statuses[aid] = "blocked"
                continue

            # ── Check dependency outputs ────────────────────────────────
            deps_met = all(
                d in agent_outputs or d == "*"
                for d in agent.dependencies
            )
            if not deps_met:
                logger.warning("Agent %s dependencies not met: %s", aid, agent.dependencies)
                agent_statuses[aid] = "skipped"
                continue

            # ── Build context with accumulated metrics ──────────────────
            ctx = AgentContext(
                marts=marts,
                metrics=accumulated_metrics,
                features=features,
                scenarios=scenarios,
                business_params=business_params,
            )

            # ── Run ─────────────────────────────────────────────────────
            try:
                output = agent.run(ctx)
                agent_outputs[aid] = output
                agent_statuses[aid] = output.status

                # Accumulate metrics from this agent
                if output.metrics:
                    accumulated_metrics.update(output.metrics)

                # Collect alerts/actions
                all_alerts.extend(output.alerts)
                all_actions.extend(output.actions)
                all_recommendations.extend(output.recommendations)

                # Handle blocking
                if output.blocked_by:
                    for blocked_id in output.blocked_by:
                        if blocked_id == "data_quality":
                            # DQ blocks everything downstream
                            blocked_agents.update(
                                a.agent_id for a in self._agents if a.agent_id != "data_quality"
                            )
                        elif blocked_id in ("sales", "marketing"):
                            blocked_agents.add(blocked_id)

                logger.info("Agent %s completed: %s", aid, output.summary[:120])

            except Exception as exc:
                logger.error("Agent %s FAILED: %s", aid, exc)
                agent_statuses[aid] = "error"

        # ── Resolve action conflicts by priority ────────────────────────
        ranked_actions = sorted(
            all_actions,
            key=lambda a: _PRIORITY_MAP.get(a.action_id.split(".")[0], 99),
        )

        critical_alerts = [a for a in all_alerts if a.severity == "critical"]

        # ── Determine business state ────────────────────────────────────
        if any(aid == "data_quality" and st == "blocked" for aid, st in agent_statuses.items()):
            state = "data_blocked"
        elif len(critical_alerts) >= 3:
            state = "critical"
        elif len(critical_alerts) >= 1:
            state = "attention"
        elif accumulated_metrics.get("breaches", 0) > 0:
            state = "covenant_watch"
        else:
            state = "healthy"

        # ── Narrative summary ───────────────────────────────────────────
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
            ranked_actions=[a.model_dump() for a in ranked_actions],
            blocked_actions=[a.model_dump() for a in all_actions if a.action_id.split(".")[0] in blocked_agents],
            opportunities=[r.model_dump() for r in all_recommendations],
            scenario_summary=scenario_summary,
            agent_statuses=agent_statuses,
        )
