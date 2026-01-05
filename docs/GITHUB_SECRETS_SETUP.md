# GitHub Secrets Setup (Abaco Loans Analytics)

This guide lists the **exact GitHub Actions secrets** referenced by workflows in this repository, and where each is used.

**Rules**

- Never paste secret values into PRs/issues/logs.
- Prefer **Repository secrets** for shared production workflows.
- For environment separation, use *distinct* secrets for staging vs production (already supported by `apps/web` workflows).
- If using GitHub CLI, ensure your token has permission to manage Actions secrets.

## Quick-start (minimum for “core operations”)

If you only do one pass, start with these:

- `AZURE_WEBAPP_PUBLISH_PROFILE` (dashboard deploy)
- `AZURE_CREDENTIALS` (dashboard deploy config + hostname resolution)
- `DATABASE_URL` (KPI parity + pipeline DB writes)
- `OPENAI_API_KEY` (multiple analytics/agent workflows)

## Managing secrets via GitHub CLI

Recommended scopes for `gh secret set`:

- `repo`
- `workflow`

If you see `Resource not accessible by personal access token`:

1. Refresh token scopes:

```bash
gh auth refresh -s repo,workflow
```

1. If the repo is in an org with SSO, authorize the token for that org.

2. Retry with an explicit repo target:

```bash
gh secret set <NAME> --repo <OWNER>/<REPO>
```

## Secrets by component

### A) Azure App Service “Dashboard” (Streamlit)

Used by `.github/workflows/deploy-dashboard.yml`.

- `AZURE_WEBAPP_PUBLISH_PROFILE`
  - Purpose: Deploy the Streamlit dashboard package to Azure App Service.
  - Where: GitHub → Settings → Secrets and variables → Actions.

- `AZURE_CREDENTIALS`
  - Purpose: `azure/login` + `az webapp config set` and resolving the App Service `defaultHostName`.
  - Notes: Must be valid JSON credentials for a service principal with access to the resource group.

**How to create App Service deploy secrets**

1) Enable basic auth for SCM and FTP (required to view publish profiles):

```bash
az resource update --resource-group "<RESOURCE_GROUP>" --name "<APP_NAME>/scm" \
  --resource-type "Microsoft.Web/sites/basicPublishingCredentialsPolicies" \
  --set properties.allow=true

az resource update --resource-group "<RESOURCE_GROUP>" --name "<APP_NAME>/ftp" \
  --resource-type "Microsoft.Web/sites/basicPublishingCredentialsPolicies" \
  --set properties.allow=true
```

1) Generate publish profile and store as a repo secret:

```bash
az webapp deployment list-publishing-profiles \
  --resource-group "<RESOURCE_GROUP>" \
  --name "<APP_NAME>" \
  --xml > publishProfile.xml

gh secret set AZURE_WEBAPP_PUBLISH_PROFILE -f publishProfile.xml
```

1) Create a service principal (used by `AZURE_CREDENTIALS`) and store as a repo secret:

```bash
az ad sp create-for-rbac \
  --name "<SP_NAME>" \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP> \
  --sdk-auth > azure-credentials.json

gh secret set AZURE_CREDENTIALS -f azure-credentials.json
```

**Optional: local Git/FTP credentials**

- User-scope credentials (shared across apps):

```bash
az webapp deployment user set --user-name "<DEPLOY_USER>" --password "<DEPLOY_PASS>"
```

- App-scope credentials (per app). For Git, append `/<APP_NAME>.git` to the `scmUri`:

```bash
az webapp deployment list-publishing-credentials \
  --resource-group "<RESOURCE_GROUP>" \
  --name "<APP_NAME>" \
  --query scmUri -o tsv
```

- Reset app-scope password:

```bash
az resource invoke-action --action newpassword \
  --resource-group "<RESOURCE_GROUP>" \
  --name "<APP_NAME>" \
  --resource-type Microsoft.Web/sites
```

### B) Web app (Next.js in `apps/web`)

Used by `apps/web/.github/workflows/deploy-production.yml`, `deploy-staging.yml`, and `rollback.yml`.

Production:

- `PROD_SUPABASE_URL`
- `PROD_SUPABASE_KEY`
- `AZURE_STATIC_WEB_APPS_TOKEN_PROD`
- `PROD_SENTRY_DSN` (optional, if you use Sentry)

Staging:

- `STAGING_SUPABASE_URL`
- `STAGING_SUPABASE_KEY`
- `AZURE_STATIC_WEB_APPS_TOKEN_STAGING`

Notes:

- These secrets are injected into the build as `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY`.

### C) Pipelines / DB writes

Common across parity checks and ingestion pipelines.

- `DATABASE_URL`
  - Purpose: PostgreSQL connection string for Supabase.
  - Used by: `.github/workflows/kpi-parity.yml` and other DB-touching workflows.

- `SUPABASE_SERVICE_ROLE`
  - Purpose: Service role key for server-side Supabase operations.
  - Used by: multiple analytics agent workflows (e.g., `operations-dashboard.yml`, `investor-reporting.yml`, `risk-monitoring.yml`).

- `SUPABASE_URL` / `SUPABASE_ANON_PUBLIC_KEY`
  - Purpose: Some scheduled workflows use this pair (distinct from the `apps/web` PROD/STAGING naming).
  - Used by: `.github/workflows/supabase-figma-scheduled.yml`.

### D) Meta / Marketing

- `META_SYSTEM_USER_TOKEN`
  - Used by: `.github/workflows/meta_ingest.yaml`.

- `META_ACCESS_TOKEN`
- `META_AD_ACCOUNT_ID`
  - Used by: `.github/workflows/meta-export.yml`, `.github/workflows/brand-monitoring.yml`.

### E) HubSpot / Cascade

Used by ingestion / unified pipeline workflows.

- `CASCADE_USERNAME`
- `CASCADE_PASSWORD`
  - Used by: `.github/workflows/cascade_ingest.yml`, `.github/workflows/daily-ingest.yml`.

- `HUBSPOT_API_KEY` or `HUBSPOTTOKEN`
  - Note: both naming styles exist across workflows; standardize later.

### F) Notifications / Observability / QA

- `SLACK_WEBHOOK_URL`, `SLACK_WEBHOOK_OPS`, `SLACK_WEBHOOK_LEADERSHIP`
- `SLACK_BOT_TOKEN`
- `OPIK_TOKEN` / `OPIKTOKEN`
- `PHOENIX_TOKEN`

### G) Code quality / security

- `SONAR_TOKEN`
- `SNYK_TOKEN`

### H) AI providers / research tools

- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `PERPLEXITY_API_KEY`
- `TAVILY_KEY`
- `CLAUDE_ROCKET_TOKEN`

### I) Figma

- `FIGMA_TOKEN`
- `FIGMA_FILE_KEY`
- `FIGMA_NODE_ID` (some workflows)

### J) Vercel (if using `.github/workflows/deploy.yml`)

- `VERCEL_TOKEN`
- `VERCEL_ORG_ID`
- `VERCEL_PROJECT_ID`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Recommended naming cleanup (later)

This repo currently mixes secret naming styles (`SUPABASE_SERVICE_ROLE` vs `SUPABASESERVICEROLE`, `OPIK_TOKEN` vs `OPIKTOKEN`).
For stability, don’t rename secrets during incident recovery. After stabilization, align names and update workflows in one PR.

## How to verify you’re unblocked

1. Re-run a previously failing workflow.
2. If it fails, confirm the missing secret name matches this file.
3. Add the missing secret and re-run.

## Validate secrets and tokens

Run the verifier locally (presence + API checks):

```bash
python scripts/validate_secrets.py
```

Presence/format only:

```bash
python scripts/validate_secrets.py --presence-only
```

Fail on missing optional secrets:

```bash
python scripts/validate_secrets.py --strict
```

GitHub Actions (manual):

```bash
gh workflow run "Verify Secrets and Integrations" -f presence_only=false -f strict=true
```
