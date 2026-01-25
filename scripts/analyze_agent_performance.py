#!/usr/bin/env python3
"""
Analyze agent performance metrics script.

This script analyzes agent execution performance based on Opik metrics.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analyze_agent_performance():
    """Analyze agent performance from metrics."""
    metrics_file = Path("outputs/opik_metrics.json")
    
    if not metrics_file.exists():
        logger.error("Metrics file not found")
        raise FileNotFoundError("opik_metrics.json not found")
    
    with open(metrics_file, "r") as f:
        metrics = json.load(f)
    
    agent_metrics = metrics.get("agents", {})
    
    # Analyze performance
    avg_response_time = agent_metrics.get("average_response_time_ms", 0)
    error_rate = agent_metrics.get("error_rate", 0)
    
    # Determine status
    if avg_response_time < 1000 and error_rate < 0.05:
        status = "optimal"
        slow_agents = "none"
    elif avg_response_time < 2000 and error_rate < 0.10:
        status = "acceptable"
        slow_agents = "some"
    else:
        status = "degraded"
        slow_agents = "multiple"
    
    logger.info(f"Agent performance status: {status}")
    logger.info(f"Slow agents: {slow_agents}")
    
    # Write analysis results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    analysis = {
        "status": status,
        "slow_agents": slow_agents,
        "average_response_time_ms": avg_response_time,
        "error_rate": error_rate
    }
    
    with open(output_dir / "agent_performance.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    return status, slow_agents


if __name__ == "__main__":
    try:
        status, slow_agents = analyze_agent_performance()
        print(f"✓ Agent performance: {status} (slow agents: {slow_agents})")
    except Exception as e:
        logger.error(f"Failed to analyze agent performance: {e}")
        raise
