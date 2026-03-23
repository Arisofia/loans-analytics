from __future__ import annotations
import os
import unittest
from unittest.mock import MagicMock, patch
from backend.python.multi_agent.base_agent import BaseAgent
from backend.python.multi_agent.protocol import AgentRequest, AgentRole, LLMProvider, Message, MessageRole

class _TestAgent(BaseAgent):

    def get_system_prompt(self) -> str:
        return 'system prompt'

class TestBaseAgentGrok(unittest.TestCase):

    @patch.object(BaseAgent, '_init_client', return_value=MagicMock())
    def test_default_model_uses_grok_env(self, _mock_init_client):
        with patch.dict(os.environ, {'GROK_MODEL': 'grok-test-model'}, clear=False):
            agent = _TestAgent(role=AgentRole.RISK_ANALYST, provider=LLMProvider.GROK)
            self.assertEqual(agent.model, 'grok-test-model')

    @patch.object(BaseAgent, '_init_client', return_value=MagicMock())
    def test_call_llm_dispatches_to_grok(self, _mock_init_client):
        agent = _TestAgent(role=AgentRole.RISK_ANALYST, provider=LLMProvider.GROK)
        request = AgentRequest(trace_id='trace-test', messages=[Message(role=MessageRole.USER, content='hello')])
        with patch.object(agent, '_call_grok', return_value={'content': 'ok'}) as mock_call_grok:
            result = agent._call_llm([{'role': 'user', 'content': 'hello'}], request)
            self.assertEqual(result['content'], 'ok')
            mock_call_grok.assert_called_once()

    @patch.object(BaseAgent, '_init_client', return_value=MagicMock())
    def test_init_grok_client_uses_xai_settings(self, _mock_init_client):
        agent = _TestAgent(role=AgentRole.RISK_ANALYST, provider=LLMProvider.GROK)
        with patch('backend.python.multi_agent.base_agent.OpenAI') as mock_openai, patch.dict(os.environ, {'XAI_API_KEY': 'xai-test-key', 'XAI_BASE_URL': 'https://api.x.ai/v1', 'LLM_TIMEOUT': '30', 'LLM_MAX_RETRIES': '4'}, clear=False):
            _ = agent._init_grok_client()
            mock_openai.assert_called_once_with(api_key='xai-test-key', base_url='https://api.x.ai/v1', timeout=30.0, max_retries=4)

    @patch.object(BaseAgent, '_init_client', return_value=MagicMock())
    def test_init_grok_client_requires_key(self, _mock_init_client):
        agent = _TestAgent(role=AgentRole.RISK_ANALYST, provider=LLMProvider.GROK)
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'XAI_API_KEY not set'):
                agent._init_grok_client()
if __name__ == '__main__':
    unittest.main()
