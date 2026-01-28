#!/usr/bin/env python3
"""Compare current costs to baseline and detect regressions.

This script compares cost reports against baseline values and alerts on regressions.
"""

import argparse
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_baselines(baseline_file: str) -> dict:
    """Load baseline costs from YAML or JSON file."""
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


def compare_costs(report_file: str, threshold: float = 0.10) -> bool:
    """Compare costs in report to baseline.

    Args:
        report_file: Path to cost report JSON
        threshold: Alert threshold (default 0.10 = 10%)

    Returns:
        True if all scenarios are within threshold, False otherwise
    """
    # Load current report
    with open(report_file) as f:
        report = json.load(f)

    # Load baselines
    baselines = load_baselines("config/cost_baselines.yml")
    if not baselines:
        baselines = load_baselines("config/cost_baselines.json")

    # If no baselines, treat current as baseline
    if not baselines or "scenarios" not in baselines:
        print("⚠️  No baselines found, current report will be treated as baseline")
        return True

    all_ok = True
    print("\n📊 Cost Regression Analysis:\n")

    for scenario_name, scenario_data in report.get("scenarios", {}).items():
        current_cost = scenario_data.get("total_cost_usd", 0.0)

        baseline_data = baselines.get("scenarios", {}).get(scenario_name, {})
        baseline_cost = baseline_data.get("baseline_cost", 0.0)

        # Convert from string format like "$0.05" to float
        if isinstance(baseline_cost, str):
            baseline_cost = float(baseline_cost.replace("$", ""))

        if baseline_cost == 0:
            print(f"⚠️  {scenario_name}: No baseline found, skipping")
            continue

        # Calculate increase
        increase = (current_cost - baseline_cost) / baseline_cost
        increase_pct = increase * 100

        # Check threshold
        scenario_threshold = baseline_data.get("threshold", threshold)
        alert = increase > scenario_threshold

        status = "🚨 ALERT" if alert else "✅ OK"
        print(f"{status} {scenario_name}:")
        print(f"  Baseline: ${baseline_cost:.4f}")
        print(f"  Current:  ${current_cost:.4f}")
        print(f"  Change:   {increase_pct:+.1f}%")
        print(
            f"  Threshold: {scenario_threshold*100:.1f}%"
        )

        if alert:
            all_ok = False
            print(f"  ⚠️  Cost increased beyond acceptable threshold!")

        # Check token budget
        token_budget = baseline_data.get("token_budget", 0)
        current_tokens = scenario_data.get("total_tokens", 0)
        if token_budget > 0 and current_tokens > token_budget:
            print(
                f"  ⚠️  Token budget exceeded: {current_tokens} > {token_budget}"
            )
            all_ok = False

        # Check API call budget
        api_budget = baseline_data.get("api_calls_budget", 0)
        current_api_calls = scenario_data.get("total_api_calls", 0)
        if api_budget > 0 and current_api_calls > api_budget:
            print(
                f"  ⚠️  API call budget exceeded: {current_api_calls} > {api_budget}"
            )
            all_ok = False

        print()

    return all_ok


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Compare costs to baseline")
    parser.add_argument(
        "report_file",
        help="Cost report JSON file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.10,
        help="Alert threshold (default: 0.10 = 10%%)",
    )
    args = parser.parse_args()

    if not Path(args.report_file).exists():
        print(f"❌ Error: Report file not found: {args.report_file}")
        sys.exit(1)

    all_ok = compare_costs(args.report_file, args.threshold)

    if all_ok:
        print("✅ All scenarios within acceptable cost thresholds")
        sys.exit(0)
    else:
        print("❌ Cost regressions detected!")
        sys.exit(1)


if __name__ == "__main__":
    main()
