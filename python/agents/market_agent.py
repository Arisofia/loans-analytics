import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("market_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market Intelligence agent execution harness")
    parser.add_argument("--query", required=True, help="Market intelligence query (e.g., 'Compare our rates with competitors')")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "MarketAgent",
        "role": "Market Intelligence Specialist",
        "goal": "Analyze competitive landscape, market trends, and economic indicators to inform strategic positioning"
    }
    
    input_data = {
        "query": args.query
    }

    LOG.info("Executing Market agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
