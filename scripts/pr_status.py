

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_REPO = "Abaco-Technol/abaco-loans-analytics"
API_ROOT = "https://api.github.com/repos"


class GitHubRequestError(RuntimeError):
    pass


def _create_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session

SESSION = _create_session()

def _token() -> Optional[str]:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


def _headers() -> Dict[str, str]:
    headers = {"Accept": "application/vnd.github+json"}
    if token := _token():
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _get(url: str, params: Optional[Dict[str, str]] = None) -> Any:
    response = SESSION.get(url, headers=_headers(), params=params, timeout=20)
    if response.status_code == 401:
        raise GitHubRequestError("Authentication failed; set GITHUB_TOKEN or GH_TOKEN.")
    if not response.ok:
        raise GitHubRequestError(
            f"GitHub request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def _put(url: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    response = SESSION.put(url, headers=_headers(), json=payload, timeout=20)
    if response.status_code == 401:
        raise GitHubRequestError("Authentication failed; set GITHUB_TOKEN or GH_TOKEN.")
    if not response.ok:
        raise GitHubRequestError(
            f"GitHub request failed ({response.status_code}): {response.text}"
        )
    return response.json()


def list_open_prs(repo: str) -> List[int]:
    payload = _get(f"{API_ROOT}/{repo}/pulls", params={"state": "open", "per_page": "30"})
    if isinstance(payload, list):
        return [pr["number"] for pr in payload if isinstance(pr, dict) and "number" in pr]
    return []


def pull_request(repo: str, number: int) -> Dict:
    return _get(f"{API_ROOT}/{repo}/pulls/{number}")


def check_runs(repo: str, sha: str) -> List[Dict]:
    payload = _get(f"{API_ROOT}/{repo}/commits/{sha}/check-runs")
    return payload.get("check_runs", [])


def commit_status(repo: str, sha: str) -> Dict:
    return _get(f"{API_ROOT}/{repo}/commits/{sha}/status")


def merge_pr(repo: str, number: int, sha: str, method: str = "merge", title: Optional[str] = None) -> Dict:
    payload: Dict[str, Any] = {"merge_method": method, "sha": sha}
    if title:
        payload["commit_title"] = title
    return _put(f"{API_ROOT}/{repo}/pulls/{number}/merge", payload)


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
    lines.extend(
        f"- {status.get('context')}: {status.get('state')} (url={status.get('target_url')})"
        for status in sorted(statuses, key=lambda s: s.get("context", ""))
    )
    return "\n".join(lines)


def merge_readiness(
    pr: Dict, checks: List[Dict], status_payload: Dict
) -> Tuple[bool, List[str]]:
    blockers: List[str] = []
    mergeable_state = pr.get("mergeable_state")
    if pr.get("draft"):
        blockers.append("PR is marked as draft")
    if mergeable_state not in {"clean", "unstable"}:
        blockers.append(f"Mergeable state is {mergeable_state or 'unknown'}")

    conclusions = {check.get("conclusion") for check in checks if check.get("status") == "completed"}
    failing_checks = conclusions - {"success", "neutral", "skipped"}
    if failing_checks:
        blockers.append("One or more checks are not successful")

    combined_state = status_payload.get("state")
    statuses = status_payload.get("statuses", [])
    if statuses and combined_state != "success":
        blockers.append(f"Combined status is {combined_state or 'unknown'}")

    return len(blockers) == 0, blockers


def _load_pr_context(repo: str, number: int) -> Dict[str, Any]:
    pr = pull_request(repo, number)
    sha = pr.get("head", {}).get("sha")
    if not sha:
        raise GitHubRequestError("Unable to resolve head commit SHA for the pull request.")
    checks = check_runs(repo, sha)
    status_payload = commit_status(repo, sha)
    ready, blockers = merge_readiness(pr, checks, status_payload)
    return {
        "pr": pr,
        "sha": sha,
        "checks": checks,
        "status": status_payload,
        "ready_to_merge": ready,
        "blockers": blockers,
    }


def render_report(repo: str, number: int) -> str:
    context = _load_pr_context(repo, number)
    return render_report_from_context(number, context)


def render_report_from_context(number: int, context: Dict[str, Any]) -> str:
    pr = context["pr"]
    status_payload = context["status"]
    report_lines = [
        f"PR #{number}: {pr.get('title', 'untitled')}",
        f"URL: {pr.get('html_url')}",
        f"State: {pr.get('state')} | Draft: {pr.get('draft')}",
        f"Mergeable: {pr.get('mergeable_state')} (rebaseable={pr.get('rebaseable')})",
        f"Conflicts: {'yes' if pr.get('mergeable_state') == 'dirty' else 'no/unknown'}",
        "",
        "Check runs:",
        summarize_checks(context["checks"]),
        "",
        "Commit statuses:",
        summarize_statuses(status_payload.get("statuses", []), status_payload.get("state")),
        "",
        f"Ready to merge: {'yes' if context['ready_to_merge'] else 'no'}",
    ]
    if context["blockers"]:
        report_lines.append("Merge blockers:")
        report_lines.extend(f"- {reason}" for reason in context["blockers"])
    return "\n".join(report_lines)


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Report GitHub PR mergeability and check-run status.",
    )
    parser.add_argument("number", type=int, nargs="?", help="Pull request number to inspect.")
    parser.add_argument("--all", action="store_true", help="Report on all open PRs.")
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Attempt to merge PRs that are ready after reporting status.",
    )
    parser.add_argument(
        "--merge-method",
        default="merge",
        choices=["merge", "squash", "rebase"],
        help="Merge strategy to use when --merge is provided.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help=f"Repository in owner/name format (default: {DEFAULT_REPO}).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        if args.all:
            pr_numbers = list_open_prs(args.repo)
            if not pr_numbers:
                print(f"No open PRs found for {args.repo}.")
                return 0

            for num in pr_numbers:
                print(f"--- Checking PR #{num} ---")
                try:
                    context = _load_pr_context(args.repo, num)
                    print(render_report_from_context(num, context))
                    if args.merge:
                        if context["ready_to_merge"]:
                            result = merge_pr(
                                args.repo,
                                num,
                                context["sha"],
                                method=args.merge_method,
                                title=f"Merge PR #{num}: {context['pr'].get('title', 'untitled')}",
                            )
                            status = "merged" if result.get("merged") else "not merged"
                            print(f"Merge attempt: {status} (sha={result.get('sha')})")
                        else:
                            print(
                                "Merge skipped: "
                                + "; ".join(context.get("blockers") or ["No merge reasons provided."])
                            )
                except Exception as e:
                    print(f"Failed to process PR #{num} (rendering or merge): {e}")
                print("\n")
        elif args.number:
            context = _load_pr_context(args.repo, args.number)
            report = render_report_from_context(args.number, context)
            print(report)
            if args.merge:
                if not context["ready_to_merge"]:
                    print(
                        "Merge skipped: "
                        + "; ".join(context.get("blockers") or ["No merge reasons provided."])
                    )
                    return 1

                result = merge_pr(
                    args.repo,
                    args.number,
                    context["sha"],
                    method=args.merge_method,
                    title=f"Merge PR #{args.number}: {context['pr'].get('title', 'untitled')}",
                )
                print(f"Merge result: {result.get('message', 'completed')} (sha={result.get('sha')})")
        else:
            sys.stderr.write("Error: Must specify a PR number or --all.\n")
            return 1
    except GitHubRequestError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
