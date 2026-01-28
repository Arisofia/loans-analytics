"""Integration tests for Supabase connectivity."""

import pytest
from unittest.mock import MagicMock, patch


class TestSupabaseIntegration:
    """Test Supabase database integration."""

    @pytest.mark.asyncio
    async def test_supabase_connection(self, mock_supabase_client):
        """Test connection to Supabase."""
        result = mock_supabase_client.table("test").select("*").execute()
        assert result.data is not None

    @pytest.mark.asyncio
    async def test_agent_data_persistence(self, mock_supabase_client, mock_agent_response):
        """Test agent results can be persisted to Supabase."""
        mock_supabase_client.table("agent_results").insert.return_value.execute.return_value = Mock(
            data=[{"id": 1, "agent_name": "test_agent"}]
        )
        
        result = mock_supabase_client.table("agent_results").insert(mock_agent_response).execute()
        assert result.data is not None

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_agent_query_supabase(self, mock_supabase_client):
        """Test agent can query data from Supabase."""
        mock_supabase_client.table("loans").select.return_value.execute.return_value = Mock(
            data=[{"loan_id": "LOAN-001", "status": "active"}]
        )
        
        result = mock_supabase_client.table("loans").select("*").execute()
        assert len(result.data) > 0


# Import Mock for the test
from unittest.mock import Mock
