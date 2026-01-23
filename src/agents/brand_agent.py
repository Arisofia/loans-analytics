import argparse
import json
import logging

from src.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("brand_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Brand & Marketing agent execution harness")
    parser.add_argument(
        "--query", required=True, help="Brand query (e.g., 'What is our current sentiment?')"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    orchestrator = AgentOrchestrator()

    agent_config = {
        "name": "BrandAgent",
        "role": "Brand & Marketing Specialist",
        "goal": "Monitor brand health, sentiment, and marketing campaign effectiveness",
    }

    input_data = {"query": args.query}

    LOG.info("Executing Brand agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
