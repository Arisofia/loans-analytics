#!/usr/bin/env python3
"""Compare performance metrics to baseline.

Detects performance regressions by comparing current metrics to baseline values.
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure repository root is importable when invoked as `python scripts/*.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.baseline_utils import load_baselines
from scripts.path_utils import validate_path


def compare_performance(metrics_file: str, threshold: float = 0.20) -> bool:
    """Compare performance metrics to baseline.

    Args:
        metrics_file: Path to performance metrics JSON
        threshold: Alert threshold (default 0.20 = 20%)

    Returns:
        True if all scenarios meet performance targets, False otherwise
    """
    # Validate metrics file path (CWE-22: Path Traversal)
    validated_metrics = validate_path(metrics_file, base_dir=".", must_exist=True)

    with open(validated_metrics) as f:  # snyk:skip=3abe2bc2-524a-464f-900d-2277378e55cb
        metrics = json.load(f)

    # Load baselines
    baselines = load_baselines("metrics/latency_baseline.yml")
    if not baselines:
        baselines = load_baselines("metrics/latency_baseline.json")

    if not baselines:
        print("⚠️  No baselines found, treating current metrics as baseline")
        return True

    all_ok = True
    print("\n📊 Performance Regression Analysis:\n")

    scenarios = metrics.get("scenarios", {})
    for scenario_name, scenario_data in scenarios.items():
        baseline_data = baselines.get("scenarios", {}).get(scenario_name, {})

        if not baseline_data:
            print(f"⚠️  {scenario_name}: No baseline found, skipping")
            continue

        # Check latency
        current_latency = scenario_data.get("latency", {})
        baseline_latency = baseline_data.get("baseline_p99_ms", 0)

        current_p99 = current_latency.get("p99", 0)

        if baseline_latency > 0:
            increase = (current_p99 - baseline_latency) / baseline_latency
            increase_pct = increase * 100

            alert = increase > threshold
            status = "🚨 ALERT" if alert else "✅ OK"

            print(f"{status} {scenario_name} (p99 latency):")
            print(f"  Baseline: {baseline_latency:.2f}ms")
            print(f"  Current:  {current_p99:.2f}ms")
            print(f"  Change:   {increase_pct:+.1f}%")
            print(f"  Threshold: {threshold*100:.1f}%")

            if alert:
                all_ok = False
                print("  ⚠️  Latency increased beyond acceptable threshold!")

        # Check success rate
        baseline_success_rate = baseline_data.get("baseline_success_rate", 100)
        current_success_rate = scenario_data.get("success_rate", 100)

        # 5% tolerance
        if current_success_rate < baseline_success_rate - 5:
            msg = (
                f"  ⚠️  Success rate dropped: "
                f"{current_success_rate:.1f}% < {baseline_success_rate:.1f}%"
            )
            print(msg)
            all_ok = False

        print()

    return all_ok


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare performance to baseline")
    parser.add_argument(
        "metrics_file",
        help="Performance metrics JSON file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.20,
        help="Alert threshold (default: 0.20 = 20%%)",
    )
    args = parser.parse_args()

    all_ok = compare_performance(args.metrics_file, args.threshold)

    if all_ok:
        print("✅ All scenarios meet performance targets")
        sys.exit(0)
    else:
        print("❌ Performance regressions detected!")
        sys.exit(1)


if __name__ == "__main__":
    main()
