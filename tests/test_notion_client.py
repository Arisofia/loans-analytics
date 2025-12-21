import unittest
from unittest.mock import MagicMock, patch
from python.notion_integration.client import NotionClient

class TestNotionClient(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict("os.environ", {"NOTION_META_TOKEN": "fake_token"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_init_sets_up_session_with_retries(self):
        with patch("python.notion_integration.client.requests.Session") as mock_session_cls:
            mock_session = mock_session_cls.return_value
            client = NotionClient()
            
            self.assertTrue(mock_session.mount.called)
            args, _ = mock_session.mount.call_args
            self.assertEqual(args[0], "https://")
            # Check adapter is mounted
            from requests.adapters import HTTPAdapter
            self.assertIsInstance(args[1], HTTPAdapter)

    @patch("python.notion_integration.client.requests.Session")
    def test_query_database_pagination(self, mock_session_cls):
        mock_session = mock_session_cls.return_value
        client = NotionClient()
        
        # Mock responses for two pages
        mock_response_1 = MagicMock()
        mock_response_1.json.return_value = {
            "results": [{"id": "1"}],
            "has_more": True,
            "next_cursor": "cursor_1"
        }
        mock_response_1.raise_for_status.return_value = None

        mock_response_2 = MagicMock()
        mock_response_2.json.return_value = {
            "results": [{"id": "2"}],
            "has_more": False,
            "next_cursor": None
        }
        mock_response_2.raise_for_status.return_value = None

        mock_session.post.side_effect = [mock_response_1, mock_response_2]

        results = client.query_database("db_id")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(results[1]["id"], "2")
        self.assertEqual(mock_session.post.call_count, 2)