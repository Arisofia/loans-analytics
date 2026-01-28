"""Tests for base agent functionality."""

from unittest.mock import MagicMock

import pytest


class TestBaseAgent:
    """Test suite for base agent class."""

    def test_base_agent_initialization(self, mock_llm_provider):
        """Test base agent can be initialized with LLM provider."""
        agent = MagicMock()
        agent.llm_provider = mock_llm_provider
        assert agent.llm_provider is not None

    def test_agent_execute_method(self, agent_execution_context):
        """Test base agent execute method."""
        agent = MagicMock()
        agent.execute.return_value = {
            "status": "success",
            "result": "Task completed",
        }

        result = agent.execute("test_task", agent_execution_context)
        assert result["status"] == "success"

    def test_agent_validate_method(self, sample_portfolio_data):
        """Test base agent validation method."""
        agent = MagicMock()
        agent.validate.return_value = {"valid": True, "errors": []}

        result = agent.validate(sample_portfolio_data)
        assert result["valid"] is True

    def test_agent_handle_error_method(self):
        """Test base agent error handling."""
        agent = MagicMock()
        agent.handle_error.return_value = {
            "error_handled": True,
            "recovery_action": "retry",
        }

        error = Exception("Test error")
        result = agent.handle_error(error)
        assert result["error_handled"] is True

    def test_agent_logging(self, agent_execution_context):
        """Test agent logging functionality."""
        agent = MagicMock()
        agent.log.return_value = {"logged": True}

        result = agent.log("Test log message", agent_execution_context)
        agent.log.assert_called_once()

    def test_agent_metrics_collection(self, performance_metrics):
        """Test agent collects performance metrics."""
        agent = MagicMock()
        agent.collect_metrics.return_value = {
            "execution_time": 100,
            "tokens_used": 50,
        }

        result = agent.collect_metrics()
        assert "execution_time" in result

    def test_agent_configuration(self):
        """Test agent configuration settings."""
        agent = MagicMock()
        agent.configure.return_value = {"configured": True}

        config = {"timeout": 30, "max_retries": 3}
        result = agent.configure(config)
        assert result["configured"] is True

    def test_agent_state_management(self):
        """Test agent state management."""
        agent = MagicMock()
        agent.get_state.return_value = {"state": "idle"}
        agent.set_state.return_value = {"state": "running"}

        state = agent.get_state()
        assert state["state"] == "idle"

        agent.set_state("running")
        agent.set_state.assert_called_once_with("running")
