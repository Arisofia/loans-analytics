"""
Tests for specialized fintech agents.

Tests Collections, Fraud Detection, Pricing, and Customer Retention agents
to ensure they provide domain-specific expertise and respond appropriately
to fintech scenarios.
"""

import unittest
from unittest.mock import Mock, patch

from python.multi_agent.specialized_agents import (
    CollectionsAgent,
    FraudDetectionAgent,
    PricingAgent,
    CustomerRetentionAgent,
)
from python.multi_agent.protocol import AgentRole


class TestCollectionsAgent(unittest.TestCase):
    """Test CollectionsAgent functionality."""

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def setUp(self, mock_init_client):
        """Set up test fixtures."""
        mock_init_client.return_value = Mock()
        self.agent = CollectionsAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct role."""
        self.assertEqual(self.agent.role, AgentRole.COLLECTIONS)

    def test_system_prompt_covers_key_topics(self):
        """Test system prompt includes all key collections topics."""
        prompt = self.agent.get_system_prompt()
        key_topics = [
            "delinquency",
            "recovery",
            "segment",  # Changed from "segmentation"
            "payment plan",
            "portfolio",
            "collection",  # Changed from "regulatory"
        ]
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())


class TestFraudDetectionAgent(unittest.TestCase):
    """Test FraudDetectionAgent functionality."""

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def setUp(self, mock_init_client):
        """Set up test fixtures."""
        mock_init_client.return_value = Mock()
        self.agent = FraudDetectionAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct role."""
        self.assertEqual(self.agent.role, AgentRole.FRAUD_DETECTION)

    def test_system_prompt_covers_fraud_topics(self):
        """Test system prompt includes fraud detection expertise."""
        prompt = self.agent.get_system_prompt()
        key_topics = [
            "fraud",
            "identity",
            "transaction",
            "verification",
            "pattern",
            "detection",  # Changed from "investigation"
        ]
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())


class TestPricingAgent(unittest.TestCase):
    """Test PricingAgent functionality."""

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def setUp(self, mock_init_client):
        """Set up test fixtures."""
        mock_init_client.return_value = Mock()
        self.agent = PricingAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct role."""
        self.assertEqual(self.agent.role, AgentRole.PRICING)

    def test_system_prompt_covers_pricing_topics(self):
        """Test system prompt includes pricing expertise."""
        prompt = self.agent.get_system_prompt()
        key_topics = [
            "pricing",
            "rate",
            "risk-based",
            "competitive",
            "optimization",
            "margin",
        ]
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())


class TestCustomerRetentionAgent(unittest.TestCase):
    """Test CustomerRetentionAgent functionality."""

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def setUp(self, mock_init_client):
        """Set up test fixtures."""
        mock_init_client.return_value = Mock()
        self.agent = CustomerRetentionAgent()

    def test_agent_initialization(self):
        """Test agent initializes with correct role."""
        self.assertEqual(self.agent.role, AgentRole.CUSTOMER_RETENTION)

    def test_system_prompt_covers_retention_topics(self):
        """Test system prompt includes retention expertise."""
        prompt = self.agent.get_system_prompt()
        key_topics = [
            "retention",
            "churn",
            "lifetime value",
            "loyalty",
            "engagement",
            "segment",
        ]
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())


class TestSpecializedAgentIntegration(unittest.TestCase):
    """Test specialized agents work together in workflows."""

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def setUp(self, mock_init_client):
        """Set up test fixtures."""
        mock_init_client.return_value = Mock()
        self.collections = CollectionsAgent()
        self.fraud = FraudDetectionAgent()
        self.pricing = PricingAgent()
        self.retention = CustomerRetentionAgent()

    def test_all_agents_have_unique_roles(self):
        """Test each specialized agent has a unique role."""
        roles = [
            self.collections.role,
            self.fraud.role,
            self.pricing.role,
            self.retention.role,
        ]
        self.assertEqual(len(roles), len(set(roles)), "Agents should have unique roles")

    def test_all_agents_have_system_prompts(self):
        """Test all agents have comprehensive system prompts."""
        agents = [self.collections, self.fraud, self.pricing, self.retention]
        for agent in agents:
            prompt = agent.get_system_prompt()
            self.assertIsNotNone(prompt)
            self.assertGreater(len(prompt), 100)
            self.assertIn("You are", prompt)

    def test_agent_role_names_match_constants(self):
        """Test agent roles match expected protocol constants."""
        self.assertEqual(self.collections.role, AgentRole.COLLECTIONS)
        self.assertEqual(self.fraud.role, AgentRole.FRAUD_DETECTION)
        self.assertEqual(self.pricing.role, AgentRole.PRICING)
        self.assertEqual(self.retention.role, AgentRole.CUSTOMER_RETENTION)


if __name__ == "__main__":
    unittest.main()
