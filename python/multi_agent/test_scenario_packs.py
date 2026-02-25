"""
Tests for product-specific scenario packs.

Tests retail loan, SME loan, auto loan, and portfolio-level scenarios
to ensure proper agent coordination and workflow execution.
"""

import unittest
from unittest.mock import patch

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
        # 4 original + 4 specialized + 3 retail + 3 SME + 3 Auto + 3 Portfolio + 2 Historical = 22 scenarios
        self.assertEqual(len(self.orchestrator.scenarios), 22)

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
                    f"Scenario {scenario_name} uses invalid role: {step.agent_role}",
                )

    def test_scenario_list_method(self):
        """Test list_scenarios returns all registered scenarios."""
        scenario_list = self.orchestrator.list_scenarios()

        self.assertEqual(len(scenario_list), 22)
        # Check retail scenarios
        self.assertIn("retail_origination", scenario_list)
        self.assertIn("retail_portfolio_review", scenario_list)
        self.assertIn("retail_rate_adjustment", scenario_list)
        # Check SME scenarios
        self.assertIn("sme_underwriting", scenario_list)
        self.assertIn("sme_portfolio_stress_test", scenario_list)
        # Check Auto scenarios
        self.assertIn("auto_origination", scenario_list)
        self.assertIn("auto_delinquency_workout", scenario_list)
        # Check Portfolio scenarios
        self.assertIn("portfolio_health_check", scenario_list)
        self.assertIn("strategic_planning", scenario_list)
        self.assertIn("regulatory_review", scenario_list)
        # Check Historical scenarios
        self.assertIn("trend_based_planning", scenario_list)
        self.assertIn("performance_attribution", scenario_list)

    def test_retail_scenarios_are_product_specific(self):
        """Test retail scenarios are designed for retail lending."""
        retail_scenarios = [
            "retail_origination",
            "retail_portfolio_review",
            "retail_rate_adjustment",
        ]

        for scenario_name in retail_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            # Check that scenario name or description mentions retail
            self.assertTrue(
                "retail" in scenario_name.lower() or "retail" in scenario.description.lower()
            )


class TestSMELoanScenarios(unittest.TestCase):
    """Test SME loan scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("python.multi_agent.base_agent.BaseAgent._init_client"):
            self.orchestrator = MultiAgentOrchestrator()

    def test_sme_underwriting_scenario(self):
        """Test SME underwriting scenario structure."""
        scenario = self.orchestrator.scenarios["sme_underwriting"]
        self.assertEqual(scenario.name, "sme_underwriting")
        self.assertEqual(len(scenario.steps), 4)
        # Verify agent sequence: Risk → Fraud → Pricing → Compliance
        expected_sequence = [
            AgentRole.RISK_ANALYST,
            AgentRole.FRAUD_DETECTION,
            AgentRole.PRICING,
            AgentRole.COMPLIANCE,
        ]
        actual_sequence = [step.agent_role for step in scenario.steps]
        self.assertEqual(actual_sequence, expected_sequence)

    def test_sme_stress_test_scenario(self):
        """Test SME portfolio stress test scenario."""
        scenario = self.orchestrator.scenarios["sme_portfolio_stress_test"]
        self.assertEqual(len(scenario.steps), 3)
        self.assertIn("stress_scenarios", scenario.steps[0].context_keys)

    def test_sme_default_management_scenario(self):
        """Test SME default management scenario."""
        scenario = self.orchestrator.scenarios["sme_default_management"]
        self.assertEqual(len(scenario.steps), 3)
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.COLLECTIONS)

    def test_sme_scenarios_have_descriptions(self):
        """Test all SME scenarios have descriptive text."""
        sme_scenarios = [
            "sme_underwriting",
            "sme_portfolio_stress_test",
            "sme_default_management",
        ]

        for scenario_name in sme_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            self.assertIsNotNone(scenario.description)
            self.assertGreater(len(scenario.description), 10)
            self.assertTrue("SME" in scenario.description or "sme" in scenario_name)


class TestAutoLoanScenarios(unittest.TestCase):
    """Test auto loan scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("python.multi_agent.base_agent.BaseAgent._init_client"):
            self.orchestrator = MultiAgentOrchestrator()

    def test_auto_origination_scenario(self):
        """Test auto loan origination scenario."""
        scenario = self.orchestrator.scenarios["auto_origination"]
        self.assertEqual(len(scenario.steps), 4)
        # Starts with fraud screening
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.FRAUD_DETECTION)

    def test_auto_delinquency_workout_scenario(self):
        """Test auto delinquency workout scenario."""
        scenario = self.orchestrator.scenarios["auto_delinquency_workout"]
        self.assertEqual(len(scenario.steps), 3)
        # Verify Collections → Retention → Risk
        expected_sequence = [
            AgentRole.COLLECTIONS,
            AgentRole.CUSTOMER_RETENTION,
            AgentRole.RISK_ANALYST,
        ]
        actual_sequence = [step.agent_role for step in scenario.steps]
        self.assertEqual(actual_sequence, expected_sequence)

    def test_auto_residual_value_scenario(self):
        """Test auto residual value analysis scenario."""
        scenario = self.orchestrator.scenarios["auto_residual_value_analysis"]
        self.assertEqual(len(scenario.steps), 3)
        self.assertIn("market_data", scenario.steps[0].context_keys)

    def test_auto_scenarios_have_descriptions(self):
        """Test all auto scenarios have descriptive text."""
        auto_scenarios = [
            "auto_origination",
            "auto_delinquency_workout",
            "auto_residual_value_analysis",
        ]

        for scenario_name in auto_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            self.assertIsNotNone(scenario.description)
            self.assertGreater(len(scenario.description), 10)
            self.assertTrue("auto" in scenario_name.lower() or "Auto" in scenario.description)


class TestPortfolioScenarios(unittest.TestCase):
    """Test portfolio-level scenarios."""

    def setUp(self):
        """Set up test fixtures."""
        with patch("python.multi_agent.base_agent.BaseAgent._init_client"):
            self.orchestrator = MultiAgentOrchestrator()

    def test_portfolio_health_check_scenario(self):
        """Test portfolio health check scenario."""
        scenario = self.orchestrator.scenarios["portfolio_health_check"]
        self.assertEqual(len(scenario.steps), 3)
        self.assertIn("portfolio_metrics", scenario.steps[0].context_keys)

    def test_strategic_planning_scenario(self):
        """Test strategic planning scenario."""
        scenario = self.orchestrator.scenarios["strategic_planning"]
        self.assertEqual(len(scenario.steps), 4)
        # Verify Growth → Risk → Pricing → Ops
        expected_sequence = [
            AgentRole.GROWTH_STRATEGIST,
            AgentRole.RISK_ANALYST,
            AgentRole.PRICING,
            AgentRole.OPS_OPTIMIZER,
        ]
        actual_sequence = [step.agent_role for step in scenario.steps]
        self.assertEqual(actual_sequence, expected_sequence)

    def test_regulatory_review_scenario(self):
        """Test regulatory review scenario."""
        scenario = self.orchestrator.scenarios["regulatory_review"]
        self.assertEqual(len(scenario.steps), 3)
        self.assertEqual(scenario.steps[0].agent_role, AgentRole.COMPLIANCE)

    def test_portfolio_scenarios_have_descriptions(self):
        """Test all portfolio scenarios have descriptive text."""
        portfolio_scenarios = [
            "portfolio_health_check",
            "strategic_planning",
            "regulatory_review",
        ]

        for scenario_name in portfolio_scenarios:
            scenario = self.orchestrator.scenarios[scenario_name]
            self.assertIsNotNone(scenario.description)
            self.assertGreater(len(scenario.description), 10)


if __name__ == "__main__":
    unittest.main()
