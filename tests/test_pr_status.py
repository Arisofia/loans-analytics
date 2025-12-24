import unittest
from unittest.mock import MagicMock, patch

from scripts.pr_status import GitHubRequestError, render_report


class TestPRStatus(unittest.TestCase):
    @patch("scripts.pr_status.SESSION")
    def test_render_report_success(self, mock_session):
        # Mock pull request response
        mock_pr_resp = MagicMock()
        mock_pr_resp.ok = True
        mock_pr_resp.json.return_value = {
            "title": "Test PR",
            "html_url": "http://github.com/pr/1",
            "state": "open",
            "draft": False,
            "mergeable_state": "clean",
            "rebaseable": True,
            "head": {"sha": "sha123"},
        }

        # Mock check runs response
        mock_checks_resp = MagicMock()
        mock_checks_resp.ok = True
        mock_checks_resp.json.return_value = {
            "check_runs": [
                {
                    "name": "ci",
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": "http://ci",
                }
            ]
        }

        # Mock commit status response
        mock_status_resp = MagicMock()
        mock_status_resp.ok = True
        mock_status_resp.json.return_value = {"state": "success", "statuses": []}

        mock_session.get.side_effect = [mock_pr_resp, mock_checks_resp, mock_status_resp]

        report = render_report("owner/repo", 1)
        self.assertIn("PR #1: Test PR", report)
        self.assertIn("ci: completed/success", report)
        self.assertIn("Mergeable: clean", report)

    @patch("scripts.pr_status.SESSION")
    def test_render_report_auth_failure(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_session.get.return_value = mock_resp

        with self.assertRaises(GitHubRequestError) as cm:
            render_report("owner/repo", 1)
        self.assertIn("Authentication failed", str(cm.exception))

    @patch("scripts.pr_status.SESSION")
    def test_list_open_prs(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [{"number": 1}, {"number": 2}]
        mock_session.get.return_value = mock_resp

        from scripts.pr_status import list_open_prs

        prs = list_open_prs("owner/repo")
        self.assertEqual(prs, [1, 2])
