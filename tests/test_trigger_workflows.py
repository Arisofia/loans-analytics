import unittest
from unittest.mock import MagicMock, patch
import os
import requests
from scripts.trigger_workflows import (
    fetch_workflows,
    resolve_workflow_targets,
    trigger_workflow,
    ensure_token
)

class TestTriggerWorkflows(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, {"GITHUB_TOKEN": "dummy_token"})
        self.env_patcher.start()

    def tearDown(self):
        self.env_patcher.stop()

    def test_ensure_token(self):
        self.assertEqual(ensure_token(), "dummy_token")

    def test_ensure_token_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                ensure_token()

    @patch("scripts.trigger_workflows.SESSION")
    def test_fetch_workflows(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"workflows": [{"id": 1, "name": "CI"}]}
        mock_resp.raise_for_status.return_value = None
        mock_session.get.return_value = mock_resp

        wfs = fetch_workflows("owner/repo", "token")
        self.assertEqual(len(wfs), 1)
        self.assertEqual(wfs[0]["name"], "CI")

    @patch("scripts.trigger_workflows.SESSION")
    def test_fetch_workflows_error(self, mock_session):
        mock_session.get.side_effect = requests.exceptions.RequestException("Error")
        with self.assertRaises(SystemExit):
            fetch_workflows("owner/repo", "token")

    def test_resolve_workflow_targets(self):
        workflows = [
            {"id": 123, "name": "CI Pipeline"},
            {"id": 456, "name": "Deploy"},
        ]
        
        # Test ID matching
        resolved = resolve_workflow_targets(workflows, ["123"])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["name"], "CI Pipeline")

        # Test Name matching (case-insensitive)
        resolved = resolve_workflow_targets(workflows, ["deploy"])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["id"], 456)

        # Test missing
        with self.assertRaises(ValueError):
            resolve_workflow_targets(workflows, ["Missing"])

    @patch("scripts.trigger_workflows.SESSION")
    def test_trigger_workflow_success(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_session.post.return_value = mock_resp

        wf = {"id": 123, "name": "CI"}
        success = trigger_workflow("owner/repo", wf, "main", "token")
        self.assertTrue(success)
        mock_session.post.assert_called_once()

    @patch("scripts.trigger_workflows.SESSION")
    def test_trigger_workflow_failure(self, mock_session):
        mock_session.post.side_effect = requests.exceptions.RequestException("Boom")
        
        wf = {"id": 123, "name": "CI"}
        success = trigger_workflow("owner/repo", wf, "main", "token")
        self.assertFalse(success)