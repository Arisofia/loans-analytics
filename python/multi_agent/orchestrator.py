from .agents import (
    RiskAnalystAgent,
    ComplianceAgent,
    GrowthStrategistAgent,
    OpsOptimizerAgent
)


class MultiAgentOrchestrator:
    def __init__(self):
        self.agents = self._init_agents()

    def _init_agents(self):
        # Initialize agents here
        agents = {
            'RiskAnalyst': RiskAnalystAgent(),
            'Compliance': ComplianceAgent(),
            'GrowthStrategist': GrowthStrategistAgent(),
            'OpsOptimizer': OpsOptimizerAgent()
        }
        return agents

    def run_scenario(self, scenario_steps):
        results = []
        for step in scenario_steps:
            agent_name, data = step
            agent = self.agents[agent_name]
            result = agent.execute(data)
            results.append(result)
        return results

    def query_agent(self, agent_name, query):
        agent = self.agents.get(agent_name)
        if agent:
            return agent.query(query)
        return None

    def create_portfolio_risk_review_scenario(self):
        scenario = [
            ('RiskAnalyst', {'portfolio_data': 'data1'}),
            ('Compliance', {'risk_assessment': 'data2'}),
            ('GrowthStrategist', {'market_analysis': 'data3'}),
            ('OpsOptimizer', {'optimization_data': 'data4'})
        ]
        return self.run_scenario(scenario)
