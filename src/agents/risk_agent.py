import argparse
import json
import logging

from src.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("risk_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Risk agent execution harness")
    parser.add_argument(
        "--query",
        required=True,
        help="Risk analysis query (e.g., 'What is the current portfolio risk?')",
    )
    parser.add_argument("--data-path", help="Path to loan data CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    orchestrator = AgentOrchestrator()

    agent_config = {
        "name": "RiskAgent",
        "role": "Risk Analyst Specialist",
        "goal": "Identify and analyze financial and credit risks within the loan portfolio",
    }

    input_data = {"query": args.query, "data_path": args.data_path}

    LOG.info("Executing Risk agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
