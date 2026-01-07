Update Playwright workflow fixer

Usage examples:

- Dry run (safe, prints preview and command):

  python scripts/update_playwright.py --input /tmp/ari_playwright.json --output /tmp/playwright_fixed.yml --dry-run

- Real update (requires GitHub CLI `gh` authenticated and a valid `sha` in the input payload):

  python scripts/update_playwright.py --input /tmp/ari_playwright.json --output /tmp/playwright_fixed.yml

Notes:
- Prefer the `--dry-run` first to verify the preview output before making changes.
- The script performs retries with exponential backoff for the `gh api` call; adjust `--retries` and `--backoff` if needed.
- For testing, import `safe_replace_on_key` from the script module to verify behavior programmatically.
