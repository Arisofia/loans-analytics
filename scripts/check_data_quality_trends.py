#!/usr/bin/env python3
"""
Check data quality trends script.

This script checks data quality trends based on Opik metrics.
"""

import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_data_quality_trends():
    """Check data quality trends from metrics."""
    metrics_file = Path("outputs/opik_metrics.json")
    
    if not metrics_file.exists():
        logger.error("Metrics file not found")
        raise FileNotFoundError("opik_metrics.json not found")
    
    with open(metrics_file, "r") as f:
        metrics = json.load(f)
    
    quality_metrics = metrics.get("data_quality", {})
    
    # Analyze trends
    completeness = quality_metrics.get("completeness_score", 0)
    validity = quality_metrics.get("validity_score", 0)
    anomalies = quality_metrics.get("anomalies_detected", 0)
    
    # Determine trend
    avg_quality = (completeness + validity) / 2
    
    if avg_quality > 0.95 and anomalies < 5:
        trend = "stable"
        anomalies_detected = "false"
    elif avg_quality > 0.85 and anomalies < 10:
        trend = "declining"
        anomalies_detected = "false"
    else:
        trend = "critical"
        anomalies_detected = "true"
    
    logger.info(f"Data quality trend: {trend}")
    logger.info(f"Anomalies detected: {anomalies_detected}")
    
    # Write analysis results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    analysis = {
        "trend": trend,
        "anomalies_detected": anomalies_detected,
        "completeness_score": completeness,
        "validity_score": validity,
        "anomaly_count": anomalies
    }
    
    with open(output_dir / "data_quality_trends.json", "w") as f:
        json.dump(analysis, f, indent=2)
    
    return trend, anomalies_detected


if __name__ == "__main__":
    try:
        trend, anomalies = check_data_quality_trends()
        print(f"✓ Data quality trend: {trend} (anomalies: {anomalies})")
    except Exception as e:
        logger.error(f"Failed to check data quality trends: {e}")
        raise
