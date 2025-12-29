import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("sales_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sales Optimization agent execution harness")
    parser.add_argument("--query", required=True, help="Sales optimization query (e.g., 'Score these leads: [...]')")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "SalesAgent",
        "role": "Sales Operations Specialist",
        "goal": "Accelerate revenue and optimize conversion by scoring leads and identifying funnel bottlenecks"
    }
    
    input_data = {
        "query": args.query
    }

    LOG.info("Executing Sales agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
