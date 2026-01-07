"""Update Playwright workflow content safely via GitHub API.

This script reads an input JSON payload (like the GitHub content API result),
fixes the quoted `"on":` key to `on:` in YAML content when present, writes a
preview file, and updates the repository via `gh api`.

Features:
- CLI with configurable input/output path, branch, message, dry-run and retries
- Input validation and explicit encoding
- Exponential backoff retries for the `gh api` call
- Logging for traceability
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import subprocess
import sys
import time
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional


logger = logging.getLogger(__name__)


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Safely fix Playwright workflow 'on' quoting and push via gh API")
    p.add_argument("--input", default="/tmp/ari_playwright.json", help="Path to input JSON (content + sha)")
    p.add_argument("--output", default="/tmp/playwright_fixed.yml", help="Path to write preview fixed YAML")
    p.add_argument("--branch", default="chore/ci-pipeline-integrity", help="Target branch for the update")
    p.add_argument("--message", default="fix(workflows): correct quoted \"on\" key in Playwright workflow", help="Commit message")
    p.add_argument("--dry-run", action="store_true", help="Don't call gh api, just write preview and print command")
    p.add_argument("--retries", type=int, default=3, help="Number of retries for gh api calls")
    p.add_argument("--backoff", type=float, default=1.0, help="Initial backoff seconds, doubled each retry")
    return p.parse_args(list(argv) if argv else None)


def load_input(input_path: Path) -> Dict:
    logger.debug('Loading input JSON from %s', input_path)
    with input_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def safe_replace_on_key(content: str) -> tuple[str, int]:
    """Replace only quoted "on" keys that appear at the start of a YAML key line.

    Returns a tuple of (new_content, replacements_count).
    Uses a multiline regex anchored to line starts to avoid accidental matches inside
    strings or values.
    """
    pattern = re.compile(r'(?m)^[ \t]*"on"\s*:')

    def _repl(m: re.Match) -> str:
        text = m.group(0)
        # Replace the quoted key with an unquoted key while preserving indentation and colon
        return text.replace('"on"', 'on')

    new, n = pattern.subn(_repl, content)
    return new, n


def fix_content(content_b64: str) -> tuple[str, int]:
    content = base64.b64decode(content_b64).decode("utf-8")
    new, n = safe_replace_on_key(content)
    if n == 0:
        logger.info('Pattern "\"on\":" not found at top-level key positions; nothing to change')
    return new, n


def write_preview(out_path: Path, content: str) -> None:
    logger.debug('Writing preview to %s', out_path)
    with out_path.open("w", encoding="utf-8") as ofh:
        ofh.write(content)


def build_gh_command(content_b64: str, sha: str, message: str, branch: str) -> List[str]:
    # Use gh api to PUT content
    cmd = [
        "gh",
        "api",
        "-X",
        "PUT",
        "/repos/Arisofia/abaco-loans-analytics/contents/.github/workflows/playwright.yml",
        "-f",
        f"message={message}",
        "-f",
        f"content={content_b64}",
        "-f",
        f"sha={sha}",
        "-f",
        f"branch={branch}",
    ]
    return cmd


def run_with_retries(cmd: List[str], retries: int = 3, backoff: float = 1.0) -> subprocess.CompletedProcess:
    attempt = 0
    while True:
        attempt += 1
        logger.debug('Running command (attempt %d): %s', attempt, cmd)
        try:
            out = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.debug('Command succeeded: %s', out.stdout[:400])
            return out
        except subprocess.CalledProcessError as exc:
            logger.warning('Command failed (attempt %d/%d): %s', attempt, retries, exc)
            if attempt >= retries:
                logger.error('Giving up after %d attempts', attempt)
                raise
            sleep = backoff * (2 ** (attempt - 1))
            logger.info('Retrying after %.1fs...', sleep)
            time.sleep(sleep)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error('Input file does not exist: %s', input_path)
        return 2

    payload = load_input(input_path)
    content_b64 = payload.get('content')
    sha = payload.get('sha')

    if not content_b64 or not sha:
        logger.error('Input JSON missing "content" or "sha" key')
        return 3

    new, replacements = fix_content(content_b64)
    write_preview(Path(args.output), new)

    if replacements == 0:
        logger.info('No top-level quoted "on" keys found; exiting without calling GH')
        return 0

    # Prepare API payload
    b64new = base64.b64encode(new.encode('utf-8')).decode('ascii')
    cmd = build_gh_command(b64new, sha, args.message, args.branch)

    logger.info('Prepared gh api command (dry_run=%s)', args.dry_run)
    if args.dry_run:
        logger.info('Dry run - command: %s', ' '.join(cmd))
        return 0

    try:
        run_with_retries(cmd, retries=args.retries, backoff=args.backoff)
        logger.info('Update completed successfully')
        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - log and exit non-zero
        logger.exception('Update failed: %s', exc)
        exit_code = 1
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
