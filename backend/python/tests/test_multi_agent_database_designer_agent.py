import unittest
from unittest.mock import Mock, patch
from backend.python.multi_agent.protocol import AgentRole
from backend.python.multi_agent.specialized_agents import DatabaseDesignerAgent

class TestDatabaseDesignerAgent(unittest.TestCase):

    def setUp(self) -> None:
        self._init_client_patcher = patch('backend.python.multi_agent.base_agent.BaseAgent._init_client')
        mock_init_client = self._init_client_patcher.start()
        mock_init_client.return_value = Mock()
        self.agent = DatabaseDesignerAgent(role=AgentRole.DATABASE_DESIGNER)

    def tearDown(self) -> None:
        self._init_client_patcher.stop()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.role, AgentRole.DATABASE_DESIGNER)

    def test_system_prompt_covers_key_topics(self):
        prompt = self.agent.get_system_prompt().lower()
        self.assertIn('database', prompt)
        self.assertIn('schema', prompt)
        self.assertIn('data model', prompt)
        self.assertIn('indexing', prompt)
        self.assertIn('optimization', prompt)
        self.assertIn('performance', prompt)

    def test_system_prompt_includes_design_approach(self):
        prompt = self.agent.get_system_prompt().lower()
        self.assertIn('domain model', prompt)
        self.assertIn('requirements', prompt)
        self.assertIn('normalized', prompt)
        self.assertIn('denormalized', prompt)
        self.assertIn('relationships', prompt)

    def test_system_prompt_includes_deliverables(self):
        prompt = self.agent.get_system_prompt().lower()
        self.assertIn('schema definitions', prompt)
        self.assertIn('index recommendations', prompt)
        self.assertIn('example queries', prompt)
        self.assertIn('transaction management', prompt)
        self.assertIn('migration strategies', prompt)
if __name__ == '__main__':
    unittest.main()
