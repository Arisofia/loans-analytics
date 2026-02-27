"""Script to run Gemini review for PRs.

This is moved out of the workflow to avoid YAML parsing issues with
large inline scripts.
"""

import importlib
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)


def require_env_vars(*env_vars: str) -> bool:
    """Check that all required environment variables are set."""
    missing = [v for v in env_vars if not os.getenv(v)]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        return False
    return True


def require_module(modname: str):
    """Dynamically import a module and return it, or None if not available."""
    try:
        return importlib.import_module(modname)
    except ImportError:
        logger.warning("Required module '%s' not installed; skipping review.", modname)
        return None


def main() -> int:
    """Run Gemini PR review and post a comment on the PR. Returns exit code."""
    # Validate required environment variables
    if not require_env_vars(
        "GITHUB_TOKEN", "GEMINI_API_KEY", "PR_NUMBER", "REPO_FULL_NAME", "BASE_REF"
    ):
        return 0

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("REPO_FULL_NAME")
    base_ref = os.getenv("BASE_REF")
    model_override = os.getenv("GEMINI_MODEL")

    # Dependency checks
    genai = require_module("google.genai")
    if genai is None:
        return 0

    requests_mod = require_module("requests")
    if requests_mod is None:
        return 0

    request_exception = getattr(
        getattr(requests_mod, "exceptions", None), "RequestException", Exception
    )

    # Configure Gemini API client
    try:
        client = genai.Client(api_key=gemini_key)
    except Exception as e:  # pragma: no cover - defensive for SDK/runtime differences
        logger.exception("Failed to configure Gemini API: %s", e)
        return 1

    model_name = model_override or "gemini-2.5-flash"
    if model_override is None:
        logger.info("No GEMINI_MODEL provided; using default model: %s", model_name)

    # Get diff using git
    try:
        result = subprocess.run(
            ["git", "diff", f"origin/{base_ref}", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        diff = result.stdout
    except subprocess.CalledProcessError as e:
        logger.exception("Error getting diff from git: %s", e.stderr)
        return 1

    if not diff.strip():
        logger.info("No changes to review")
        return 0

    # Limit diff size for Gemini API
    max_diff_len = 8000
    safe_diff = diff[:max_diff_len]

    prompt = (
        "Review this pull request diff and provide feedback on:\n"
        "1. Code quality and best practices\n"
        "2. Potential bugs or issues\n"
        "3. Security concerns\n"
        "4. Performance considerations\n"
        "5. General suggestions\n\n"
        f"Diff:\n{safe_diff}\n"
    )

    try:
        response = client.models.generate_content(model=model_name, contents=prompt)
        review_comment = getattr(response, "text", str(response))
    except (ImportError, ValueError, RuntimeError) as e:
        logger.exception("Error calling Gemini API: %s", e)
        return 1
    except TypeError as e:
        logger.exception("Invalid argument to Gemini API: %s", e)
        return 1

    # Post comment to PR
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"body": f"## 🤖 Gemini AI Review\n\n{review_comment}"}

    try:
        resp = requests_mod.post(api_url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        logger.info("Review posted successfully")
    except request_exception:
        logger.exception("Failed to post review")
        return 1

    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
