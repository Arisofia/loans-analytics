"""Tests for agent factory utilities."""

import unittest
from unittest.mock import Mock, patch

from python.multi_agent.agent_factory import agent_with_role
from python.multi_agent.base_agent import BaseAgent
from python.multi_agent.protocol import AgentRole, LLMProvider


class TestAgentFactory(unittest.TestCase):
    """Test agent factory decorator functionality."""

    def test_decorator_adds_init_method(self):
        """Test that the decorator adds an __init__ method to the class."""

        @agent_with_role(AgentRole.RISK_ANALYST)
        class TestAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Test prompt"

        # Verify the class has __init__
        self.assertTrue(hasattr(TestAgent, "__init__"))
        self.assertIsNotNone(TestAgent.__init__)

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def test_decorated_agent_initializes_with_correct_role(self, mock_init_client):
        """Test that decorated agent initializes with the specified role."""
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.COMPLIANCE)
        class TestAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Compliance test prompt"

        agent = TestAgent()
        self.assertEqual(agent.role, AgentRole.COMPLIANCE)

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def test_decorated_agent_accepts_provider_parameter(self, mock_init_client):
        """Test that decorated agent accepts provider parameter."""
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.GROWTH_STRATEGIST)
        class TestAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Growth test prompt"

        # Test with default provider
        agent1 = TestAgent()
        self.assertEqual(agent1.provider, LLMProvider.OPENAI)

        # Test with custom provider
        agent2 = TestAgent(provider=LLMProvider.ANTHROPIC)
        self.assertEqual(agent2.provider, LLMProvider.ANTHROPIC)

    @patch("python.multi_agent.base_agent.BaseAgent._init_client")
    def test_decorated_agent_accepts_kwargs(self, mock_init_client):
        """Test that decorated agent passes through kwargs."""
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.OPS_OPTIMIZER)
        class TestAgent(BaseAgent):
            def get_system_prompt(self) -> str:
                return "Ops test prompt"

        # Test with custom model
        agent = TestAgent(model="gpt-4")
        self.assertEqual(agent.model, "gpt-4")


if __name__ == "__main__":
    unittest.main()
