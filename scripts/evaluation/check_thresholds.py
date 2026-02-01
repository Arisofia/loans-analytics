#!/usr/bin/env python3
"""
Evaluation Threshold Checker

Validates ML model evaluation metrics against configured thresholds.
Part of the Model Evaluation Pipeline for fintech compliance.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

# Setup basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_metrics(metrics_file: Path) -> Dict[str, Any]:
    """Load evaluation metrics from JSON report."""
    if not metrics_file.exists():
        logger.error("Metrics file not found", extra={"path": str(metrics_file)})
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")

    with metrics_file.open() as f:
        return json.load(f)


def load_thresholds(config_file: Path) -> Dict[str, Any]:
    """Load threshold configuration from YAML."""
    if not config_file.exists():
        logger.warning(
            "Threshold config not found, using defaults",
            extra={"path": str(config_file)},
        )
        return get_default_thresholds()

    try:
        import yaml

        with config_file.open() as f:
            return yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed, using default thresholds")
        return get_default_thresholds()


def get_default_thresholds() -> Dict[str, Any]:
    """Return default threshold configuration for fintech ML models."""
    return {
        "accuracy": {"min": 0.95, "target": 0.98},
        "precision": {"min": 0.90, "target": 0.95},
        "recall": {"min": 0.85, "target": 0.92},
        "f1_score": {"min": 0.88, "target": 0.93},
        "test_coverage": {"min": 95.0, "target": 98.0},
    }


def check_thresholds(metrics: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate metrics against thresholds.

    Returns:
        Dict with 'passed', 'message', 'failures', and 'warnings' keys
    """
    failures = []
    warnings = []

    # Extract test results if available
    test_summary = metrics.get("summary", {})
    tests_passed = test_summary.get("passed", 0)
    tests_total = test_summary.get("total", 0)

    # Check test pass rate
    if tests_total > 0:
        pass_rate = (tests_passed / tests_total) * 100
        min_coverage = thresholds.get("test_coverage", {}).get("min", 95.0)
        target_coverage = thresholds.get("test_coverage", {}).get("target", 98.0)

        if pass_rate < min_coverage:
            failures.append(f"Test pass rate {pass_rate:.1f}% below minimum {min_coverage}%")
        elif pass_rate < target_coverage:
            warnings.append(f"Test pass rate {pass_rate:.1f}% below target {target_coverage}%")

    # Check for model-specific metrics if present
    model_metrics = metrics.get("model_metrics", {})
    for metric_name, threshold_config in thresholds.items():
        if metric_name == "test_coverage":
            continue

        if metric_name in model_metrics:
            value = model_metrics[metric_name]
            min_val = threshold_config.get("min")
            target_val = threshold_config.get("target")

            if min_val and value < min_val:
                failures.append(f"{metric_name}={value:.3f} below minimum {min_val:.3f}")
            elif target_val and value < target_val:
                warnings.append(f"{metric_name}={value:.3f} below target {target_val:.3f}")

    passed = len(failures) == 0
    message = "All thresholds passed" if passed else f"{len(failures)} threshold(s) failed"

    if warnings:
        message += f" ({len(warnings)} warning(s))"

    result = {
        "passed": passed,
        "message": message,
        "failures": failures,
        "warnings": warnings,
        "tests_total": tests_total,
        "tests_passed": tests_passed,
    }

    logger.info(
        "Threshold check complete",
        extra={
            "passed": passed,
            "failures_count": len(failures),
            "warnings_count": len(warnings),
        },
    )

    return result


def main():
    """Main entry point for threshold checking."""
    parser = argparse.ArgumentParser(description="Check evaluation metrics against thresholds")
    parser.add_argument(
        "--metrics-file",
        type=Path,
        required=True,
        help="Path to evaluation metrics JSON file",
    )
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to threshold configuration YAML",
    )
    parser.add_argument("--output", type=Path, required=True, help="Path to output results JSON")

    args = parser.parse_args()

    try:
        metrics = load_metrics(args.metrics_file)
        thresholds = load_thresholds(args.config)
        results = check_thresholds(metrics, thresholds)

        with args.output.open("w") as f:
            json.dump(results, f, indent=2)

        logger.info("Threshold results written", extra={"path": str(args.output)})

        # Exit with error code if thresholds failed
        sys.exit(0 if results["passed"] else 1)

    except Exception as e:
        logger.exception("Threshold check failed", extra={"error": str(e)})
        # Write error result even on failure
        error_result = {
            "passed": False,
            "message": f"Error: {str(e)}",
            "failures": [str(e)],
            "warnings": [],
            "tests_total": 0,
            "tests_passed": 0,
        }
        try:
            with args.output.open("w") as f:
                json.dump(error_result, f, indent=2)
        except Exception as write_error:
            logger.error(f"Failed to write error result: {write_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
