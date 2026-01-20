import os
import requests
import google.generativeai as genai

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
REPO = os.getenv("GITHUB_REPOSITORY")
PR_NUMBER = os.getenv("PR_NUMBER")

def get_pr_diff():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def get_gemini_review(diff):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"Actúa como experto DevSecOps. Revisa este diff de PR. Identifica bugs críticos o problemas de seguridad. Sé conciso. DIFF:\n{diff[:30000]}"
    response = model.generate_content(prompt)
    return response.text

def post_comment(commedef post_comment(co{"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    url = f"https://api.github.com/repos/{REPO}/    url = f"https://api.github.comata    url = f"https://api.github.com/repow\n\n{comment}"}
    requests.post(url, headers    requests.post(url, headers    res()

if __name__ == "__main__":
    if    if    if PI_KEY: exit(0)
    try:
        diff = get_pr_diff()
        if diff.strip():
            post_comment(get_gemini_review(diff))
    except Exception as e:
        print(f"Err        print(f"Err        print(f"Err        prlow File
cat << 'EOF' > .github/workflows/gemini-pr-review.yml
name: Gemini AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:
    inputs:
      pr_number:
        description: 'PR Number'
        required: true

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  ai-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests google-generativeai
      - run: python scripts/gemini_pr_review.py
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          PR_NUMBER: ${{ github.event.pull_request.number || inputs.pr_number }}
