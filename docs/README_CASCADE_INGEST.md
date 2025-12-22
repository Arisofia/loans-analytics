# Cascade Ingestion Runbook

## Overview
- Runs daily at 03:00 UTC via `orchestration/github/workflows/cascade_ingest.yml` with strict logging, retries, and audit manifests under `data/audit/runs/`.
- Uses Playwright with a read-only session cookie to fetch the Cascade export, then canonicalizes the loan tape via `python/ingest/transform.py` before persisting CSV and Parquet.
- The C-suite agent relies on this data to regenerate executive summaries, slide decks, and Slack alerts after each run.

## Secrets (GitHub Actions → Settings → Secrets)
- `CASCADE_SESSION_COOKIE`: the read-only user session cookie captured from Cascade (see section below).
- `CASCADE_EXPORT_URL`: the export URL the read-only view uses to download the CSV.
- `SLACK_WEBHOOK_INGEST`: Slack webhook used by the success notifier.
- `PLAYWRIGHT_BROWSERS_PATH` (optional): if you customize the Playwright cache path.
- `FIGMA_TOKEN`, `NOTION_TOKEN`, `GITHUB_TOKEN`: used downstream by the agents.
- `SOURCERY_TOKEN`, `SONAR_TOKEN`, `SONAR_HOST_URL`: required by the Vibe Solutioning CI gate (see `orchestration/github/workflows/vibe_quality_gate.yml`).
- `PERPLEXITY_API_KEY` or `COMET_KEY` (optional): for the public crawl manifest (`config/integrations/perplexity_comet.yaml`).
- `SLACK_WEBHOOK_OPS`: for the growth/lead notifications if configured.

## Adding the Cascade Session Cookie
1. Log in with the read-only Cascade user and open DevTools → Application → Cookies → `cascadedebt.com`.
2. Copy the `session` cookie value.
3. In GitHub Settings → Secrets → Actions, add `CASCADE_SESSION_COOKIE` and paste the cookie value.
4. Add `CASCADE_EXPORT_URL` with the CSV export link that the read-only user produces (typically ends with `/export` or `/download`).
5. Keep the cookie read-only; it is only valid for a user session and the script does not require an admin API key.

## Deployment Steps (exact commands when landing the feature)
```bash
git checkout -b feature/cascade-ingest
# Add the new scripts, specs, configs, docs, and workflows
git add .
git commit -S -m "feat(cascade): automated Cascade ingestion + C-suite agent (v1)"
git push origin feature/cascade-ingest
gh pr create --base main \
  --head feature/cascade-ingest \
  --title "feat(cascade): automated Cascade ingestion + C-suite agent (v1)" \
  --body "Adds production Cascade ingestion pipeline, daily orchestration, data validation and KPI baseline generation. See README_CASCADE_INGEST.md for deployment details."
```

## Running Locally for Production Tests
1. Install dependencies:
   ```bash
   python -m pip install --upgrade pip
   pip install pandas playwright backoff pyarrow
   playwright install chromium
   ```
2. Export the Cascade session cookie locally:
   ```bash
   export CASCADE_SESSION_COOKIE="<cookie value>"
   ```
3. Run the ingestion script:
   ```bash
   python3 scripts/cascade_ingest.py \
     --export-url "<export_url>" \
     --output-prefix "data/raw/cascade/loan_tapes/202601/loan_tape_full"
   ```
4. Review `data/raw/cascade/loan_tapes/` for the CSV/Parquet output and `data/audit/runs/cascade_ingest_run_<run_id>.json` for the tracked manifest.

## Orchestration Notes
- `orchestration/github/workflows/cascade_ingest.yml` installs Playwright, runs the script, uploads the Parquet artifact, and notifies Slack on success.
- `python/agents/c_suite_agent.py` wireframes executive outputs using `agents/specs/c_suite_agent.yaml` and the prompt in `agents/prompts/c_suite_prompt.md`.
- The `vibe_quality_gate.yml` workflow enforces Black/Flake8/Sonar/Sourcery + tests as the CI gate for this package.

## Growth agent & risk models
- `python/agents/growth_agent.py` runs after ingest to spotlight high-potential leads, recording each run in `data/agents/growth/`.
- `analytics.v_loan_risk_drivers` (SQL defined in `sql/models/v_loan_risk_drivers.sql`) surfaces product-level roll rates so both agents and human operators can trace driver shifts.

## Logging & Audit
- Each run writes `data/audit/runs/cascade_ingest_run_<run_id>.json` to capture inputs, outputs, and a hash of the session secret for compliance.
- Parquet and CSV outputs are saved under the prefix provided via `OUTPUT_PREFIX` and stored as artifacts for downstream consumers.

## Post-Deployment Checklist
- Confirm secrets are populated per the list above.
- Validate that the Cascade export URL still returns the expected CSV format; update selectors if the UI changes.
- Review the Prisma/Vibe gate results in `orchestration/github/workflows/vibe_quality_gate.yml` and ensure `SOURCERY_TOKEN`/`SONAR_TOKEN` are healthy.
- Verify the C-suite agent run by launching `python/agents/c_suite_agent.py --run-id <run_id> --date-range "last 30 days"` and inspect `data/agents/c_suite/`.
