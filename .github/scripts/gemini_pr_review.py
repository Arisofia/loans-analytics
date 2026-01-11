"""Script to run Gemini review for PRs.
This is moved out of the workflow to avoid YAML parsing issues with large inline scripts.
"""

import os
import sys
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def require_env_vars(*vars):
    missing = [v for v in vars if not os.getenv(v)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        return False
    return True

def require_module(modname):
    try:
        return __import__(modname)
    except ImportError:
        logger.error(f"Required module '{modname}' not installed; skipping Gemini review.")
        return None



def main() -> int:
    """Run Gemini PR review and post a comment on the PR. Returns exit code."""
    # Validate required environment variables
    if not require_env_vars("GITHUB_TOKEN", "GEMINI_API_KEY", "PR_NUMBER", "REPO_FULL_NAME", "BASE_REF"):
        return 0

    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("REPO_FULL_NAME")
    base_ref = os.getenv("BASE_REF")
    model_override = os.getenv("GEMINI_MODEL")

    # Dependency checks
    genai = require_module("google.generativeai")
    if genai is None:
        return 0
    requests_mod = require_module("requests")
    if requests_mod is None:
        return 0
    RequestException = getattr(requests_mod, "exceptions", requests_mod).__dict__.get("RequestException", Exception)

    # Configure Gemini API
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
    model_name: Optional[str] = model_override
    if not model_name:
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

    # Limit diff size for Gemini API
    max_diff_len = 8000
    safe_diff = diff[:max_diff_len]

    prompt = (
        "Review this pull request diff and provide feedback on:\n"
        "1. Code quality and best practices\n"
        "2. Potential bugs or issues\n"
        "3. Security concerns\n"
        "4. Performance improvements\n"
        "5. General suggestions\n\n"
        f"Diff:\n{safe_diff}\n"
    )

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
        resp = requests_mod.post(api_url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
        logger.info("Review posted successfully")
    except RequestException:
        logger.exception("Failed to post review")
        return 1

    return 0



if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
