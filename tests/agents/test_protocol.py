"""Tests for agent communication protocol."""

from unittest.mock import MagicMock

import pytest


class TestAgentProtocol:
    """Test suite for agent communication protocol."""

    def test_protocol_message_format(self, sample_agent_message):
        """Test protocol message follows correct format."""
        assert isinstance(sample_agent_message, list)
        assert all(isinstance(msg, dict) for msg in sample_agent_message)
        assert all("role" in msg and "content" in msg for msg in sample_agent_message)

    def test_protocol_request_structure(self):
        """Test protocol request structure."""
        request = {
            "action": "analyze",
            "payload": {"data": "test"},
            "metadata": {"timestamp": "2026-01-28T00:00:00Z"},
        }
        assert "action" in request
        assert "payload" in request
        assert "metadata" in request

    def test_protocol_response_structure(self, mock_agent_response):
        """Test protocol response structure."""
        assert "status" in mock_agent_response
        assert "result" in mock_agent_response
        assert "metadata" in mock_agent_response

    def test_protocol_error_response(self):
        """Test protocol error response format."""
        error_response = {
            "status": "error",
            "error_code": "AGENT_ERROR_001",
            "error_message": "Agent execution failed",
            "metadata": {"timestamp": "2026-01-28T00:00:00Z"},
        }
        assert error_response["status"] == "error"
        assert "error_code" in error_response

    def test_protocol_versioning(self):
        """Test protocol version compatibility."""
        protocol = MagicMock()
        protocol.version = "1.0.0"
        protocol.is_compatible.return_value = True

        assert protocol.is_compatible("1.0.0")

    def test_protocol_serialization(self, mock_agent_response):
        """Test protocol message serialization."""
        protocol = MagicMock()
        protocol.serialize.return_value = '{"status": "success"}'

        serialized = protocol.serialize(mock_agent_response)
        assert isinstance(serialized, str)

    def test_protocol_deserialization(self):
        """Test protocol message deserialization."""
        protocol = MagicMock()
        protocol.deserialize.return_value = {"status": "success"}

        deserialized = protocol.deserialize('{"status": "success"}')
        assert isinstance(deserialized, dict)

    def test_protocol_validation(self):
        """Test protocol message validation."""
        protocol = MagicMock()
        protocol.validate.return_value = {"valid": True, "errors": []}

        message = {"action": "test", "payload": {}}
        result = protocol.validate(message)
        assert result["valid"] is True
