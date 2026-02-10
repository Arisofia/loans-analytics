#!/usr/bin/env python3
"""
Multi-Agent System CLI

Command-line interface for orchestrator operations.

Usage:
    python -m python.multi_agent.cli list-scenarios
    python -m python.multi_agent.cli run-scenario loan_risk_review --context \
        '{"loan_id": "123"}'
    python -m python.multi_agent.cli run-agent risk_analyst --input \
        "Analyze portfolio risk"
"""

import argparse
import json
import sys
from typing import Any, Dict

from .orchestrator import MultiAgentOrchestrator
from .protocol import AgentRole, Message, MessageRole


def list_scenarios() -> None:
    """List all available scenarios."""
    orchestrator = MultiAgentOrchestrator()
    scenario_names = orchestrator.list_scenarios()

    print("\n📋 Available Scenarios:\n")
    for name in scenario_names:
        scenario = orchestrator.get_scenario(name)
        if scenario:
            print(f"  • {name}")
            print(f"    Steps: {len(scenario.steps)}")
            print(f"    Description: {scenario.description}\n")


def run_scenario(scenario_name: str, context: Dict[str, Any]) -> None:
    """Execute a scenario with given context."""
    orchestrator = MultiAgentOrchestrator()

    scenario = orchestrator.get_scenario(scenario_name)
    if not scenario:
        print(f"❌ Error: Scenario '{scenario_name}' not found")
        sys.exit(1)

    print(f"\n🚀 Running Scenario: {scenario_name}")
    print(f"📊 Steps: {len(scenario.steps)}\n")

    try:
        results = orchestrator.run_scenario(scenario_name, context)

        print("✅ Scenario completed successfully\n")
        print("📤 Results:")
        print(json.dumps(results, indent=2))

    except (ValueError, RuntimeError, KeyError) as e:
        print(f"❌ Scenario failed: {e}")
        sys.exit(1)


def run_agent(
    agent_role_str: str,
    user_input: str,
    context: Dict[str, Any] | None = None,
) -> None:
    """Run a single agent with given input."""
    try:
        agent_role = AgentRole(agent_role_str)
    except ValueError:
        print(f"❌ Error: Invalid agent role '{agent_role_str}'")
        print(f"Valid roles: {', '.join([r.value for r in AgentRole])}")
        sys.exit(1)

    orchestrator = MultiAgentOrchestrator()
    trace_id = orchestrator.tracer.generate_trace_id()

    print(f"\n🤖 Running Agent: {agent_role.value}")
    print(f"🔍 Trace ID: {trace_id}\n")

    try:
        messages = [Message(role=MessageRole.USER, content=user_input)]
        response = orchestrator.run_agent(
            role=agent_role,
            messages=messages,
            trace_id=trace_id,
            context=context or {},
        )

        print("✅ Agent response received\n")
        print("📤 Response:")
        print(f"  Content: {response.message.content}")
        print(f"  Tokens: {response.tokens_used}")
        print(f"  Cost: ${response.cost_usd:.6f}")
        print(f"  Latency: {response.latency_ms:.2f}ms")

    except (ValueError, RuntimeError, ConnectionError) as e:
        print(f"❌ Agent failed: {e}")
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  List all scenarios:
    python -m python.multi_agent.cli list-scenarios

  Run a scenario:
    python -m python.multi_agent.cli run-scenario loan_risk_review \\
        --context '{"loan_id": "123", "amount": 50000}'

  Run a single agent:
    python -m python.multi_agent.cli run-agent risk_analyst \\
        --input "Analyze loan portfolio for high-risk indicators"
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-scenarios command
    subparsers.add_parser("list-scenarios", help="List all available scenarios")

    # run-scenario command
    scenario_parser = subparsers.add_parser("run-scenario", help="Execute a scenario")
    scenario_parser.add_argument("scenario_name", help="Name of the scenario to run")
    scenario_parser.add_argument(
        "--context",
        type=str,
        default="{}",
        help="JSON context for the scenario (default: {})",
    )

    # run-agent command
    agent_parser = subparsers.add_parser("run-agent", help="Run a single agent")
    agent_parser.add_argument(
        "agent_role",
        choices=[r.value for r in AgentRole],
        help="Agent role to invoke",
    )
    agent_parser.add_argument("--input", required=True, help="Input text for the agent")
    agent_parser.add_argument(
        "--context",
        type=str,
        default="{}",
        help="JSON context for the agent (default: {})",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "list-scenarios":
        list_scenarios()

    elif args.command == "run-scenario":
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON context: {e}")
            sys.exit(1)
        run_scenario(args.scenario_name, context)

    elif args.command == "run-agent":
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON context: {e}")
            sys.exit(1)
        run_agent(args.agent_role, args.input, context)


if __name__ == "__main__":
    main()
