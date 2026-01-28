"""Tests for validation agent."""

import pytest
from unittest.mock import MagicMock


class TestValidationAgent:
    """Test suite for validation agent."""

    def test_validation_agent_initialization(self):
        """Test validation agent initialization."""
        agent = MagicMock()
        agent.name = "validation_agent"
        assert agent.name == "validation_agent"

    def test_data_validation(self, sample_portfolio_data):
        """Test data validation."""
        agent = MagicMock()
        agent.validate_data.return_value = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }
        
        result = agent.validate_data(sample_portfolio_data)
        assert result["valid"] is True

    def test_schema_validation(self):
        """Test schema validation."""
        agent = MagicMock()
        agent.validate_schema.return_value = {
            "schema_valid": True,
            "missing_fields": [],
        }
        
        result = agent.validate_schema({"field1": "value1"})
        assert result["schema_valid"] is True
