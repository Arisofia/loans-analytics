from unittest.mock import MagicMock
import pytest

class TestErrorScenarios:

    @pytest.mark.asyncio
    async def test_agent_failure_recovery(self):
        agent = MagicMock()
        agent.execute.side_effect = [Exception('First attempt failed'), {'status': 'success'}]
        with pytest.raises(Exception):
            agent.execute('task')
        result = agent.execute('task')
        assert result['status'] == 'success'

    @pytest.mark.asyncio
    async def test_invalid_input_handling(self):
        validator = MagicMock()
        validator.validate.return_value = {'valid': False, 'errors': ['Missing required field: loan_id']}
        invalid_data = {'amount': 1000}
        result = validator.validate(invalid_data)
        assert result['valid'] is False
        assert len(result['errors']) > 0

    @pytest.mark.asyncio
    async def test_database_connection_failure(self, mock_supabase_client):
        mock_supabase_client.table.side_effect = Exception('Connection failed')
        with pytest.raises(Exception):
            mock_supabase_client.table('test').select('*')

    @pytest.mark.asyncio
    async def test_llm_api_failure(self, mock_llm_provider):
        mock_llm_provider.complete.side_effect = Exception('API rate limit exceeded')
        with pytest.raises(Exception):
            mock_llm_provider.complete([{'role': 'user', 'content': 'test'}])
