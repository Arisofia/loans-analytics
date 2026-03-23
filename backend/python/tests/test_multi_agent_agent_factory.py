import unittest
from unittest.mock import Mock, patch
from backend.python.multi_agent.agent_factory import agent_with_role
from backend.python.multi_agent.base_agent import BaseAgent
from backend.python.multi_agent.protocol import AgentRole, LLMProvider

class TestAgentFactory(unittest.TestCase):

    def test_decorator_adds_init_method(self):

        @agent_with_role(AgentRole.RISK_ANALYST)
        class TestAgent(BaseAgent):

            def get_system_prompt(self) -> str:
                return 'Test prompt'
        self.assertTrue(hasattr(TestAgent, '__init__'))
        self.assertIsNotNone(TestAgent.__init__)

    @patch('backend.python.multi_agent.base_agent.BaseAgent._init_client')
    def test_decorated_agent_initializes_with_correct_role(self, mock_init_client):
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.COMPLIANCE)
        class TestAgent(BaseAgent):

            def get_system_prompt(self) -> str:
                return 'Compliance test prompt'
        agent = TestAgent()
        self.assertEqual(agent.role, AgentRole.COMPLIANCE)

    @patch('backend.python.multi_agent.base_agent.BaseAgent._init_client')
    def test_decorated_agent_accepts_provider_parameter(self, mock_init_client):
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.GROWTH_STRATEGIST)
        class TestAgent(BaseAgent):

            def get_system_prompt(self) -> str:
                return 'Growth test prompt'
        agent1 = TestAgent()
        self.assertEqual(agent1.provider, LLMProvider.OPENAI)
        agent2 = TestAgent(provider=LLMProvider.GEMINI)
        self.assertEqual(agent2.provider, LLMProvider.GEMINI)

    @patch('backend.python.multi_agent.base_agent.BaseAgent._init_client')
    def test_decorated_agent_accepts_kwargs(self, mock_init_client):
        mock_init_client.return_value = Mock()

        @agent_with_role(AgentRole.OPS_OPTIMIZER)
        class TestAgent(BaseAgent):

            def get_system_prompt(self) -> str:
                return 'Ops test prompt'
        agent = TestAgent(model='gpt-4')
        self.assertEqual(agent.model, 'gpt-4')
if __name__ == '__main__':
    unittest.main()
