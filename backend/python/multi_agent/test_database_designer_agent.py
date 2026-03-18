"""
Tests for DatabaseDesignerAgent.

Tests Database Designer agent to ensure it provides domain-specific expertise
for database design, schema optimization, and data architecture decisions.
"""

import unittest
from unittest.mock import Mock, patch

from backend.python.multi_agent.protocol import AgentRole
from backend.python.multi_agent.specialized_agents import DatabaseDesignerAgent


class TestDatabaseDesignerAgent(unittest.TestCase):
    """Test DatabaseDesignerAgent functionality."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self._init_client_patcher = patch("python.multi_agent.base_agent.BaseAgent._init_client")
        mock_init_client = self._init_client_patcher.start()
        mock_init_client.return_value = Mock()
        self.agent = DatabaseDesignerAgent(role=AgentRole.DATABASE_DESIGNER)

    def tearDown(self) -> None:
        """Tear down test fixtures."""
        self._init_client_patcher.stop()

    def test_agent_initialization(self):
        """Test agent initializes with correct role."""
        self.assertEqual(self.agent.role, AgentRole.DATABASE_DESIGNER)

    def test_system_prompt_covers_key_topics(self):
        """Test system prompt includes all key database design topics."""
        prompt = self.agent.get_system_prompt()
        key_topics = [
            "database",
            "schema",
            "data model",
            "indexing",
            "optimization",
            "performance",
        ]
        for topic in key_topics:
            self.assertIn(topic.lower(), prompt.lower())

    def test_system_prompt_includes_design_approach(self):
        """Test system prompt includes database design methodology."""
        prompt = self.agent.get_system_prompt()
        methodology_keywords = [
            "domain model",
            "requirements",
            "normalized",
            "denormalized",
            "relationships",
        ]
        for keyword in methodology_keywords:
            self.assertIn(keyword.lower(), prompt.lower())

    def test_system_prompt_includes_deliverables(self):
        """Test system prompt specifies expected deliverables."""
        prompt = self.agent.get_system_prompt()
        deliverables = [
            "schema definitions",
            "index recommendations",
            "example queries",
            "transaction management",
            "migration strategies",
        ]
        for deliverable in deliverables:
            self.assertIn(deliverable.lower(), prompt.lower())


if __name__ == "__main__":
    unittest.main()
