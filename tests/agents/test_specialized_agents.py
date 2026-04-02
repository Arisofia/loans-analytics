import unittest
from unittest.mock import Mock, patch
from backend.loans_analytics.multi_agent.protocol import AgentRole
from backend.loans_analytics.multi_agent.specialized_agents import CollectionsAgent, CustomerRetentionAgent, DatabaseDesignerAgent, FraudDetectionAgent, PricingAgent

class TestCollectionsAgent(unittest.TestCase):

    @patch('backend.loans_analytics.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = Mock()
        self.agent = CollectionsAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.role, AgentRole.COLLECTIONS)

    def test_system_prompt_covers_key_topics(self):
        prompt = self.agent.get_system_prompt()
        key_topics = ['delinquency', 'recovery', 'segment', 'payment plan', 'portfolio', 'collection']
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())

class TestFraudDetectionAgent(unittest.TestCase):

    @patch('backend.loans_analytics.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = Mock()
        self.agent = FraudDetectionAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.role, AgentRole.FRAUD_DETECTION)

    def test_system_prompt_covers_fraud_topics(self):
        prompt = self.agent.get_system_prompt()
        key_topics = ['fraud', 'identity', 'transaction', 'verification', 'pattern', 'detection']
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())

class TestPricingAgent(unittest.TestCase):

    @patch('backend.loans_analytics.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = Mock()
        self.agent = PricingAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.role, AgentRole.PRICING)

    def test_system_prompt_covers_pricing_topics(self):
        prompt = self.agent.get_system_prompt()
        key_topics = ['pricing', 'rate', 'risk-based', 'competitive', 'optimization', 'margin']
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())

class TestCustomerRetentionAgent(unittest.TestCase):

    @patch('backend.loans_analytics.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = Mock()
        self.agent = CustomerRetentionAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.role, AgentRole.CUSTOMER_RETENTION)

    def test_system_prompt_covers_retention_topics(self):
        prompt = self.agent.get_system_prompt()
        key_topics = ['retention', 'churn', 'lifetime value', 'loyalty', 'engagement', 'segment']
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())

class TestSpecializedAgentIntegration(unittest.TestCase):

    @patch('backend.loans_analytics.multi_agent.base_agent.BaseAgent._init_client')
    def setUp(self, mock_init_client):
        mock_init_client.return_value = Mock()
        self.collections = CollectionsAgent()
        self.fraud = FraudDetectionAgent()
        self.pricing = PricingAgent()
        self.retention = CustomerRetentionAgent()
        self.database_designer = DatabaseDesignerAgent()

    def test_all_agents_have_unique_roles(self):
        roles = [self.collections.role, self.fraud.role, self.pricing.role, self.retention.role, self.database_designer.role]
        self.assertEqual(len(roles), len(set(roles)), 'Agents should have unique roles')

    def test_all_agents_have_system_prompts(self):
        agents = [self.collections, self.fraud, self.pricing, self.retention, self.database_designer]
        for agent in agents:
            prompt = agent.get_system_prompt()
            self.assertIsNotNone(prompt)
            self.assertGreater(len(prompt), 100)
            self.assertIn('You are', prompt)

    def test_agent_role_names_match_constants(self):
        self.assertEqual(self.collections.role, AgentRole.COLLECTIONS)
        self.assertEqual(self.fraud.role, AgentRole.FRAUD_DETECTION)
        self.assertEqual(self.pricing.role, AgentRole.PRICING)
        self.assertEqual(self.retention.role, AgentRole.CUSTOMER_RETENTION)
        self.assertEqual(self.database_designer.role, AgentRole.DATABASE_DESIGNER)
if __name__ == '__main__':
    unittest.main()
