import unittest
from unittest.mock import MagicMock, patch

from scripts.pr_status import (
    GitHubRequestError,
    merge_pr,
    merge_readiness,
    render_report,
)


class TestPRStatus(unittest.TestCase):
    @patch("scripts.pr_status.SESSION")
    def test_render_report_success(self, mock_session):
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

        mock_status_resp = MagicMock()
        mock_status_resp.ok = True
        mock_status_resp.json.return_value = {"state": "success", "statuses": []}

        mock_session.get.side_effect = [mock_pr_resp, mock_checks_resp, mock_status_resp]

        report = render_report("owner/repo", 1)
        self.assertIn("PR #1: Test PR", report)
        self.assertIn("ci: completed/success", report)
        self.assertIn("Mergeable: clean", report)
        self.assertIn("Ready to merge: yes", report)

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

    def test_merge_readiness_success(self):
        pr = {"mergeable_state": "clean", "draft": False}
        checks = [{"status": "completed", "conclusion": "success"}]
        status_payload = {"state": "success", "statuses": [{"context": "ci", "state": "success"}]}

        ready, blockers = merge_readiness(pr, checks, status_payload)
        self.assertTrue(ready)
        self.assertEqual(blockers, [])

    def test_merge_readiness_blockers(self):
        pr = {"mergeable_state": "dirty", "draft": True}
        checks = [{"status": "completed", "conclusion": "failure"}]
        status_payload = {"state": "failure", "statuses": [{"context": "ci", "state": "failure"}]}

        ready, blockers = merge_readiness(pr, checks, status_payload)
        self.assertFalse(ready)
        self.assertTrue(any("draft" in blocker for blocker in blockers))
        self.assertTrue(any("dirty" in blocker for blocker in blockers))
        self.assertTrue(any("checks" in blocker for blocker in blockers))
        self.assertTrue(any("failure" in blocker for blocker in blockers))

    @patch("scripts.pr_status.SESSION")
    def test_merge_pr_success(self, mock_session):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.ok = True
        mock_resp.json.return_value = {"merged": True, "sha": "merged123"}
        mock_session.put.return_value = mock_resp

        result = merge_pr("owner/repo", 42, "headsha", method="squash", title="Merge now")

        self.assertTrue(result.get("merged"))
        mock_session.put.assert_called_once()
        args, kwargs = mock_session.put.call_args
        self.assertIn("/pulls/42/merge", args[0])
        self.assertEqual(kwargs["json"]["merge_method"], "squash")


if __name__ == "__main__":
    unittest.main()
