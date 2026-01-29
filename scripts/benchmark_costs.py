#!/usr/bin/env python3
"""Benchmark costs for multi-agent scenarios.

This script runs test scenarios and collects cost data for baseline comparison.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.monitoring import CostTracker


def run_loan_analysis_scenario(tracker: CostTracker) -> None:
    """Run loan analysis scenario benchmark."""
    tracker.start_scenario("loan_analysis")

    # Simulate analytics agent
    tracker.track_agent_execution(
        agent_name="analytics_agent",
        tokens_input=300,
        tokens_output=200,
        execution_time_ms=150,
    )

    # Simulate risk agent
    tracker.track_agent_execution(
        agent_name="risk_agent",
        tokens_input=200,
        tokens_output=100,
        execution_time_ms=100,
    )

    # Simulate API calls
    tracker.track_api_call("analytics_agent", "supabase", "/loans", 0.001)
    tracker.track_api_call("risk_agent", "supabase", "/risk_scores", 0.001)
    tracker.track_api_call("analytics_agent", "n8n", "/webhook", 0.001)


def run_risk_assessment_scenario(tracker: CostTracker) -> None:
    """Run risk assessment scenario benchmark."""
    tracker.start_scenario("risk_assessment")

    # Simulate risk agent
    tracker.track_agent_execution(
        agent_name="risk_agent",
        tokens_input=250,
        tokens_output=50,
        execution_time_ms=120,
    )

    # Simulate API calls
    tracker.track_api_call("risk_agent", "supabase", "/portfolio", 0.001)
    tracker.track_api_call("risk_agent", "n8n", "/alerts", 0.001)


def run_portfolio_validation_scenario(tracker: CostTracker) -> None:
    """Run portfolio validation scenario benchmark."""
    tracker.start_scenario("portfolio_validation")

    # Simulate validation agent
    tracker.track_agent_execution(
        agent_name="validation_agent",
        tokens_input=150,
        tokens_output=50,
        execution_time_ms=80,
    )

    # Simulate API call
    tracker.track_api_call("validation_agent", "supabase", "/validate", 0.001)


def main():
    """Run all benchmark scenarios."""
    parser = argparse.ArgumentParser(description="Benchmark agent costs")
    parser.add_argument(
        "--output",
        default="cost_report.json",
        help="Output file for cost report",
    )
    parser.add_argument(
        "--scenarios",
        nargs="+",
        default=["loan_analysis", "risk_assessment", "portfolio_validation"],
        help="Scenarios to benchmark",
    )
    args = parser.parse_args()

    tracker = CostTracker()

    print("Running cost benchmarks...")

    if "loan_analysis" in args.scenarios:
        print("  - loan_analysis scenario")
        run_loan_analysis_scenario(tracker)

    if "risk_assessment" in args.scenarios:
        print("  - risk_assessment scenario")
        run_risk_assessment_scenario(tracker)

    if "portfolio_validation" in args.scenarios:
        print("  - portfolio_validation scenario")
        run_portfolio_validation_scenario(tracker)

    # Save report
    tracker.save_report(args.output)
    print(f"\n✅ Cost report saved to {args.output}")

    # Display summary
    print("\n📊 Cost Summary:")
    for scenario in args.scenarios:
        cost_data = tracker.get_scenario_cost(scenario)
        print(f"\n{scenario}:")
        print(f"  Total Cost: ${cost_data['total_cost_usd']:.4f}")
        print(f"  Total Tokens: {cost_data['total_tokens']}")
        print(f"  API Calls: {cost_data['total_api_calls']}")
        print(f"  Agents: {cost_data['agent_count']}")


if __name__ == "__main__":
    main()
