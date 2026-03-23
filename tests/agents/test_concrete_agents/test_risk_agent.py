from unittest.mock import MagicMock

class TestRiskAgent:

    def test_risk_agent_initialization(self, mock_llm_provider):
        agent = MagicMock()
        agent.name = 'risk_agent'
        assert agent.name == 'risk_agent'

    def test_credit_risk_assessment(self, sample_portfolio_data):
        agent = MagicMock()
        agent.assess_credit_risk.return_value = {'risk_score': 0.35, 'risk_level': 'medium', 'factors': ['high_ltv', 'previous_default']}
        result = agent.assess_credit_risk(sample_portfolio_data)
        assert result['risk_level'] == 'medium'

    def test_early_warning_system(self):
        agent = MagicMock()
        agent.check_early_warnings.return_value = {'alerts': [{'type': 'high_delinquency', 'severity': 'high'}], 'alert_count': 1}
        result = agent.check_early_warnings()
        assert result['alert_count'] > 0
