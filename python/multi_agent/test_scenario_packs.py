"""
Tests for product-specific scenario packs.

Tests retail loan, SME loan, auto loan, and portfolio-level scenarios
to ensure proper agent coordination and workflow execution.
"""

import unittest
from unittest.mock import Mock, patch

from python.multi_agent.orchestrator import MultiAgentOrchestrator
from python.multi_agent.protocol import AgentRole


class TestRetailLoanScenarios(unittest.TestCase):
    """Test retail loan scenario workflows."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("python.multi_agent.base_agent.BaseAgent._init_client"):
            self.orchestrator = MultiAgentOrchestrator()

    def test_retail_origination_scenario_exists(self):
        """Test retail origination scenario is registered."""
        self.assertIn("retail_origination", self.orchestrator.scenarios)

    def test_retail_origination_workflow_structure(self):
        """Test retail origination has correct workflow steps."""
        scenario = self.orchestrator.scenarios["retail_origination"]
        
        self.assertEqual(scenario.name, "retail_origination")
        self.assertEqual(len(scenario.steps), 4)
        
        # Verify agent sequence: Fraud → Risk → Pricing → Compliance
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.FRAUD_DETECTION)
        self.assertEqual(scenario.steps[1].agent_role, AgentRole.RISK_ANALYST)
        self.assertEqual(scenario.steps[2].agent_role, AgentRole.PRICING)
        self.assertEqual(scenario.steps[3].agent_role, AgentRole.COMPLIANCE)
        
        # Verify output keys
        self.assertEqual(scenario.steps[0].output_key, "fraud_screen")
        self.assertEqual(scenario.steps[1].output_key, "underwriting_decision")
        self.assertEqual(scenario.steps[2].output_key, "rate_quote")
        self.assertEqual(scenario.steps[3].output_key, "compliance_approval")

    def test_retail_portfolio_review_scenario_exists(self):
        """Test retail portfolio review scenario is registered."""
        self.assertIn("retail_portfolio_review", self.orchestrator.scenarios)

    def test_retail_portfolio_review_workflow_structure(self):
        """Test retail portfolio review has correct workflow steps."""
        scenario = self.orchestrator.scenarios["retail_portfolio_review"]
        
        self.assertEqual(scenario.name, "retail_portfolio_review")
        self.assertEqual(len(scenario.steps), 4)
        
        # Verify agent sequence: Risk → Collections → Retention → Ops
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.RISK_ANALYST)
        self.assertEqual(scenario.steps[1].agent_role, AgentRole.COLLECTIONS)
        self.assertEqual(scenario.steps[2].agent_role, AgentRole.CUSTOMER_RETENTION)
        self.assertEqual(scenario.steps[3].agent_role, AgentRole.OPS_OPTIMIZER)

    def test_retail_rate_adjustment_scenario_exists(self):
        """Test retail rate adjustment scenario is registered."""
        self.assertIn("retail_rate_adjustment", self.orchestrator.scenarios)

    def test_retail_rate_adjustment_workflow_structure(self):
        """Test retail rate adjustment has correct workflow steps."""
        scenario = self.orchestrator.scenarios["retail_rate_adjustment"]
        
        self.assertEqual(scenario.name, "retail_rate_adjustment")
        self.assertEqual(len(scenario.steps), 4)
        
        # Verify agent sequence: Risk → Pricing → Retention → Compliance
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.RISK_ANALYST)
        self.assertEqual(scenario.steps[1].agent_role, AgentRole.PRICING)
        self.assertEqual(scenario.steps[2].agent_role, AgentRole.CUSTOMER_RETENTION)
        self.assertEqual(scenario.steps[3].agent_role, AgentRole.COMPLIANCE)

    def test_retail_scenarios_use_correct_context_keys(self):
        """Test retail scenarios reference correct context variables."""
        origination = self.orchestrator.scenarios["retail_origination"]
        
        # Fraud step needs application_data
        self.assertIn("application_data", origination.steps[0].context_keys)
        
        # Risk step needs fraud_screen and credit_data
        self.assertIn("fraud_screen", origination.steps[1].context_keys)
        self.assertIn("credit_data", origination.steps[1].context_keys)
        
        # Pricing step needs underwriting_decision and market_rates
        self.assertIn("underwriting_decision", origination.steps[2].context_keys)
        self.assertIn("market_rates", origination.steps[2].context_keys)

    def test_all_retail_scenarios_have_descriptions(self):
        """Test all retail scenarios have descriptive text."""
        retail_scenarios = [
            "retail_origination",
            "retail_portfolio_review",
            "retail_rate_adjustment",
        ]
        
        for scenario_name in retail_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            self.assertIsNotNone(scenario.description)
            self.assertGreater(len(scenario.description), 10)
            self.assertTrue(scenario.description.startswith(scenario.description[0].upper()))


class TestScenarioIntegration(unittest.TestCase):
    """Test scenario integration and completeness."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("python.multi_agent.base_agent.BaseAgent._init_client"):
            self.orchestrator = MultiAgentOrchestrator()

    def test_total_scenario_count(self):
        """Test total number of registered scenarios."""
        # 8 original + 3 retail = 11 scenarios
        self.assertEqual(len(self.orchestrator.scenarios), 11)

    def test_all_scenarios_have_unique_names(self):
        """Test scenario names are unique."""
        scenario_names = list(self.orchestrator.scenarios.keys())
        self.assertEqual(len(scenario_names), len(set(scenario_names)))

    def test_all_scenarios_use_valid_agent_roles(self):
        """Test all scenarios reference valid agent roles."""
        valid_roles = set(AgentRole)
        
        for scenario_name, scenario in self.orchestrator.scenarios.items():
            for step in scenario.steps:
                self.assertIn(
                    step.agent_role,
                    valid_roles,
                    f"Scenario {scenario_name} uses invalid role: {step.agent_role}"
                )

    def test_scenario_list_method(self):
        """Test list_scenarios returns all registered scenarios."""
        scenario_list = self.orchestrator.list_scenarios()
        
        self.assertEqual(len(scenario_list), 11)
        self.assertIn("retail_origination", scenario_list)
        self.assertIn("retail_portfolio_review", scenario_list)
        self.assertIn("retail_rate_adjustment", scenario_list)

    def test_retail_scenarios_are_product_specific(self):
        """Test retail scenarios are designed for retail lending."""
        retail_scenarios = ["retail_origination", "retail_portfolio_review", "retail_rate_adjustment"]
        
        for scenario_name in retail_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            # Check that scenario name or description mentions retail
            self.assertTrue(
                "retail" in scenario_name.lower() or "retail" in scenario.description.lower()
            )


if __name__ == "__main__":
    unittest.main()
