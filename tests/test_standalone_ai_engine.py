import unittest
from unittest.mock import MagicMock

from abaco_runtime.standalone_ai_engine import StandaloneAIEngine
from scripts.clients import AIResponse


class TestStandaloneAIEngine(unittest.TestCase):
    def setUp(self):
        self.mock_grok = MagicMock()
        self.mock_gemini = MagicMock()
        # Set a small limit to easily test routing and truncation
        self.engine = StandaloneAIEngine(
            grok_client=self.mock_grok, gemini_client=self.mock_gemini, max_prompt_chars=100
        )

    def test_routes_small_payload_to_grok(self):
        self.mock_grok.generate_text.return_value = AIResponse(text="Grok response", raw={})

        data = {"key": "small"}
        response = self.engine.generate_response("persona", {}, data)

        self.assertEqual(response, "Grok response")
        self.mock_grok.generate_text.assert_called_once()
        self.mock_gemini.generate_text.assert_not_called()

    def test_routes_large_payload_to_gemini(self):
        self.mock_gemini.generate_text.return_value = AIResponse(text="Gemini response", raw={})

        # Create data larger than max_prompt_chars // 2 (50) but smaller than max (100)
        data = {"key": "x" * 60}
        response = self.engine.generate_response("persona", {}, data)

        self.assertEqual(response, "Gemini response")
        self.mock_gemini.generate_text.assert_called_once()
        self.mock_grok.generate_text.assert_not_called()

    def test_truncates_oversized_payload(self):
        self.mock_gemini.generate_text.return_value = AIResponse(text="Response", raw={})

        # Create data larger than max_prompt_chars (100)
        data = {"key": "x" * 150}
        self.engine.generate_response("persona", {}, data)

        # Check that the prompt passed to generate_text contains the truncated marker
        args, _ = self.mock_gemini.generate_text.call_args
        prompt = args[0]
        self.assertIn("[TRUNCATED]", prompt)
