import sys

from multi_agent import (
    MultiAgentOrchestrator,
)


class AskGemini:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def ask_agent(self, agent_id, question):
        return self.orchestrator.query_agent(agent_id, question)

    def run_portfolio_review(self, scenario):
        # Execute the full scenario
        # ... implementation of running the portfolio review
        pass


def main():
    if "--scenario" in sys.argv:
        scenario = sys.argv[sys.argv.index("--scenario") + 1]
        orchestrator = MultiAgentOrchestrator()
        review = AskGemini(orchestrator)
        review.run_portfolio_review(scenario)
    else:
        print("Usage: script.py --scenario <scenario_name>")


if __name__ == "__main__":
    main()
