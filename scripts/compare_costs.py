#!/usr/bin/env python3
"""Compare current costs to baseline and detect regressions.

This script compares cost reports against baseline values and alerts on regressions.
"""

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.baseline_utils import load_baselines
from scripts.path_utils import validate_path


@dataclass(frozen=True)
class CostComparison:
    scenario_name: str
    baseline_cost: float
    current_cost: float
    increase_pct: float
    scenario_threshold: float
    alert: bool


def _parse_cost_value(value) -> float:
    """Parse cost value from string or float format."""
    if isinstance(value, str):
        return float(value.replace("$", ""))
    return float(value)


def _check_cost_regression(
    current_cost: float, baseline_cost: float, scenario_threshold: float
) -> tuple[bool, float, float]:
    """Check cost regression and return (alert, increase, increase_pct)."""
    increase = (current_cost - baseline_cost) / baseline_cost
    increase_pct = increase * 100
    alert = increase > scenario_threshold
    return alert, increase, increase_pct


def _print_cost_result(result: CostComparison) -> None:
    """Print cost comparison result."""
    status = "🚨 ALERT" if result.alert else "✅ OK"
    print(f"{status} {result.scenario_name}:")
    print(f"  Baseline: ${result.baseline_cost:.4f}")
    print(f"  Current:  ${result.current_cost:.4f}")
    print(f"  Change:   {result.increase_pct:+.1f}%")
    print(f"  Threshold: {result.scenario_threshold*100:.1f}%")
    if result.alert:
        print("  ⚠️  Cost increased beyond acceptable threshold!")


def _check_budget_limits(scenario_data: dict, baseline_data: dict) -> bool:
    """Check token and API call budget limits. Returns True if all limits exceeded."""
    budget_exceeded = False

    token_budget = baseline_data.get("token_budget", 0)
    current_tokens = scenario_data.get("total_tokens", 0)
    if 0 < token_budget < current_tokens:
        print(f"  ⚠️  Token budget exceeded: {current_tokens} > {token_budget}")
        budget_exceeded = True

    api_budget = baseline_data.get("api_calls_budget", 0)
    current_api_calls = scenario_data.get("total_api_calls", 0)
    if 0 < api_budget < current_api_calls:
        print(f"  ⚠️  API call budget exceeded: {current_api_calls} > {api_budget}")
        budget_exceeded = True

    return budget_exceeded


def _process_scenario(
    scenario_name: str, scenario_data: dict, baseline_data: dict, default_threshold: float
) -> bool:
    """Process a single scenario and return whether all checks passed."""
    current_cost = scenario_data.get("total_cost_usd", 0.0)
    baseline_cost = _parse_cost_value(baseline_data.get("baseline_cost", 0.0))

    if baseline_cost == 0:
        print(f"⚠️  {scenario_name}: No baseline found, skipping")
        return True

    scenario_threshold = baseline_data.get("threshold", default_threshold)
    alert, _, increase_pct = _check_cost_regression(current_cost, baseline_cost, scenario_threshold)

    comparison = CostComparison(
        scenario_name=scenario_name,
        baseline_cost=baseline_cost,
        current_cost=current_cost,
        increase_pct=increase_pct,
        scenario_threshold=scenario_threshold,
        alert=alert,
    )
    _print_cost_result(comparison)

    budget_exceeded = _check_budget_limits(scenario_data, baseline_data)
    print()

    return not alert and not budget_exceeded


def compare_costs(report_file: str, threshold: float = 0.10) -> bool:
    """Compare costs in report to baseline.

    Args:
        report_file: Path to cost report JSON
        threshold: Alert threshold (default 0.10 = 10%)

    Returns:
        True if all scenarios are within threshold, False otherwise
    """
    # Load current report with path validation (CWE-22: Path Traversal)
    validated_report = validate_path(report_file, base_dir=".", must_exist=True)
    with open(validated_report) as f:  # snyk:skip=614452fc-363f-41b9-8235-d3c3e51c3825
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
        baseline_data = baselines.get("scenarios", {}).get(scenario_name, {})
        scenario_ok = _process_scenario(scenario_name, scenario_data, baseline_data, threshold)
        all_ok = all_ok and scenario_ok

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
