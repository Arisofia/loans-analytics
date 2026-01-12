#!/usr/bin/env python3
"""
Unified metrics analysis script.

Analyzes agent performance, pipeline health, and data quality trends from Opik metrics.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_metrics():
    """Analyze all metrics from opik_metrics.json."""
    metrics_file = Path("outputs/opik_metrics.json")

    if not metrics_file.exists():
        logger.error("Metrics file not found")
        raise FileNotFoundError("outputs/opik_metrics.json not found")

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    # 1. Agent Performance
    agent_metrics = metrics.get("agents", {})
    avg_response_time = agent_metrics.get("average_response_time_ms", 0)
    error_rate = agent_metrics.get("error_rate", 0)

    if avg_response_time < 1000 and error_rate < 0.05:
        agent_status = "optimal"
        slow_agents = "none"
    elif avg_response_time < 2000 and error_rate < 0.10:
        agent_status = "acceptable"
        slow_agents = "some"
    else:
        agent_status = "degraded"
        slow_agents = "multiple"

    # 2. Pipeline Health
    pipeline_metrics = metrics.get("pipeline", {})
    total_runs = pipeline_metrics.get("total_runs", 0)
    failed_runs = pipeline_metrics.get("failed_runs", 0)
    failure_rate = failed_runs / total_runs if total_runs > 0 else 0

    if total_runs == 0:
        pipeline_status = "unknown"
        pipeline_issues = 1
    elif failure_rate < 0.05:
        pipeline_status = "healthy"
        pipeline_issues = 0
    elif failure_rate < 0.15:
        pipeline_status = "degraded"
        pipeline_issues = 1
    else:
        pipeline_status = "unhealthy"
        pipeline_issues = 2

    # 3. Data Quality Trends
    quality_metrics = metrics.get("data_quality", {})
    completeness = quality_metrics.get("completeness_score", 0)
    validity = quality_metrics.get("validity_score", 0)
    anomalies = quality_metrics.get("anomalies_detected", 0)
    avg_quality = (completeness + validity) / 2

    if avg_quality > 0.95 and anomalies < 5:
        quality_trend = "stable"
        anomalies_detected = "false"
    elif avg_quality > 0.85 and anomalies < 10:
        quality_trend = "declining"
        anomalies_detected = "false"
    else:
        quality_trend = "critical"
        anomalies_detected = "true"

    # Summary
    logger.info(f"Agent performance: {agent_status}")
    logger.info(f"Pipeline health: {pipeline_status}")
    logger.info(f"Data quality trend: {quality_trend}")

    # Write unified analysis results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    analysis = {
        "agents": {
            "status": agent_status,
            "slow_agents": slow_agents,
            "average_response_time_ms": avg_response_time,
            "error_rate": error_rate,
        },
        "pipeline": {
            "health_status": pipeline_status,
            "issues_count": pipeline_issues,
            "total_runs": total_runs,
            "failed_runs": failed_runs,
            "failure_rate": failure_rate,
        },
        "data_quality": {
            "trend": quality_trend,
            "anomalies_detected": anomalies_detected,
            "completeness_score": completeness,
            "validity_score": validity,
            "anomaly_count": anomalies,
        }
    }

    with open(output_dir / "metrics_analysis.json", "w") as f:
        json.dump(analysis, f, indent=2)

    return analysis


if __name__ == "__main__":
    try:
        results = analyze_metrics()
        print("✓ Metrics analysis complete")
        print(f"  - Agents: {results['agents']['status']}")
        print(f"  - Pipeline: {results['pipeline']['health_status']}")
        print(f"  - Quality: {results['data_quality']['trend']}")
    except Exception as e:
        logger.error(f"Failed to analyze metrics: {e}")
        exit(1)
