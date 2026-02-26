"""Performance tracking for multi-agent system.

Tracks latency, success rates, and system health metrics.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PerformanceMetric:
    """Performance metric for a single operation."""

    operation_name: str
    duration_ms: float
    success: bool
    agent_name: Optional[str] = None
    scenario_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_name": self.operation_name,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "agent_name": self.agent_name,
            "scenario_name": self.scenario_name,
            "timestamp": self.timestamp,
        }


class PerformanceTracker:
    """Track performance metrics for multi-agent system."""

    def __init__(self):
        """Initialize performance tracker."""
        self.metrics: List[PerformanceMetric] = []
        self.scenario_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.agent_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)

    def track_scenario_latency(
        self,
        scenario_name: str,
        duration_ms: float,
        success: bool = True,
    ) -> PerformanceMetric:
        """Track latency for a scenario.

        Args:
            scenario_name: Name of the scenario
            duration_ms: Duration in milliseconds
            success: Whether the scenario succeeded

        Returns:
            PerformanceMetric object
        """
        metric = PerformanceMetric(
            operation_name=scenario_name,
            duration_ms=duration_ms,
            success=success,
            scenario_name=scenario_name,
        )
        self.metrics.append(metric)
        self.scenario_metrics[scenario_name].append(metric)
        return metric

    def track_agent_latency(
        self,
        agent_name: str,
        duration_ms: float,
        success: bool = True,
        scenario_name: Optional[str] = None,
    ) -> PerformanceMetric:
        """Track latency for an agent.

        Args:
            agent_name: Name of the agent
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
            scenario_name: Optional scenario name

        Returns:
            PerformanceMetric object
        """
        metric = PerformanceMetric(
            operation_name=f"{agent_name}_execution",
            duration_ms=duration_ms,
            success=success,
            agent_name=agent_name,
            scenario_name=scenario_name,
        )
        self.metrics.append(metric)
        self.agent_metrics[agent_name].append(metric)
        if scenario_name:
            self.scenario_metrics[scenario_name].append(metric)
        return metric

    def track_success_rate(
        self,
        scenario_name: str,
        successes: int,
        failures: int,
    ) -> Dict[str, Any]:
        """Track success/failure ratio for a scenario.

        Args:
            scenario_name: Name of the scenario
            successes: Number of successful executions
            failures: Number of failed executions

        Returns:
            Dictionary with success rate metrics
        """
        total = successes + failures
        success_rate = successes / total if total > 0 else 0.0

        return {
            "scenario_name": scenario_name,
            "successes": successes,
            "failures": failures,
            "total": total,
            "success_rate": round(success_rate * 100, 2),
        }

    def get_latency_percentiles(
        self,
        metrics: List[PerformanceMetric],
    ) -> Dict[str, float]:
        """Calculate p50, p95, p99 latency from metrics.

        Args:
            metrics: List of performance metrics

        Returns:
            Dictionary with percentile values
        """
        if not metrics:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "min": 0.0, "max": 0.0}

        durations = [m.duration_ms for m in metrics]
        durations.sort()

        return {
            "p50": round(statistics.median(durations), 2),
            "p95": round(self._percentile(durations, 0.95), 2),
            "p99": round(self._percentile(durations, 0.99), 2),
            "avg": round(statistics.mean(durations), 2),
            "min": round(min(durations), 2),
            "max": round(max(durations), 2),
        }

    def get_scenario_performance(
        self,
        scenario_name: str,
    ) -> Dict[str, Any]:
        """Get performance statistics for a scenario.

        Args:
            scenario_name: Name of the scenario

        Returns:
            Dictionary with performance statistics
        """
        metrics = self.scenario_metrics.get(scenario_name, [])
        if not metrics:
            return {
                "scenario_name": scenario_name,
                "total_executions": 0,
                "success_rate": 0.0,
                "latency": {},
            }

        successes = sum(1 for m in metrics if m.success)
        failures = len(metrics) - successes
        success_rate = successes / len(metrics) if metrics else 0.0

        return {
            "scenario_name": scenario_name,
            "total_executions": len(metrics),
            "successes": successes,
            "failures": failures,
            "success_rate": round(success_rate * 100, 2),
            "latency": self.get_latency_percentiles(metrics),
        }

    def get_agent_performance(
        self,
        agent_name: str,
    ) -> Dict[str, Any]:
        """Get performance statistics for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with performance statistics
        """
        metrics = self.agent_metrics.get(agent_name, [])
        if not metrics:
            return {
                "agent_name": agent_name,
                "total_executions": 0,
                "success_rate": 0.0,
                "latency": {},
            }

        successes = sum(1 for m in metrics if m.success)
        failures = len(metrics) - successes
        success_rate = successes / len(metrics) if metrics else 0.0

        return {
            "agent_name": agent_name,
            "total_executions": len(metrics),
            "successes": successes,
            "failures": failures,
            "success_rate": round(success_rate * 100, 2),
            "latency": self.get_latency_percentiles(metrics),
        }

    def get_performance_report(
        self,
        time_window: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Args:
            time_window: Optional time window (not yet implemented)

        Returns:
            Dictionary with performance report
        """
        # Reserved for future filtering without breaking public API.
        _ = time_window

        scenarios = {name: self.get_scenario_performance(name) for name in self.scenario_metrics}

        agents = {name: self.get_agent_performance(name) for name in self.agent_metrics}

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_operations": len(self.metrics),
            "scenarios": scenarios,
            "agents": agents,
        }

    def save_report(self, output_path: str) -> None:
        """Save performance report to JSON file.

        Args:
            output_path: Path to save the report
        """
        report = self.get_performance_report()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile value from sorted data."""
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile
        f = int(k)
        c = k - f
        if f + 1 < len(data):
            return data[f] + c * (data[f + 1] - data[f])
        return data[f]
