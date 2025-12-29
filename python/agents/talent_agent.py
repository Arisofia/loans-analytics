import argparse
import json
import logging

from python.agents.orchestrator import AgentOrchestrator

LOG = logging.getLogger("talent_agent")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="HR & Talent agent execution harness")
    parser.add_argument("--query", required=True, help="Talent query (e.g., 'Assess retention risk for Sales department')")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    orchestrator = AgentOrchestrator()
    
    agent_config = {
        "name": "TalentAgent",
        "role": "People Analytics Specialist",
        "goal": "Optimize organizational health through people analytics, performance prediction, and retention risk scoring"
    }
    
    input_data = {
        "query": args.query
    }

    LOG.info("Executing Talent agent with query: %s", args.query)
    result = orchestrator.run(input_data, agent_config)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
