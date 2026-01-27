class BaseAgent:
    def __init__(self):
        pass

    def run(self):
        raise NotImplementedError("Subclasses should implement this!")


class RiskAnalystAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = "Analyze loan portfolio risks, focusing on default probabilities and economic implications."

    def run(self):
        # Implementation details for analyzing loan risks
        print(self.prompt)


class GrowthStrategistAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = "Identify growth opportunities for the loan portfolio by analyzing market trends."

    def run(self):
        # Implementation details for growth strategies
        print(self.prompt)


class OpsOptimizerAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = "Optimize the operational efficiency of the loan processing pipeline."

    def run(self):
        # Implementation details for operational optimization
        print(self.prompt)


class ComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.prompt = "Ensure compliance with financial regulations and standards in the loan portfolio."

    def run(self):
        # Implementation details for compliance checks
        print(self.prompt)
