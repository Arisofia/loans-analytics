from typing import Any, Dict, List

from src.agents.llm_provider import BaseLLM, LLMResponse
from src.agents.orchestrator import AgentOrchestrator


class Sprint3MockLLM(BaseLLM):
    """A mock LLM that follows the ReAct pattern for Sprint 3 agents."""

    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.step = 0

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> LLMResponse:
        self.step += 1
        if self.agent_type == "risk":
            if self.step == 1:
                content = """Thought: I need to run a full portfolio analysis to identify risks.
Action: run_portfolio_analysis
Action Input: {}
"""
            else:
                content = """Thought: I have the analysis.
Final Answer: The portfolio has a delinquency rate of 25% in this sample, with 2 high-risk loans identified.
"""
        elif self.agent_type == "financial":
            if self.step == 1:
                content = """Thought: I need to simulate a 1% interest rate increase.
Action: simulate_portfolio_scenario
Action Input: {"rate_adjustment": 0.01}
"""
            else:
                content = """Thought: I have the simulation results.
Final Answer: A 1% rate increase would improve portfolio yield from 3.99% to 4.99%.
"""
        else:
            content = "Final Answer: Done."

        return LLMResponse(content=content)


def test_risk_agent():
    print("Testing Risk Agent...")
    orchestrator = AgentOrchestrator()
    orchestrator.llm = Sprint3MockLLM("risk")

    input_data = {"query": "What is the current portfolio risk?"}
    agent_config = {"name": "RiskAgent", "role": "Risk Analyst", "goal": "Analyze portfolio risk"}

    result = orchestrator.run(input_data, agent_config)
    print(f"Risk Agent Output: {result['output']}")
    assert "25%" in result["output"]
    print("Risk Agent test passed!")


def test_financial_agent():
    print("\nTesting Financial Agent...")
    orchestrator = AgentOrchestrator()
    orchestrator.llm = Sprint3MockLLM("financial")

    input_data = {"query": "What happens if interest rates rise by 1%?"}
    agent_config = {
        "name": "FinancialAgent",
        "role": "Financial Analyst",
        "goal": "Simulate financial scenarios",
    }

    result = orchestrator.run(input_data, agent_config)
    print(f"Financial Agent Output: {result['output']}")
    assert "4.99%" in result["output"]
    print("Financial Agent test passed!")


if __name__ == "__main__":
    test_risk_agent()
    test_financial_agent()
