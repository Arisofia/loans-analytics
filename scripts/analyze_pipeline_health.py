#!/usr/bin/env python3
"""
Analyze pipeline health metrics script.

This script analyzes data pipeline health based on Opik metrics.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_pipeline_health():
    """Analyze pipeline health from metrics."""
    metrics_file = Path("outputs/opik_metrics.json")

    if not metrics_file.exists():
        logger.error("Metrics file not found")
        raise FileNotFoundError("opik_metrics.json not found")

    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    pipeline_metrics = metrics.get("pipeline", {})

    # Analyze health
    total_runs = pipeline_metrics.get("total_runs", 0)
    failed_runs = pipeline_metrics.get("failed_runs", 0)

    failure_rate = failed_runs / total_runs if total_runs > 0 else 0

    if total_runs == 0:
        health_status = "unknown"
        issues = 1
    else:
        if failure_rate < 0.05:
            health_status = "healthy"
            issues = 0
        elif failure_rate < 0.15:
            health_status = "degraded"
            issues = 1
        else:
            health_status = "unhealthy"
            issues = 2

    logger.info(f"Pipeline health status: {health_status}")
    logger.info(f"Issues found: {issues}")

    # Write analysis results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    analysis = {
        "health_status": health_status,
        "issues_count": issues,
        "total_runs": total_runs,
        "failed_runs": failed_runs,
        "failure_rate": failure_rate,
    }

    with open(output_dir / "pipeline_health.json", "w") as f:
        json.dump(analysis, f, indent=2)

    return health_status, issues


if __name__ == "__main__":
    try:
        status, issues = analyze_pipeline_health()
        print(f"✓ Pipeline health: {status} ({issues} issues)")
    except Exception as e:
        logger.error(f"Failed to analyze pipeline health: {e}")
        raise
