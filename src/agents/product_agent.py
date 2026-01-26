import argparse
import json
import logging

from src.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("product_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Product Intelligence agent execution harness")
    parser.add_argument(
        "--query", required=True, help="Product query (e.g., 'Prioritize these features: [...]')"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    orchestrator = AgentOrchestrator()

    agent_config = {
        "name": "ProductAgent",
        "role": "Product Intelligence Specialist",
        "goal": "Optimize product development through feature analysis, user feedback synthesis, and roadmap prioritization",
    }

    input_data = {"query": args.query}

    LOG.info("Executing Product agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
