# Reviewer Checklist

- [ ] All Python tests pass (`python -m pytest`)
- [ ] Cascade ingest workflow runs successfully in GitHub Actions
- [ ] All required secrets are set in the repository:
  - `CASCADE_SESSION_COOKIE`
  - `AZURE_STORAGE_CONNECTION_STRING`
  - `SLACK_WEBHOOK_URL`
  - etc.
- [ ] Parquet and other artifacts are generated and uploaded as expected
- [ ] Slack or other notifications are received (if configured)
- [ ] Code and documentation changes are clear and complete
