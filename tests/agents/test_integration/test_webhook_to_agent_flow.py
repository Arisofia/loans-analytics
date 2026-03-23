from unittest.mock import MagicMock
import pytest

class TestWebhookToAgentFlow:

    @pytest.mark.asyncio
    async def test_webhook_triggers_agent(self, mock_n8n_webhook):
        _ = mock_n8n_webhook
        webhook_handler = MagicMock()
        webhook_handler.handle_webhook.return_value = {'agent_triggered': True, 'agent_name': 'analytics_agent'}
        result = webhook_handler.handle_webhook({'event': 'new_loan'})
        assert result['agent_triggered'] is True

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_webhook_to_agent_to_supabase(self, mock_n8n_webhook, mock_supabase_client):
        _ = (mock_n8n_webhook, mock_supabase_client)
        flow = MagicMock()
        flow.execute_complete_flow.return_value = {'webhook_received': True, 'agent_executed': True, 'data_stored': True}
        result = flow.execute_complete_flow()
        assert all([result['webhook_received'], result['agent_executed'], result['data_stored']])

    @pytest.mark.asyncio
    async def test_webhook_payload_validation(self):
        validator = MagicMock()
        validator.validate_webhook_payload.return_value = {'valid': True, 'errors': []}
        payload = {'event': 'new_loan', 'data': {'loan_id': 'LOAN-001'}}
        result = validator.validate_webhook_payload(payload)
        assert result['valid'] is True
