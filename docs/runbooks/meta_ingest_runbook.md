# Meta Ingest Runbook

## Token Rotation
- Generate a new system user token in Meta Business Manager.
- Update the GitHub Actions secret `META_SYSTEM_USER_TOKEN`.
- Confirm the new token works by running the ingest job.

## Secrets & environment
- Ensure `META_SYSTEM_USER_TOKEN` and, if needed, `META_REFRESH_TOKEN` exist in repo Secrets before running CI.
- The Meta ingest pipeline also uses `FIGMA_TOKEN` and `SLACK_WEBHOOK_URL` when pushing summaries for marketing operations; verify these if you use the agent automations.

## Troubleshooting
- Check workflow logs for API errors or rate limits.
- Ensure all required fields and ad account IDs are present in config/integrations/meta.yaml.
- If you see 400/401 errors, verify token validity and permissions.

## Verification
- Local sanity check: run `npm install` and `npm test` inside `node/services/meta-connector` to exercise `MetaGraphClient` and ingestion helpers.
- CI runs the `Meta Integration Tests` workflow (`orchestration/github/workflows/meta_integration.yml`) on pushes/PRs touching the connector directory so regressions surface early.
- Look for expected responses under `data/raw/meta/` and the workflow artifacts/logs for any HTTP issues.

## Audit
- All ingest runs are logged in GitHub Actions and can be reviewed for failures or anomalies.
- Data is written to data/raw/meta/ and loaded to data/warehouse/fact_marketing_spend.parquet.
