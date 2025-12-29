import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("customer_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Customer Intelligence agent execution harness")
    parser.add_argument("--query", required=True, help="Customer intelligence query (e.g., 'What is the churn risk for customer CUST-001?')")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "CustomerAgent",
        "role": "Customer Intelligence Specialist",
        "goal": "Deep customer profiling and behavioral prediction to optimize retention and growth"
    }
    
    input_data = {
        "query": args.query
    }

    LOG.info("Executing Customer agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
