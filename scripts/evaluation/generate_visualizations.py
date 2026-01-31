#!/usr/bin/env python3
"""
Evaluation Metrics Visualization Generator

Creates charts and visualizations from ML model evaluation metrics.
Part of the Model Evaluation Pipeline for fintech compliance.
"""

import argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_metrics(metrics_file: Path) -> Dict[str, Any]:
    """Load evaluation metrics from JSON report."""
    if not metrics_file.exists():
        logger.error("Metrics file not found", extra={"path": str(metrics_file)})
        raise FileNotFoundError(f"Metrics file not found: {metrics_file}")

    with metrics_file.open() as f:
        return json.load(f)


def generate_test_summary_chart(metrics: Dict[str, Any], output_dir: Path):
    """Generate test pass/fail summary chart."""
    try:
        import matplotlib  # pylint: disable=import-outside-toplevel
        import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel

        matplotlib.use("Agg")  # Non-interactive backend for CI

        summary = metrics.get("summary", {})
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)

        _, ax = plt.subplots(figsize=(8, 6))
        categories = ["Passed", "Failed", "Skipped"]
        values = [passed, failed, skipped]
        colors = ["#28a745", "#dc3545", "#ffc107"]

        ax.bar(categories, values, color=colors)
        ax.set_ylabel("Count")
        ax.set_title("Test Execution Summary")
        ax.grid(axis="y", alpha=0.3)

        output_file = output_dir / "test_summary.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info("Generated test summary chart", extra={"path": str(output_file)})

    except ImportError:
        logger.warning("matplotlib not installed, skipping chart generation")
    except Exception as e:
        logger.error("Failed to generate test summary chart", extra={"error": str(e)})


def generate_duration_chart(metrics: Dict[str, Any], output_dir: Path):
    """Generate test duration distribution chart."""
    try:
        import matplotlib  # pylint: disable=import-outside-toplevel
        import matplotlib.pyplot as plt  # pylint: disable=import-outside-toplevel

        matplotlib.use("Agg")

        tests = metrics.get("tests", [])
        if not tests:
            logger.warning("No test data available for duration chart")
            return

        durations = [test.get("call", {}).get("duration", 0) for test in tests]
        test_names = [test.get("nodeid", "").split("::")[-1][:30] for test in tests]

        # Only plot top 20 slowest tests
        sorted_data = sorted(zip(durations, test_names), reverse=True)[:20]
        durations, test_names = zip(*sorted_data) if sorted_data else ([], [])

        _, ax = plt.subplots(figsize=(10, 8))
        ax.barh(range(len(test_names)), durations)
        ax.set_yticks(range(len(test_names)))
        ax.set_yticklabels(test_names, fontsize=8)
        ax.set_xlabel("Duration (seconds)")
        ax.set_title("Top 20 Slowest Tests")
        ax.grid(axis="x", alpha=0.3)

        output_file = output_dir / "test_durations.png"
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        plt.close()

        logger.info("Generated duration chart", extra={"path": str(output_file)})

    except ImportError:
        logger.warning("matplotlib not installed, skipping chart generation")
    except Exception as e:
        logger.error("Failed to generate duration chart", extra={"error": str(e)})


def generate_coverage_report(metrics: Dict[str, Any], output_dir: Path):
    """Generate coverage report (placeholder for future implementation)."""
    logger.info("Coverage report generation not yet implemented")


def main():
    """Main entry point for visualization generation."""
    parser = argparse.ArgumentParser(
        description="Generate visualizations from evaluation metrics"
    )
    parser.add_argument(
        "--metrics-file",
        type=Path,
        required=True,
        help="Path to evaluation metrics JSON file",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for output visualizations",
    )

    args = parser.parse_args()

    try:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        metrics = load_metrics(args.metrics_file)

        logger.info(
            "Generating visualizations",
            extra={
                "metrics_file": str(args.metrics_file),
                "output_dir": str(args.output_dir),
            },
        )

        generate_test_summary_chart(metrics, args.output_dir)
        generate_duration_chart(metrics, args.output_dir)
        generate_coverage_report(metrics, args.output_dir)

        logger.info("Visualization generation complete")

    except Exception as e:
        logger.exception("Visualization generation failed", extra={"error": str(e)})
        raise


if __name__ == "__main__":
    main()
