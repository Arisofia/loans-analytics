#!/usr/bin/env python3
"""Post performance analysis comment to GitHub PR."""

import argparse
import json

from scripts.path_utils import validate_path


def format_performance_comment(metrics_file: str) -> str:
    """Format performance metrics as GitHub comment.

    Args:
        metrics_file: Path to metrics JSON file

    Returns:
        Formatted markdown comment
    """
    # Validate metrics file path (CWE-22: Path Traversal)
    validated_metrics = validate_path(metrics_file, base_dir=".", must_exist=True)

    with open(validated_metrics) as f:  # snyk:skip=f40d7b06-c546-44db-ad45-074644040df8
        metrics = json.load(f)

    comment = "## ⚡ Performance Analysis Report\n\n"
    comment += f"**Generated:** {metrics.get('timestamp', 'N/A')}\n\n"

    scenarios = metrics.get("scenarios", {})
    if not scenarios:
        comment += "No scenarios found in metrics.\n"
        return comment

    comment += "### Scenario Performance\n\n"
    comment += "| Scenario | Executions | Success Rate | p50 | p95 | p99 | Status |\n"
    comment += "|----------|------------|--------------|-----|-----|-----|--------|\n"

    for scenario_name, scenario_data in scenarios.items():
        total = scenario_data.get("total_executions", 0)
        success_rate = scenario_data.get("success_rate", 0)
        latency = scenario_data.get("latency", {})

        p50 = latency.get("p50", 0)
        p95 = latency.get("p95", 0)
        p99 = latency.get("p99", 0)

        # Determine status
        if p99 < 200 and success_rate >= 95:
            status = "✅"
        elif p99 < 300 and success_rate >= 90:
            status = "⚠️"
        else:
            status = "❌"

        comment += (
            f"| {scenario_name} | {total} | {success_rate:.1f}% | "
            f"{p50:.1f}ms | {p95:.1f}ms | {p99:.1f}ms | {status} |\n"
        )

    comment += "\n### Performance Targets\n\n"
    comment += "- ✅ **Good**: p99 < 200ms, Success Rate ≥ 95%\n"
    comment += "- ⚠️ **Acceptable**: p99 < 300ms, Success Rate ≥ 90%\n"
    comment += "- ❌ **Needs Attention**: p99 ≥ 300ms or Success Rate < 90%\n\n"

    # Agent performance
    agents = metrics.get("agents", {})
    if agents:
        comment += "### Agent Performance\n\n"
        comment += "| Agent | Executions | Success Rate | Avg Latency | p99 Latency |\n"
        comment += "|-------|------------|--------------|-------------|-------------|\n"

        for agent_name, agent_data in agents.items():
            total = agent_data.get("total_executions", 0)
            success_rate = agent_data.get("success_rate", 0)
            latency = agent_data.get("latency", {})

            avg = latency.get("avg", 0)
            p99 = latency.get("p99", 0)

            comment += (
                f"| {agent_name} | {total} | {success_rate:.1f}% | "
                f"{avg:.1f}ms | {p99:.1f}ms |\n"
            )

    comment += "\n---\n"
    comment += "*Performance metrics collected from automated benchmarks*\n"

    return comment


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Post performance analysis to GitHub PR")
    parser.add_argument(
        "metrics_file",
        help="Performance metrics JSON file",
    )
    args = parser.parse_args()

    comment = format_performance_comment(args.metrics_file)
    print(comment)


if __name__ == "__main__":
    main()
