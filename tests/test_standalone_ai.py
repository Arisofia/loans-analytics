import unittest
from unittest.mock import MagicMock, mock_open, patch

from abaco_runtime.standalone_ai import StandaloneAIEngine


class TestStandaloneAI(unittest.TestCase):
    def setUp(self):
        self.mock_kb_data = '{"risk_guidelines": "Always check LTV."}'

    @patch("pathlib.Path.exists", return_value=True)
    @patch(
        "pathlib.Path.open",
        new_callable=mock_open,
        read_data='{"risk_guidelines": "Always check LTV."}',
    )
    @patch("abaco_runtime.standalone_ai.GrokClient")
    def test_generate_response_online(self, mock_grok_cls, mock_file, mock_exists):
        # Setup mock client
        mock_client = mock_grok_cls.return_value
        mock_response = MagicMock()
        mock_response.text = "AI Analysis: Risk is low."
        mock_client.generate_text.return_value = mock_response

        # Initialize engine with mock client
        engine = StandaloneAIEngine(ai_client=mock_client)

        context = {"summary": "Loan application", "knowledge_id": "risk_guidelines"}
        data = {"ltv": 80}

        response = engine.generate_response("risk_analyst", context, data)

        self.assertEqual(response, "AI Analysis: Risk is low.")
        mock_client.generate_text.assert_called_once()

    @patch("pathlib.Path.exists", return_value=False)
    def test_generate_response_offline(self, mock_exists):
        engine = StandaloneAIEngine(ai_client=None)
        response = engine.generate_response("risk_analyst", {"summary": "Offline test"}, {"kpi": 1})

        self.assertIn("[authoritative and concise]", response)
        self.assertIn("Offline test", response)
