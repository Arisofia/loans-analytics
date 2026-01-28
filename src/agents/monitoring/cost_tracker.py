"""Cost tracking for multi-agent system.

Tracks LLM token usage, API calls, database operations, and compute costs.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AgentCost:
    """Cost metrics for a single agent execution."""

    agent_name: str
    scenario_name: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0
    api_calls: int = 0
    db_operations: int = 0
    execution_time_ms: float = 0
    cost_usd: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_name": self.agent_name,
            "scenario_name": self.scenario_name,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_total,
            "api_calls": self.api_calls,
            "db_operations": self.db_operations,
            "execution_time_ms": self.execution_time_ms,
            "cost_usd": self.cost_usd,
            "timestamp": self.timestamp,
        }


class CostTracker:
    """Track costs for multi-agent system execution."""

    # Cost per 1K tokens (approximate OpenAI GPT-4o-mini pricing)
    COST_PER_1K_INPUT_TOKENS = 0.00015
    COST_PER_1K_OUTPUT_TOKENS = 0.0006

    def __init__(self):
        """Initialize cost tracker."""
        self.metrics: Dict[str, List[AgentCost]] = {}
        self.current_scenario: Optional[str] = None

    def start_scenario(self, scenario_name: str) -> None:
        """Start tracking a new scenario."""
        self.current_scenario = scenario_name
        if scenario_name not in self.metrics:
            self.metrics[scenario_name] = []

    def track_agent_execution(
        self,
        agent_name: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        execution_time_ms: float = 0,
    ) -> AgentCost:
        """Track cost for a single agent execution.

        Args:
            agent_name: Name of the agent
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            execution_time_ms: Execution time in milliseconds

        Returns:
            AgentCost object with computed costs
        """
        if not self.current_scenario:
            raise ValueError("No active scenario. Call start_scenario() first.")

        tokens_total = tokens_input + tokens_output
        cost = self._calculate_token_cost(tokens_input, tokens_output)

        agent_cost = AgentCost(
            agent_name=agent_name,
            scenario_name=self.current_scenario,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
            execution_time_ms=execution_time_ms,
            cost_usd=cost,
        )

        self.metrics[self.current_scenario].append(agent_cost)
        return agent_cost

    def track_api_call(
        self,
        agent_name: str,
        service: str,
        endpoint: str,
        cost: float = 0.001,
    ) -> None:
        """Track third-party API costs.

        Args:
            agent_name: Name of the agent making the call
            service: Service name (e.g., 'supabase', 'n8n')
            endpoint: API endpoint called
            cost: Cost per API call in USD
        """
        if not self.current_scenario:
            raise ValueError("No active scenario. Call start_scenario() first.")

        # Track as API call
        scenario_metrics = self.metrics.get(self.current_scenario, [])
        for metric in reversed(scenario_metrics):
            if metric.agent_name == agent_name:
                metric.api_calls += 1
                metric.cost_usd += cost
                break

    def get_scenario_cost(self, scenario_name: str) -> Dict[str, Any]:
        """Calculate total cost for a scenario.

        Args:
            scenario_name: Name of the scenario

        Returns:
            Dictionary with cost breakdown
        """
        if scenario_name not in self.metrics:
            return {
                "scenario_name": scenario_name,
                "total_cost_usd": 0.0,
                "total_tokens": 0,
                "total_api_calls": 0,
                "agent_count": 0,
                "agents": [],
            }

        scenario_metrics = self.metrics[scenario_name]
        total_cost = sum(m.cost_usd for m in scenario_metrics)
        total_tokens = sum(m.tokens_total for m in scenario_metrics)
        total_api_calls = sum(m.api_calls for m in scenario_metrics)

        agent_costs = {}
        for metric in scenario_metrics:
            if metric.agent_name not in agent_costs:
                agent_costs[metric.agent_name] = {
                    "cost_usd": 0.0,
                    "tokens": 0,
                    "api_calls": 0,
                }
            agent_costs[metric.agent_name]["cost_usd"] += metric.cost_usd
            agent_costs[metric.agent_name]["tokens"] += metric.tokens_total
            agent_costs[metric.agent_name]["api_calls"] += metric.api_calls

        return {
            "scenario_name": scenario_name,
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_api_calls": total_api_calls,
            "agent_count": len(agent_costs),
            "agents": [
                {"name": name, **costs} for name, costs in agent_costs.items()
            ],
        }

    def compare_to_baseline(
        self,
        scenario_name: str,
        baseline_cost: float,
        threshold: float = 0.10,
    ) -> Dict[str, Any]:
        """Compare scenario cost to baseline and alert if exceeded.

        Args:
            scenario_name: Name of the scenario
            baseline_cost: Baseline cost in USD
            threshold: Alert threshold (default 0.10 = 10%)

        Returns:
            Dictionary with comparison results
        """
        current = self.get_scenario_cost(scenario_name)
        current_cost = current["total_cost_usd"]

        if baseline_cost == 0:
            increase_percentage = 0.0
            alert = False
        else:
            increase_percentage = (current_cost - baseline_cost) / baseline_cost
            alert = increase_percentage > threshold

        return {
            "scenario_name": scenario_name,
            "baseline_cost_usd": baseline_cost,
            "current_cost_usd": current_cost,
            "increase_percentage": round(increase_percentage * 100, 2),
            "threshold_percentage": threshold * 100,
            "alert": alert,
            "message": (
                f"⚠️ Cost increased by {increase_percentage*100:.1f}% "
                f"(threshold: {threshold*100:.1f}%)"
                if alert
                else f"✅ Cost within acceptable range ({increase_percentage*100:.1f}% change)"
            ),
        }

    def save_report(self, output_path: str) -> None:
        """Save cost report to JSON file.

        Args:
            output_path: Path to save the report
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "scenarios": {
                name: self.get_scenario_cost(name) for name in self.metrics.keys()
            },
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

    def _calculate_token_cost(
        self, tokens_input: int, tokens_output: int
    ) -> float:
        """Calculate cost based on token usage."""
        input_cost = (tokens_input / 1000) * self.COST_PER_1K_INPUT_TOKENS
        output_cost = (tokens_output / 1000) * self.COST_PER_1K_OUTPUT_TOKENS
        return input_cost + output_cost
