import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("ops_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Operations Excellence agent execution harness")
    parser.add_argument("--query", required=True, help="Operations query (e.g., 'What are the current bottlenecks?')")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "OpsAgent",
        "role": "Operations Excellence Specialist",
        "goal": "Optimize operational efficiency, monitor SLAs, and identify process bottlenecks"
    }
    
    input_data = {
        "query": args.query
    }

    LOG.info("Executing Ops agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
