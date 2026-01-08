"""Script to run Gemini review for PRs.
This is moved out of the workflow to avoid YAML parsing issues with large inline scripts.
"""
import os
import sys
import subprocess
import logging
from typing import Optional
import requests
from requests.exceptions import RequestException

try:
    import google.generativeai as genai  # type: ignore
except ImportError:
    genai = None

logger = logging.getLogger(__name__)


def main() -> int:
    """Run Gemini PR review and post a comment on the PR. Returns exit code."""
    exit_code = 0

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("REPO_FULL_NAME")
    base_ref = os.getenv("BASE_REF")
    model_override = os.getenv("GEMINI_MODEL")

    if not github_token or not pr_number or not repo:
        logger.info("Missing GitHub context; skipping Gemini review.")
        return 0

    if not gemini_key:
        logger.info("GEMINI_API_KEY not configured; skipping AI review.")
        return 0

    if genai is None:
        logger.info("google.generativeai not installed; skipping Gemini review.")
        return 0

    # Configure the SDK if available (guard for multiple SDK versions)
    try:
        configure_fn = getattr(genai, "configure", None)
        if callable(configure_fn):
            configure_fn(api_key=gemini_key)
        else:
            logger.warning("google.generativeai.configure not available; skipping Gemini review.")
            return 0
    except Exception:
        logger.exception("Failed to configure Gemini API")
        return 1

    # Discover model
    model_name: Optional[str] = None
    if model_override:
        model_name = model_override
    else:
        try:
            list_models_fn = getattr(genai, "list_models", None)
            if callable(list_models_fn):
                for model in list_models_fn():
                    supported = getattr(model, "supported_generation_methods", None)
                    if supported and "generateContent" in supported:
                        model_name = getattr(model, "name", None)
                        break
            else:
                logger.warning("google.generativeai.list_models not available; cannot auto-detect model")
        except Exception:
            logger.exception("Could not list Gemini models")
            model_name = None

    if not model_name:
        logger.info("No compatible Gemini model found; skipping review.")
        return 0

    GenModel = getattr(genai, "GenerativeModel", None)
    if GenModel is None:
        logger.error("google.generativeai.GenerativeModel not available; skipping review.")
        return 0

    try:
        model = GenModel(model_name)
    except Exception:
        logger.exception("Failed to create GenerativeModel")
        return 1

    # Get diff using git
    try:
        result = subprocess.run(
            ["git", "diff", f"origin/{base_ref}", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        diff = result.stdout
    except subprocess.CalledProcessError:
        logger.exception("Error getting diff from git")
        return 1

    if not diff.strip():
        logger.info("No changes to review")
        return 0

    # Create prompt for Gemini
    prompt = f"""Review this pull request diff and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Security concerns
4. Performance improvements
5. General suggestions

Diff:
{diff[:8000]}
"""

    try:
        response = model.generate_content(prompt)
        review_comment = getattr(response, "text", str(response))
    except Exception:
        logger.exception("Error calling Gemini API")
        return 1

    # Post comment to PR (use a short timeout to avoid hanging)
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"body": f"## 🤖 Gemini AI Review\n\n{review_comment}"}

    try:
        resp = requests.post(api_url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        logger.info("Review posted successfully")
    except RequestException:
        logger.exception("Failed to post review")
        exit_code = 1

    return exit_code


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
