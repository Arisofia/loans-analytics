import unittest
from unittest.mock import MagicMock, patch
import os
from scripts.clients import GrokClient, GeminiClient, AIResponse

class TestGrokClient(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {"GROK_API_KEY": "dummy_key"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_init_defaults(self):
        client = GrokClient()
        self.assertEqual(client.model, "grok-beta")
        self.assertEqual(client.base_url, "https://api.groq.com/v1")

    @patch("scripts.clients.requests.Session")
    def test_session_configuration(self, mock_session_cls):
        mock_session = mock_session_cls.return_value
        _ = GrokClient()
        
        # Verify adapter mount
        self.assertTrue(mock_session.mount.called)
        args, _ = mock_session.mount.call_args
        self.assertEqual(args[0], "https://")
        
        # Verify retry configuration
        from requests.adapters import HTTPAdapter
        self.assertIsInstance(args[1], HTTPAdapter)
        self.assertEqual(args[1].max_retries.total, 3)

    @patch("scripts.clients.requests.Session")
    def test_generate_text_calls_api(self, mock_session_cls):
        mock_session = mock_session_cls.return_value
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_response.raise_for_status.return_value = None
        mock_session.post.return_value = mock_response
        
        client = GrokClient()
        result = client.generate_text("Test prompt")
        
        self.assertIsInstance(result, AIResponse)
        self.assertEqual(result.text, "Test response")
        mock_session.post.assert_called_once()
        
        # Verify URL and headers
        args, kwargs = mock_session.post.call_args
        self.assertEqual(args[0], "https://api.groq.com/v1/chat/completions")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer dummy_key")

    def test_generate_text_raises_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            client = GrokClient(api_key=None)
            with self.assertRaises(ValueError):
                client.generate_text("prompt")


class TestGeminiClient(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {"GOOGLE_API_KEY": "dummy_key"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("scripts.clients.genai")
    def test_init_configures_genai(self, mock_genai):
        _ = GeminiClient()
        mock_genai.configure.assert_called_with(api_key="dummy_key")
        mock_genai.GenerativeModel.assert_called_with("gemini-1.5-pro")

    def test_init_raises_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                GeminiClient(api_key=None)

    @patch("scripts.clients.genai")
    def test_generate_text_calls_model(self, mock_genai):
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        mock_response = MagicMock()
        mock_response.text = "Gemini response"
        mock_response.to_json.return_value = '{"candidates": []}'
        mock_model.generate_content.return_value = mock_response

        client = GeminiClient()
        result = client.generate_text("prompt")

        self.assertEqual(result.text, "Gemini response")
        mock_model.generate_content.assert_called_with("prompt", generation_config={})