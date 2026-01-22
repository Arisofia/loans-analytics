import os

import google.generativeai as genai
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")


def get_pr_diff():
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.diff",
    }
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text


def get_gemini_review(diff):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Actúa como experto DevSecOps. Revisa este diff de PR. Identifica bugs críticos o problemas de seguridad. Sé conciso. DIFF:\n{diff[:30000]}"
    response = model.generate_content(prompt)
    return response.text


def post_comment(comment):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    data = {"body": f"## 🤖 Gemini Code Review\n\n{comment}"}
    requests.post(url, headers=headers, json=data).raise_for_status()


if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("No GEMINI_API_KEY found.")
        exit(0)
    try:
        diff = get_pr_diff()
        review = get_gemini_review(diff)
        post_comment(review)
        print("Review posted successfully.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
