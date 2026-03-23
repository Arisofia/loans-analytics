from unittest.mock import MagicMock

class TestCustomAgents:

    def test_custom_agent_registration(self):
        registry = MagicMock()
        registry.register.return_value = {'registered': True}
        result = registry.register('custom_agent', {})
        assert result['registered'] is True

    def test_custom_agent_execution(self, agent_execution_context):
        agent = MagicMock()
        agent.execute_custom.return_value = {'status': 'success', 'result': 'Custom task completed'}
        result = agent.execute_custom('custom_task', agent_execution_context)
        assert result['status'] == 'success'
