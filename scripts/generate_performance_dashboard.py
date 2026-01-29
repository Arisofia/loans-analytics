#!/usr/bin/env python3
"""Generate performance dashboard from metrics.

Creates a visual dashboard showing latency trends, success rates, and performance metrics.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.path_utils import validate_path


def generate_ascii_chart(data: list, max_width: int = 50) -> str:
    """Generate a simple ASCII bar chart.

    Args:
        data: List of values
        max_width: Maximum width of bars

    Returns:
        ASCII chart as string
    """
    if not data:
        return "No data"

    max_val = max(data)
    if max_val == 0:
        return "All values are 0"

    chart = []
    for i, val in enumerate(data):
        bar_width = int((val / max_val) * max_width)
        bar = "█" * bar_width
        chart.append(f"{i:3d} | {bar} {val:.2f}")

    return "\n".join(chart)


def generate_dashboard(metrics_file: str) -> str:
    """Generate dashboard from metrics file.

    Args:
        metrics_file: Path to metrics JSON file

    Returns:
        Dashboard content as string
    """
    # Validate metrics file path (CWE-22: Path Traversal)
    validated_metrics = validate_path(metrics_file, base_dir=".", must_exist=True)

    with open(validated_metrics) as f:  # snyk:skip=8b4beff2-bd1e-4d50-8618-c2b5cf9f5f3c
        metrics = json.load(f)

    dashboard = []
    dashboard.append("=" * 70)
    dashboard.append("  🚀 MULTI-AGENT SYSTEM PERFORMANCE DASHBOARD")
    dashboard.append("=" * 70)
    dashboard.append("")

    timestamp = metrics.get("timestamp", "N/A")
    dashboard.append(f"📅 Generated: {timestamp}")
    dashboard.append(f"📊 Total Operations: {metrics.get('total_operations', 0)}")
    dashboard.append("")

    # Scenario metrics
    scenarios = metrics.get("scenarios", {})
    if scenarios:
        dashboard.append("=" * 70)
        dashboard.append("  SCENARIO PERFORMANCE")
        dashboard.append("=" * 70)
        dashboard.append("")

        for scenario_name, scenario_data in scenarios.items():
            dashboard.append(f"📦 {scenario_name.upper()}")
            dashboard.append("-" * 70)

            total = scenario_data.get("total_executions", 0)
            success_rate = scenario_data.get("success_rate", 0)
            dashboard.append(f"  Executions: {total}")
            dashboard.append(f"  Success Rate: {success_rate:.1f}%")

            latency = scenario_data.get("latency", {})
            if latency:
                dashboard.append("  Latency:")
                dashboard.append(f"    p50: {latency.get('p50', 0):.2f}ms")
                dashboard.append(f"    p95: {latency.get('p95', 0):.2f}ms")
                dashboard.append(f"    p99: {latency.get('p99', 0):.2f}ms")
                dashboard.append(f"    avg: {latency.get('avg', 0):.2f}ms")
                dashboard.append(f"    min: {latency.get('min', 0):.2f}ms")
                dashboard.append(f"    max: {latency.get('max', 0):.2f}ms")

            # Alert if p99 exceeds threshold
            p99 = latency.get("p99", 0)
            if p99 > 200:
                dashboard.append(
                    f"  ⚠️  WARNING: p99 latency ({p99:.2f}ms) exceeds 200ms threshold!"
                )

            dashboard.append("")

    # Agent metrics
    agents = metrics.get("agents", {})
    if agents:
        dashboard.append("=" * 70)
        dashboard.append("  AGENT PERFORMANCE")
        dashboard.append("=" * 70)
        dashboard.append("")

        for agent_name, agent_data in agents.items():
            dashboard.append(f"🤖 {agent_name}")
            dashboard.append("-" * 70)

            total = agent_data.get("total_executions", 0)
            success_rate = agent_data.get("success_rate", 0)
            dashboard.append(f"  Executions: {total}")
            dashboard.append(f"  Success Rate: {success_rate:.1f}%")

            latency = agent_data.get("latency", {})
            if latency:
                dashboard.append(f"  Average Latency: {latency.get('avg', 0):.2f}ms")
                dashboard.append(f"  p99 Latency: {latency.get('p99', 0):.2f}ms")

            dashboard.append("")

    # Summary
    dashboard.append("=" * 70)
    dashboard.append("  SUMMARY")
    dashboard.append("=" * 70)
    dashboard.append("")

    # Calculate overall health
    if scenarios:
        avg_success_rate = sum(s.get("success_rate", 0) for s in scenarios.values()) / len(
            scenarios
        )
        avg_p99 = sum(s.get("latency", {}).get("p99", 0) for s in scenarios.values()) / len(
            scenarios
        )

        dashboard.append(f"✅ Average Success Rate: {avg_success_rate:.1f}%")
        dashboard.append(f"⚡ Average p99 Latency: {avg_p99:.2f}ms")
        dashboard.append("")

        if avg_success_rate >= 95 and avg_p99 < 200:
            dashboard.append("🎉 System Health: EXCELLENT")
        elif avg_success_rate >= 90 and avg_p99 < 300:
            dashboard.append("✅ System Health: GOOD")
        elif avg_success_rate >= 80 and avg_p99 < 500:
            dashboard.append("⚠️  System Health: FAIR")
        else:
            dashboard.append("❌ System Health: NEEDS ATTENTION")

    dashboard.append("")
    dashboard.append("=" * 70)

    return "\n".join(dashboard)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate performance dashboard")
    parser.add_argument(
        "--metrics",
        default="metrics/performance_metrics.json",
        help="Path to metrics JSON file",
    )
    parser.add_argument(
        "--output",
        help="Output file (default: print to stdout)",
    )
    args = parser.parse_args()

    dashboard = generate_dashboard(args.metrics)

    if args.output:
        # Validate output path for security (CWE-22: Path Traversal)
        validated_output = validate_path(args.output, base_dir=".", allow_write=True)
        Path(str(validated_output)).parent.mkdir(
            parents=True, exist_ok=True
        )  # snyk:skip=c419c097-e875-44f2-be0c-a3261cf30e67
        with open(
            str(validated_output), "w"
        ) as f:  # snyk:skip=5ba0cf06-1091-4e03-ac31-083151018469
            f.write(dashboard)
        print(f"✅ Dashboard saved to {validated_output}")
    else:
        print(dashboard)


if __name__ == "__main__":
    main()
