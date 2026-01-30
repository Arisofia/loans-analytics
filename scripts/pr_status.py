#!/usr/bin/env python3
"""
PR Status Report Script

Generates a summary of open pull requests in the repository.
Used by the PR Monitor workflow.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime


def run_gh_command(args: list[str]) -> dict | list | None:
    """Run a GitHub CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout) if result.stdout.strip() else None
    except subprocess.CalledProcessError as e:
        print(f"Error running gh command: {e.stderr}", file=sys.stderr)
        return None
    except json.JSONDecodeError:
        return None


def get_open_prs() -> list[dict]:
    """Get all open pull requests."""
    prs = run_gh_command([
        "pr", "list",
        "--state", "open",
        "--json", "number,title,author,createdAt,updatedAt,isDraft,labels,reviewDecision,url"
    ])
    return prs or []


def format_pr_report(prs: list[dict]) -> str:
    """Format pull requests into a readable report."""
    if not prs:
        return "✅ No open pull requests"

    lines = [
        f"📊 **PR Status Report** - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}",
        f"Total open PRs: {len(prs)}",
        "",
    ]

    # Categorize PRs
    drafts = [pr for pr in prs if pr.get("isDraft")]
    ready = [pr for pr in prs if not pr.get("isDraft")]
    needs_review = [pr for pr in ready if pr.get("reviewDecision") not in ("APPROVED", "CHANGES_REQUESTED")]
    approved = [pr for pr in ready if pr.get("reviewDecision") == "APPROVED"]
    changes_requested = [pr for pr in ready if pr.get("reviewDecision") == "CHANGES_REQUESTED"]

    if approved:
        lines.append("### ✅ Approved & Ready to Merge")
        for pr in approved:
            lines.append(f"  - #{pr['number']}: {pr['title']} (@{pr['author']['login']})")
        lines.append("")

    if changes_requested:
        lines.append("### 🔄 Changes Requested")
        for pr in changes_requested:
            lines.append(f"  - #{pr['number']}: {pr['title']} (@{pr['author']['login']})")
        lines.append("")

    if needs_review:
        lines.append("### 👀 Needs Review")
        for pr in needs_review:
            lines.append(f"  - #{pr['number']}: {pr['title']} (@{pr['author']['login']})")
        lines.append("")

    if drafts:
        lines.append("### 📝 Drafts")
        for pr in drafts:
            lines.append(f"  - #{pr['number']}: {pr['title']} (@{pr['author']['login']})")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate PR status report")
    parser.add_argument("--all", action="store_true", help="Show all PRs (default behavior)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Check if gh CLI is available
    if not os.environ.get("GITHUB_TOKEN") and not os.path.exists(os.path.expanduser("~/.config/gh/hosts.yml")):
        print("::notice::GitHub CLI not authenticated - skipping PR monitor")
        sys.exit(0)

    prs = get_open_prs()

    if args.json:
        print(json.dumps(prs, indent=2))
    else:
        report = format_pr_report(prs)
        print(report)

    # Summary for GitHub Actions
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(format_pr_report(prs))


if __name__ == "__main__":
    main()
