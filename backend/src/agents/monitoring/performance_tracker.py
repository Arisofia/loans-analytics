from __future__ import annotations
import json
import math
import statistics
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

@dataclass
class PerformanceMetric:
    operation_name: str
    duration_ms: float
    success: bool
    agent_name: Optional[str] = None
    scenario_name: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {'operation_name': self.operation_name, 'duration_ms': self.duration_ms, 'success': self.success, 'agent_name': self.agent_name, 'scenario_name': self.scenario_name, 'timestamp': self.timestamp}

class PerformanceTracker:

    def __init__(self):
        self._lock = threading.RLock()
        self.metrics: List[PerformanceMetric] = []
        self.scenario_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.agent_metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)

    @staticmethod
    def _validate_name(name: str, field_name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f'{field_name} must be a non-empty string')

    @staticmethod
    def _validate_duration(duration_ms: float) -> None:
        if not isinstance(duration_ms, (int, float)) or not math.isfinite(duration_ms):
            raise ValueError('duration_ms must be a finite number')
        if duration_ms < 0:
            raise ValueError('duration_ms must be non-negative')

    @staticmethod
    def _validate_count(name: str, value: int) -> None:
        if not isinstance(value, int):
            raise ValueError(f'{name} must be an integer')
        if value < 0:
            raise ValueError(f'{name} must be non-negative')

    def track_scenario_latency(self, scenario_name: str, duration_ms: float, success: bool=True) -> PerformanceMetric:
        self._validate_name(scenario_name, 'scenario_name')
        self._validate_duration(duration_ms)
        metric = PerformanceMetric(operation_name=scenario_name, duration_ms=duration_ms, success=success, scenario_name=scenario_name)
        with self._lock:
            self.metrics.append(metric)
            self.scenario_metrics[scenario_name].append(metric)
        return metric

    def track_agent_latency(self, agent_name: str, duration_ms: float, success: bool=True, scenario_name: Optional[str]=None) -> PerformanceMetric:
        self._validate_name(agent_name, 'agent_name')
        self._validate_duration(duration_ms)
        if scenario_name is not None:
            self._validate_name(scenario_name, 'scenario_name')
        metric = PerformanceMetric(operation_name=f'{agent_name}_execution', duration_ms=duration_ms, success=success, agent_name=agent_name, scenario_name=scenario_name)
        with self._lock:
            self.metrics.append(metric)
            self.agent_metrics[agent_name].append(metric)
            if scenario_name:
                self.scenario_metrics[scenario_name].append(metric)
        return metric

    def track_success_rate(self, scenario_name: str, successes: int, failures: int) -> Dict[str, Any]:
        self._validate_name(scenario_name, 'scenario_name')
        self._validate_count('successes', successes)
        self._validate_count('failures', failures)
        total = successes + failures
        success_rate = successes / total if total > 0 else 0.0
        return {'scenario_name': scenario_name, 'successes': successes, 'failures': failures, 'total': total, 'success_rate': round(success_rate * 100, 2)}

    def get_latency_percentiles(self, metrics: List[PerformanceMetric]) -> Dict[str, float]:
        if not metrics:
            return {'p50': 0.0, 'p95': 0.0, 'p99': 0.0, 'avg': 0.0, 'min': 0.0, 'max': 0.0}
        durations = [m.duration_ms for m in metrics]
        durations.sort()
        return {'p50': round(statistics.median(durations), 2), 'p95': round(self._percentile(durations, 0.95), 2), 'p99': round(self._percentile(durations, 0.99), 2), 'avg': round(statistics.mean(durations), 2), 'min': round(min(durations), 2), 'max': round(max(durations), 2)}

    def get_scenario_performance(self, scenario_name: str) -> Dict[str, Any]:
        self._validate_name(scenario_name, 'scenario_name')
        with self._lock:
            metrics = list(self.scenario_metrics.get(scenario_name, []))
        if not metrics:
            return {'scenario_name': scenario_name, 'total_executions': 0, 'success_rate': 0.0, 'latency': {}}
        successes = sum((m.success for m in metrics))
        failures = len(metrics) - successes
        success_rate = successes / len(metrics) if metrics else 0.0
        return {'scenario_name': scenario_name, 'total_executions': len(metrics), 'successes': successes, 'failures': failures, 'success_rate': round(success_rate * 100, 2), 'latency': self.get_latency_percentiles(metrics)}

    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        self._validate_name(agent_name, 'agent_name')
        with self._lock:
            metrics = list(self.agent_metrics.get(agent_name, []))
        if not metrics:
            return {'agent_name': agent_name, 'total_executions': 0, 'success_rate': 0.0, 'latency': {}}
        successes = sum((m.success for m in metrics))
        failures = len(metrics) - successes
        success_rate = successes / len(metrics) if metrics else 0.0
        return {'agent_name': agent_name, 'total_executions': len(metrics), 'successes': successes, 'failures': failures, 'success_rate': round(success_rate * 100, 2), 'latency': self.get_latency_percentiles(metrics)}

    def get_performance_report(self, time_window: Optional[str]=None) -> Dict[str, Any]:
        _ = time_window
        with self._lock:
            scenario_names = list(self.scenario_metrics.keys())
            agent_names = list(self.agent_metrics.keys())
            total_operations = len(self.metrics)
        scenarios = {name: self.get_scenario_performance(name) for name in scenario_names}
        agents = {name: self.get_agent_performance(name) for name in agent_names}
        return {'timestamp': datetime.now(timezone.utc).isoformat(), 'total_operations': total_operations, 'scenarios': scenarios, 'agents': agents}

    def save_report(self, output_path: str) -> None:
        report = self.get_performance_report()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

    def _percentile(self, data: List[float], percentile: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * percentile
        f = int(k)
        c = k - f
        return data[f] + c * (data[f + 1] - data[f]) if f + 1 < len(data) else data[f]
