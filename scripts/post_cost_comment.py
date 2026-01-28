#!/usr/bin/env python3
"""Post cost analysis comment to GitHub PR.

This script posts a formatted cost analysis comment to a GitHub PR.
"""

import argparse
import json
import sys
from pathlib import Path


def format_cost_comment(report_file: str) -> str:
    """Format cost report as GitHub comment.

    Args:
        report_file: Path to cost report JSON

    Returns:
        Formatted markdown comment
    """
    with open(report_file) as f:
        report = json.load(f)

    comment = "## 💰 Cost Analysis Report\n\n"
    comment += f"**Generated:** {report.get('timestamp', 'N/A')}\n\n"

    scenarios = report.get("scenarios", {})
    if not scenarios:
        comment += "No scenarios found in report.\n"
        return comment

    comment += "### Scenario Costs\n\n"
    comment += "| Scenario | Total Cost | Tokens | API Calls | Agents |\n"
    comment += "|----------|------------|--------|-----------|--------|\n"

    total_cost = 0.0
    total_tokens = 0
    total_api_calls = 0

    for scenario_name, scenario_data in scenarios.items():
        cost = scenario_data.get("total_cost_usd", 0.0)
        tokens = scenario_data.get("total_tokens", 0)
        api_calls = scenario_data.get("total_api_calls", 0)
        agents = scenario_data.get("agent_count", 0)

        total_cost += cost
        total_tokens += tokens
        total_api_calls += api_calls

        comment += f"| {scenario_name} | ${cost:.4f} | {tokens} | {api_calls} | {agents} |\n"

    comment += f"| **TOTAL** | **${total_cost:.4f}** | **{total_tokens}** | **{total_api_calls}** | - |\n\n"

    # Add agent breakdown for first scenario
    if scenarios:
        first_scenario = list(scenarios.values())[0]
        if first_scenario.get("agents"):
            comment += "### Agent Breakdown (Sample)\n\n"
            comment += "| Agent | Cost | Tokens | API Calls |\n"
            comment += "|-------|------|--------|--------|\n"
            for agent in first_scenario["agents"]:
                comment += (
                    f"| {agent['name']} | ${agent['cost_usd']:.4f} | "
                    f"{agent['tokens']} | {agent['api_calls']} |\n"
                )
            comment += "\n"

    comment += "---\n"
    comment += "*Cost estimates based on OpenAI GPT-4o-mini pricing*\n"

    return comment


def post_to_github(comment: str) -> None:
    """Post comment to GitHub PR using environment variables.

    Args:
        comment: Comment text to post
    """
    # This would use GitHub API to post comment
    # For now, just print to stdout for GitHub Actions to capture
    print(comment)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Post cost analysis to GitHub PR")
    parser.add_argument(
        "report_file",
        help="Cost report JSON file",
    )
    args = parser.parse_args()

    if not Path(args.report_file).exists():
        print(f"❌ Error: Report file not found: {args.report_file}")
        sys.exit(1)

    comment = format_cost_comment(args.report_file)
    post_to_github(comment)


if __name__ == "__main__":
    main()
