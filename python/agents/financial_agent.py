import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("financial_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Financial agent execution harness")
    parser.add_argument("--query", required=True, help="Financial analysis query (e.g., 'What happens if interest rates rise by 1%?')")
    parser.add_argument("--data-path", help="Path to loan data CSV")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "FinancialAgent",
        "role": "Financial Planning & Analysis Specialist",
        "goal": "Perform financial simulations and portfolio yield optimizations"
    }
    
    input_data = {
        "query": args.query,
        "data_path": args.data_path
    }

    LOG.info("Executing Financial agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
