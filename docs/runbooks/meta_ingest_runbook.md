# Meta Ingest Runbook

## Token Rotation
- Generate a new system user token in Meta Business Manager.
- Update the GitHub Actions secret `META_SYSTEM_USER_TOKEN`.
- Confirm the new token works by running the ingest job.

## Troubleshooting
- Check workflow logs for API errors or rate limits.
- Ensure all required fields and ad account IDs are present in config/integrations/meta.yaml.
- If you see 400/401 errors, verify token validity and permissions.

## Audit
- All ingest runs are logged in GitHub Actions and can be reviewed for failures or anomalies.
- Data is written to data/raw/meta/ and loaded to data/warehouse/fact_marketing_spend.parquet.
