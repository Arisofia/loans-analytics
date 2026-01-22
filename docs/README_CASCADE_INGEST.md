
## Overview


## Secrets (GitHub Actions → Settings → Secrets)

- `CASCADE_EXPORT_URL`: the export URL the read-only view uses to download the CSV.
- `PLAYWRIGHT_BROWSERS_PATH` (optional): if you customize the Playwright cache path.
- `NOTION_TOKEN`, `GITHUB_TOKEN`: used downstream by the agents.
- `SOURCERY_TOKEN`, `SONAR_TOKEN`, `SONAR_HOST_URL`: required by the Vibe Solutioning CI gate (see `orchestration/github/workflows/vibe_quality_gate.yml`).
- `PERPLEXITY_API_KEY` or `COMET_KEY` (optional): for the public crawl manifest (`config/integrations/perplexity_comet.yaml`).
# ...existing code...


3. In GitHub Settings → Secrets → Actions, add `CASCADE_SESSION_COOKIE` with the `Bearer <token>` string you extracted and set `CASCADE_COOKIE_NAME` only if you fallback to cookie auth.
4. Add `CASCADE_EXPORT_URL` with the CSV export link that the read-only user produces (typically ends with `/export` or `/download`).
5. Keep the cookie read-only; it is only valid for a user session and the script does not require an admin API key.

## Deployment Steps (exact commands when landing the feature)

```bash
# Add the new scripts, specs, configs, docs, and workflows
git add .
gh pr create --base main \
```

## Running Locally for Production Tests

1. Install dependencies:

   ```bash
   python -m pip install --upgrade pip
   pip install pandas backoff pyarrow
   ```

   ```bash
   pip install playwright
   python -m playwright install --with-deps chromium
   ```


   ```bash
   export CASCADE_SESSION_COOKIE="<cookie value>"
   ```

3. Run the ingestion script; it now expects the export endpoint to return a ZIP file and will unpack the XLS/XLSX/CSV inside before canonicalizing:

   ```bash
     --export-url "<export_url>" \
   ```

4. If the main script encounters UI changes or you need a lightweight download for debugging, use the Plan B helper:

   ```bash
   ```
   It downloads the ZIP to `downloads/` and honors `CASCADE_COOKIE_NAME`.


## Orchestration Notes

- `python/agents/c_suite_agent.py` wireframes executive outputs using `agents/specs/c_suite_agent.yaml` and the prompt in `agents/prompts/c_suite_prompt.md`.
- The `vibe_quality_gate.yml` workflow enforces Black/Flake8/Sonar/Sourcery + tests as the CI gate for this package.

## Growth agent & risk models

- `python/agents/growth_agent.py` runs after ingest to spotlight high-potential leads, recording each run in `data/agents/growth/`.
- `analytics.v_loan_risk_drivers` (SQL defined in `sql/models/v_loan_risk_drivers.sql`) surfaces product-level roll rates so both agents and human operators can trace driver shifts.

## Logging & Audit

- Parquet and CSV outputs are saved under the prefix provided via `OUTPUT_PREFIX` and stored as artifacts for downstream consumers.

## Post-Deployment Checklist

- Confirm secrets are populated per the list above.
- Review the Prisma/Vibe gate results in `orchestration/github/workflows/vibe_quality_gate.yml` and ensure `SOURCERY_TOKEN`/`SONAR_TOKEN` are healthy.
- Verify the C-suite agent run by launching `src/agents/c_suite_agent.py --run-id <run_id> --date-range "last 30 days"` and inspect `data/agents/c_suite/`.
