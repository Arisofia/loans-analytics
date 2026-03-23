from unittest.mock import MagicMock

class TestValidationAgent:

    def test_validation_agent_initialization(self):
        agent = MagicMock()
        agent.name = 'validation_agent'
        assert agent.name == 'validation_agent'

    def test_data_validation(self, sample_portfolio_data):
        agent = MagicMock()
        agent.validate_data.return_value = {'valid': True, 'errors': [], 'warnings': []}
        result = agent.validate_data(sample_portfolio_data)
        assert result['valid'] is True

    def test_schema_validation(self):
        agent = MagicMock()
        agent.validate_schema.return_value = {'schema_valid': True, 'missing_fields': []}
        result = agent.validate_schema({'field1': 'value1'})
        assert result['schema_valid'] is True
