"""Script to run Gemini review for PRs.
This is moved out of the workflow to avoid YAML parsing issues with large inline scripts.
"""
import os
import sys
import subprocess
import requests

try:
    import google.generativeai as genai
except Exception:
    genai = None


def main() -> int:
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_key = os.getenv("GEMINI_API_KEY")
    pr_number = os.getenv("PR_NUMBER")
    repo = os.getenv("REPO_FULL_NAME")
    base_ref = os.getenv("BASE_REF")
    model_override = os.getenv("GEMINI_MODEL")

    if not github_token or not pr_number or not repo:
        print("Missing GitHub context; skipping Gemini review.")
        return 0

    if not gemini_key:
        print("GEMINI_API_KEY not configured; skipping AI review.")
        return 0

    if genai is None:
        print("google-generativeai not installed; skipping Gemini review.")
        return 0

    genai.configure(api_key=gemini_key)

    model_name = None
    if model_override:
        model_name = model_override
    else:
        try:
            for model in genai.list_models():
                if hasattr(model, "supported_generation_methods") and "generateContent" in model.supported_generation_methods:
                    model_name = model.name
                    break
        except Exception as e:
            print(f"Could not list Gemini models: {e}")
            model_name = None

    if not model_name:
        print("No compatible Gemini model found; skipping review.")
        return 0

    model = genai.GenerativeModel(model_name)

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
        print(f"Error getting diff: {e}")
        return 1

    if not diff.strip():
        print("No changes to review")
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
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return 0

    # Post comment to PR
    api_url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    }
    data = {"body": f"## 🤖 Gemini AI Review\n\n{review_comment}"}

    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 201:
        print("Review posted successfully")
        return 0
    else:
        print(f"Failed to post review: {response.status_code} {response.text}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
