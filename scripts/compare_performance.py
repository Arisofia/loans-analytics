#!/usr/bin/env python3
"""Compare performance metrics to baseline.

Detects performance regressions by comparing current metrics to baseline values.
"""

import argparse
import json
import sys
from pathlib import Path


def load_baseline(baseline_file: str) -> dict:
    """Load baseline metrics from YAML or JSON file."""
    baseline_path = Path(baseline_file)
    if not baseline_path.exists():
        print(f"⚠️  Baseline file not found: {baseline_file}")
        return {}

    with open(baseline_path) as f:
        if baseline_file.endswith(".json"):
            return json.load(f)
        elif baseline_file.endswith((".yml", ".yaml")):
            try:
                import yaml

                return yaml.safe_load(f)
            except ImportError:
                print("⚠️  PyYAML not installed, cannot read YAML baselines")
                return {}
    return {}


def compare_performance(metrics_file: str, threshold: float = 0.20) -> bool:
    """Compare performance metrics to baseline.

    Args:
        metrics_file: Path to performance metrics JSON
        threshold: Alert threshold (default 0.20 = 20%)

    Returns:
        True if all scenarios meet performance targets, False otherwise
    """
    if not Path(metrics_file).exists():
        print(f"❌ Error: Metrics file not found: {metrics_file}")
        return False

    with open(metrics_file) as f:
        metrics = json.load(f)

    # Load baselines
    baselines = load_baseline("metrics/latency_baseline.yml")
    if not baselines:
        baselines = load_baseline("metrics/latency_baseline.json")

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
                print(f"  ⚠️  Latency increased beyond acceptable threshold!")

        # Check success rate
        baseline_success_rate = baseline_data.get("baseline_success_rate", 100)
        current_success_rate = scenario_data.get("success_rate", 100)

        if current_success_rate < baseline_success_rate - 5:  # 5% tolerance
            print(f"  ⚠️  Success rate dropped: {current_success_rate:.1f}% < {baseline_success_rate:.1f}%")
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
