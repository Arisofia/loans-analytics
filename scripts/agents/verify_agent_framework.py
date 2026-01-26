from typing import Any, Dict, List

from src.agents.llm_provider import BaseLLM, LLMResponse
from src.agents.orchestrator import AgentOrchestrator


class ReActMockLLM(BaseLLM):
    """A mock LLM that follows the ReAct pattern for testing."""

    def __init__(self):
        self.step = 0

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> LLMResponse:
        self.step += 1
        if self.step == 1:
            content = """Thought: I need to check the risk by running an SQL query.
Action: run_sql_query
Action Input: {"query": "SELECT * FROM risk_metrics WHERE loan_id = 123"}
"""
        elif self.step == 2:
            content = """Thought: I have the risk metrics. Now I need to simulate a scenario.
Action: simulate_scenario
Action Input: {"params": {"interest_rate": 0.05}}
"""
        else:
            content = """Thought: I have all the information needed.
Final Answer: The risk level for loan 123 is low based on the SQL query and scenario simulation.
"""
        return LLMResponse(content=content)


def test_agent_react_flow():
    print("Testing Agent ReAct Flow...")
    orchestrator = AgentOrchestrator()
    # Override with ReActMockLLM for testing
    orchestrator.llm = ReActMockLLM()

    input_data = {"query": "What is the risk for loan 123?"}
    agent_config = {
        "name": "RiskAgent",
        "role": "Risk Analyst",
        "goal": "Analyze risk for specific loans",
    }

    result = orchestrator.run(input_data, agent_config)
    print(f"Final Output: {result['output']}")
    assert "The risk level for loan 123 is low" in result["output"]
    print("Test passed!")


if __name__ == "__main__":
    test_agent_react_flow()
