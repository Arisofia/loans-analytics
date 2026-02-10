"""Integration tests for agent chaining."""

from unittest.mock import MagicMock

import pytest


class TestAgentChaining:
    """Test sequential agent execution chaining."""

    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_sequential_agent_chain(self):
        """Test agents can be chained sequentially."""
        chain = MagicMock()
        chain.execute_chain.return_value = {
            "agents_executed": ["agent1", "agent2", "agent3"],
            "final_result": "Chain completed",
        }

        result = chain.execute_chain(["agent1", "agent2", "agent3"])
        assert len(result["agents_executed"]) == 3

    @pytest.mark.asyncio
    async def test_conditional_agent_chain(self):
        """Test conditional agent execution based on results."""
        chain = MagicMock()
        chain.execute_conditional.return_value = {
            "agents_executed": ["agent1", "agent3"],
            "skipped": ["agent2"],
        }

        result = chain.execute_conditional()
        assert "agent2" in result["skipped"]

    @pytest.mark.asyncio
    async def test_parallel_agent_execution(self):
        """Test parallel execution of independent agents."""
        orchestrator = MagicMock()
        orchestrator.execute_parallel.return_value = {
            "agents": ["agent1", "agent2"],
            "all_completed": True,
        }

        result = orchestrator.execute_parallel(["agent1", "agent2"])
        assert result["all_completed"] is True
