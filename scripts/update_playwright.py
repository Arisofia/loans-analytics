#!/usr/bin/env python3
"""
Playwright Workflow Quoting Fixer.

This script automates the correction of quoted `"on":` keys to `on:` in
GitHub Actions YAML files via the GitHub API. This is necessary to avoid
YAML validation issues while ensuring CI pipeline integrity.

Standards:
- PEP 8 compliant
- Type-safe (mypy verified)
- Robust error handling and retries
- Detailed logging for traceability
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Tuple

# Configuration Defaults
DEFAULT_INPUT = "/tmp/ari_playwright.json"
DEFAULT_OUT = "/tmp/playwright_fixed.yml"
DEFAULT_REPO = "Arisofia/abaco-loans-analytics"
DEFAULT_REPO_PATH = ".github/workflows/playwright.yml"
DEFAULT_BRANCH = "chore/ci-pipeline-integrity"
DEFAULT_MESSAGE = 'fix(workflows): correct quoted "on" key in Playwright workflow'
MAX_RETRIES = 3
RETRY_DELAY = 2.0


def safe_replace_on_key(content: str) -> Tuple[str, int]:
    """
    Replace only quoted "on" keys that appear at start of line.

    Args:
        content: The raw YAML content.

    Returns:
        A tuple containing (modified_content, count_of_replacements).
    """
    # Pattern: Line start, optional whitespace, "on", then colon
    pattern = re.compile(r'(?m)^[ \t]*"on"\s*:')
    return pattern.subn(lambda m: m.group(0).replace('"on"', "on"), content)


def fix_content(content_b64: str) -> Tuple[str, int]:
    """
    Decode base64 content, fix top-level quoted "on" keys, and return
    the fixed content (decoded) and number of replacements.

    Args:
        content_b64: Base64-encoded YAML content.

    Returns:
        Tuple of (fixed_content_str, replacements_count)
    """
    raw = base64.b64decode(content_b64).decode("utf-8")
    new_content, count = safe_replace_on_key(raw)
    return new_content, count


def run_gh_update(
    repo: str,
    repo_path: str,
    payload: Dict[str, str],
    retries: int = MAX_RETRIES,
    backoff: float = RETRY_DELAY,
) -> subprocess.CompletedProcess:
    """
    Call `gh api` to update the file contents with retry logic.

    Args:
        repo: Repository name (org/repo).
        repo_path: Path to the file in the repository.
        payload: Dictionary containing message, content, sha, and branch.
        retries: Number of retry attempts on failure.
        backoff: Seconds to wait between retries.

    Returns:
        The completed process object.

    Raises:
        subprocess.CalledProcessError: If the command fails after all retries.
    """
    url = f"/repos/{repo}/contents/{repo_path}"
    cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        url,
        "-f",
        f"message={payload['message']}",
        "-f",
        f"content={payload['content']}",
        "-f",
        f"sha={payload['sha']}",
        "-f",
        f"branch={payload['branch']}",
    ]

    for attempt in range(retries):
        try:
            logging.debug("Running GH API (Attempt %d/%d)", attempt + 1, retries)
            return subprocess.run(cmd, check=True, capture_output=True, text=True, shell=False)
        except subprocess.CalledProcessError:
            if attempt == retries - 1:
                raise
            logging.warning("API call failed, retrying in %.1fs...", backoff)
            time.sleep(backoff)

    raise RuntimeError("Unexpected failure in retry logic")


def parse_args(argv=None) -> argparse.Namespace:
    """Parse and return command-line arguments."""
    p = argparse.ArgumentParser(description="Safely fix quoted 'on' keys in GitHub Workflows")
    p.add_argument("--input", default=DEFAULT_INPUT, help="Path to input JSON")
    # Accept both --out and --output for compatibility with tests and users
    p.add_argument(
        "--out",
        "--output",
        dest="out",
        default=DEFAULT_OUT,
        help="Path to write preview",
    )
    p.add_argument("--repo", default=DEFAULT_REPO, help="Target repository")
    p.add_argument("--path", default=DEFAULT_REPO_PATH, help="Workflow path")
    p.add_argument("--branch", default=DEFAULT_BRANCH, help="Target branch")
    p.add_argument("--message", default=DEFAULT_MESSAGE, help="Commit message")
    p.add_argument("--dry-run", action="store_true", help="Preview mode")
    p.add_argument("--preview-lines", type=int, default=15, help="Lines to preview")
    p.add_argument("--retries", type=int, default=MAX_RETRIES, help="Number of GH API retries")
    p.add_argument(
        "--backoff",
        type=float,
        default=RETRY_DELAY,
        help="Backoff seconds between retries",
    )
    return p.parse_args(argv)


def main(argv=None) -> int:
    """
    Main entry point for the workflow fixer script.

    Args:
        argv: Optional list of command-line arguments (for tests).

    Returns:
        Exit code: 0 for success, non-zero for errors.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    args = parse_args(argv)
    in_path, out_path = Path(args.input), Path(args.out)

    if not in_path.exists():
        logging.error("Required input file %s not found", in_path)
        return 2

    exit_code = 0
    try:
        data = json.loads(in_path.read_text(encoding="utf-8"))
        content_b64, sha = data.get("content"), data.get("sha")

        if not content_b64 or not sha:
            logging.error("Input JSON must contain 'content' and 'sha'")
            return 2

        content = base64.b64decode(content_b64).decode("utf-8")
        new_content, replacements = safe_replace_on_key(content)
        out_path.write_text(new_content, encoding="utf-8")

        print(f"\n--- Preview (First {args.preview_lines} lines) ---")
        print("\n".join(new_content.splitlines()[: args.preview_lines]))
        print("-------------------------------------------\n")

        if replacements == 0:
            logging.info("Repository is already correct")
        elif args.dry_run:
            logging.info("Dry-run mode: No changes pushed")
        else:
            b64new = base64.b64encode(new_content.encode("utf-8")).decode("ascii")
            payload = {
                "message": args.message,
                "content": b64new,
                "sha": sha,
                "branch": args.branch,
            }
            res = run_gh_update(
                args.repo,
                args.path,
                payload,
                retries=args.retries,
                backoff=args.backoff,
            )
            logging.info("Success: %s", (res.stdout or "OK")[:200])

    except json.JSONDecodeError as exc:
        logging.error("Invalid JSON: %s", exc)
        exit_code = 2
    except FileNotFoundError:
        logging.error("'gh' tool not found")
        exit_code = 3
    except subprocess.CalledProcessError as exc:
        logging.error("API failed (Exit %s): %s", exc.returncode, exc.stderr)
        exit_code = 4
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logging.error("Unexpected error: %s", exc)
        exit_code = 2

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
