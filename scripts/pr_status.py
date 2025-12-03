from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional

import requests

DEFAULT_REPO = "Abaco-Technol/abaco-loans-analytics"
API_ROOT = "https://api.github.com/repos"


class GitHubRequestError(RuntimeError):
    pass


def _token() -> Optional[str]:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


def _headers() -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token := _token():
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, params: Optional[Dict[str, str]] = None) -> Dict:
    response = requests.get(url, headers=_headers(), params=params, timeout=20)
    if response.status_code == 401:
        raise GitHubRequestError("Authentication failed; set GITHUB_TOKEN or GH_TOKEN.")
    if not response.ok:
        raise GitHubRequestError(
            f"GitHub request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def pull_request(repo: str, number: int) -> Dict:
    return _get(f"{API_ROOT}/{repo}/pulls/{number}")


def check_runs(repo: str, sha: str) -> List[Dict]:
    payload = _get(f"{API_ROOT}/{repo}/commits/{sha}/check-runs")
    return payload.get("check_runs", [])


def commit_status(repo: str, sha: str) -> Dict:
    return _get(f"{API_ROOT}/{repo}/commits/{sha}/status")


def summarize_checks(checks: List[Dict]) -> str:
    if not checks:
        return "No check runs reported."
    lines = []
    for check in sorted(checks, key=lambda c: c.get("name", "")):
        status = check.get("status", "unknown")
        conclusion = check.get("conclusion") or "pending"
        lines.append(
            f"- {check.get('name')}: {status}/{conclusion} (url={check.get('html_url')})"
        )
    return "\n".join(lines)


def summarize_statuses(statuses: List[Dict], state: str) -> str:
    if not statuses:
        return f"Combined state: {state or 'unknown'} (no individual statuses)."
    lines = [f"Combined state: {state or 'unknown'}"]
    for status in sorted(statuses, key=lambda s: s.get("context", "")):
        lines.append(
            f"- {status.get('context')}: {status.get('state')} (url={status.get('target_url')})"
        )
    return "\n".join(lines)


def render_report(repo: str, number: int) -> str:
    pr = pull_request(repo, number)
    sha = pr.get("head", {}).get("sha")
    if not sha:
        raise GitHubRequestError("Unable to resolve head commit SHA for the pull request.")

    checks = check_runs(repo, sha)
    status_payload = commit_status(repo, sha)
    report_lines = [
        f"PR #{number}: {pr.get('title', 'untitled')}",
        f"URL: {pr.get('html_url')}",
        f"State: {pr.get('state')} | Draft: {pr.get('draft')}",
        f"Mergeable: {pr.get('mergeable_state')} (rebaseable={pr.get('rebaseable')})",
        f"Conflicts: {'yes' if pr.get('mergeable_state') == 'dirty' else 'no/unknown'}",
        "",
        "Check runs:",
        summarize_checks(checks),
        "",
        "Commit statuses:",
        summarize_statuses(status_payload.get("statuses", []), status_payload.get("state")),
    ]
    return "\n".join(report_lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report GitHub PR mergeability and check-run status.",
    )
    parser.add_argument("number", type=int, help="Pull request number to inspect.")
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"Repository in owner/name format (default: {DEFAULT_REPO}).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        report = render_report(args.repo, args.number)
    except GitHubRequestError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
