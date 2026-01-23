# Runbook: Deployment Blocked (GitHub Actions / Azure)

**Symptoms**

- Deploy workflows fail (syntax errors, missing secrets, auth failures).
- Azure deploy step completes but health check fails.

**Primary goals**

1. Restore deploy capability (CI green).
2. Ensure deployment targets the correct hostname.
3. Confirm post-deploy health check is meaningful.

## Triage (5–15 minutes)

1) **Confirm which deploy path is failing**

- Streamlit dashboard deploy: `.github/workflows/deploy-dashboard.yml`
- Web deploy: `apps/web/.github/workflows/deploy-*.yml`

1) **Check the failure category**

- Workflow syntax / action reference errors
- Missing secrets (publish profile / Azure creds)
- Azure auth failures
- Health check aimed at wrong host/path

1) **Confirm required secrets exist**
Typical deploy secrets:

- `AZURE_WEBAPP_PUBLISH_PROFILE` (App Service deploy)
- `AZURE_CREDENTIALS` (Azure CLI config steps)
- `AZURE_STATIC_WEB_APPS_TOKEN_*` (SWA deploy)

Quick validation:

- Run `python scripts/validate_secrets.py --presence-only`, or
- Run the GitHub Actions workflow **Verify Secrets and Integrations**.

## Decision flow

```mermaid
flowchart TD
  A[Deployment failed] --> B{Workflow syntax/action reference error?}
  B -->|Yes| C[Fix YAML; ensure actions versions exist; rerun]
  B -->|No| D{Missing secret?}
  D -->|Yes| E[Add secret; rerun]
  D -->|No| F{Azure login/auth failed?}
  F -->|Yes| G[Validate AZURE_CREDENTIALS/service principal permissions; rerun]
  F -->|No| H{Deploy succeeded but health check failed?}
  H -->|Yes| I[Resolve real hostname (defaultHostName) and correct health check path]
  H -->|No| J[Inspect app runtime logs (App Service) or SWA logs; escalate]
```

## Evidence to capture

- Workflow run URL + failing step output.
- Target resource name + resource group.
- Health check URL that was tested.

## Common fixes

- **Wrong health check host**: use App Service `defaultHostName` via Azure CLI (or a secret override) instead of assuming `https://<name>.azurewebsites.net`.
- **Secrets unavailable on PRs from forks**: guard deploy jobs to only run on `push` to `main` and/or internal PRs.
- **Action version doesn’t exist**: use a known major (e.g., `actions/setup-node@v4`).
- **Publish profile missing**: ensure SCM/FTP basic auth is enabled for the App Service, then regenerate `AZURE_WEBAPP_PUBLISH_PROFILE`.
- **azure/webapps-deploy: No credentials found**: confirm `AZURE_WEBAPP_PUBLISH_PROFILE` is set and non-empty in repo secrets; otherwise add an `azure/login` step with `AZURE_CREDENTIALS`.

## Follow-up hardening

- Add a `workflow_dispatch` path so you can redeploy manually.
- Add a single “Validate deployment” job that curls the correct host and reports status.
