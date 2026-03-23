from unittest.mock import Mock
import pytest

class TestSupabaseIntegration:

    @pytest.mark.asyncio
    async def test_supabase_connection(self, mock_supabase_client):
        result = mock_supabase_client.table('test').select('*').execute()
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_agent_data_persistence(self, mock_supabase_client, mock_agent_response):
        mock_supabase_client.table('agent_results').insert.return_value.execute.return_value = Mock(data=[{'id': 1, 'agent_name': 'test_agent'}])
        result = mock_supabase_client.table('agent_results').insert(mock_agent_response).execute()
        assert result.data is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_agent_query_supabase(self, mock_supabase_client):
        mock_supabase_client.table('loans').select.return_value.execute.return_value = Mock(data=[{'loan_id': 'LOAN-001', 'status': 'active'}])
        result = mock_supabase_client.table('loans').select('*').execute()
        assert len(result.data) > 0
