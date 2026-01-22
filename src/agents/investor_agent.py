import argparse
import json
import logging

from src.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("investor_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Investor Relations agent execution harness")
    parser.add_argument(
        "--query",
        required=True,
        help="Investor relations query (e.g., 'What is the current ROI and valuation?')",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    orchestrator = AgentOrchestrator()

    agent_config = {
        "name": "InvestorAgent",
        "role": "Investor Relations Specialist",
        "goal": "Provide board-level intelligence, ROI analysis, and strategic capital optimization insights",
    }

    input_data = {"query": args.query}

    LOG.info("Executing Investor agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
