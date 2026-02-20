import json
from pathlib import Path

import pytest

from src.agents.monitoring.performance_tracker import PerformanceMetric, PerformanceTracker


def test_performance_metric_to_dict():
    """Test PerformanceMetric to_dict conversion."""
    metric = PerformanceMetric(
        operation_name="test_op",
        duration_ms=100.5,
        success=True,
        agent_name="test_agent",
        scenario_name="test_scenario",
    )
    d = metric.to_dict()
    assert d["operation_name"] == "test_op"
    assert d["duration_ms"] == 100.5
    assert d["success"] is True
    assert d["agent_name"] == "test_agent"
    assert d["scenario_name"] == "test_scenario"
    assert "timestamp" in d


def test_performance_tracker_latency():
    """Test tracking scenario and agent latency."""
    tracker = PerformanceTracker()

    # Track scenario latency
    tracker.track_scenario_latency("scenario_1", 200.0, True)
    assert len(tracker.metrics) == 1
    assert len(tracker.scenario_metrics["scenario_1"]) == 1

    # Track agent latency
    tracker.track_agent_latency("agent_1", 50.0, True, scenario_name="scenario_1")
    assert len(tracker.metrics) == 2
    assert len(tracker.agent_metrics["agent_1"]) == 1
    assert len(tracker.scenario_metrics["scenario_1"]) == 2


def test_performance_tracker_success_rate():
    """Test success rate calculation."""
    tracker = PerformanceTracker()
    rate_info = tracker.track_success_rate("scenario_1", 8, 2)
    assert rate_info["success_rate"] == 80.0
    assert rate_info["total"] == 10


def test_get_latency_percentiles():
    """Test latency percentile calculations."""
    tracker = PerformanceTracker()
    metrics = [
        PerformanceMetric("op", 10.0, True),
        PerformanceMetric("op", 20.0, True),
        PerformanceMetric("op", 30.0, True),
        PerformanceMetric("op", 40.0, True),
        PerformanceMetric("op", 50.0, True),
    ]
    percentiles = tracker.get_latency_percentiles(metrics)
    assert percentiles["p50"] == 30.0
    assert percentiles["avg"] == 30.0
    assert percentiles["min"] == 10.0
    assert percentiles["max"] == 50.0
    assert percentiles["p95"] > 40.0


def test_get_performance_report(tmp_path):
    """Test generating and saving a performance report."""
    tracker = PerformanceTracker()
    tracker.track_scenario_latency("scenario_1", 150.0, True)
    tracker.track_agent_latency("agent_1", 60.0, True, "scenario_1")

    report = tracker.get_performance_report()
    assert "timestamp" in report
    assert report["total_operations"] == 2
    assert "scenario_1" in report["scenarios"]
    assert "agent_1" in report["agents"]

    report_file = tmp_path / "report.json"
    tracker.save_report(str(report_file))
    assert report_file.exists()
    with open(report_file, "r") as f:
        saved_report = json.load(f)
    assert saved_report["total_operations"] == 2
