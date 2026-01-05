# Azure App Service Deployment Guide

Complete step-by-step guide for deploying Abaco Analytics Dashboard to Azure App Service with tracing, health checks, and secrets management.

## Prerequisites

- Azure subscription with resource group `AI-MultiAgent-Ecosystem-RG`
- Azure CLI (`az` command) installed and authenticated
- GitHub CLI (`gh`) installed and authenticated (used for setting repository secrets interactively)
- GitHub repository with push access
- Streamlit dashboard code at `/dashboard/app.py`

## 1. Create Azure Resources

### 1.1 Create App Service Plan

```bash
az appservice plan create \
  --name abaco-analytics-plan \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --sku B2 \
  --is-linux
```

### 1.2 Create App Service (Web App)

```bash
az webapp create \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --plan abaco-analytics-plan \
  --name abaco-analytics-dashboard \
  --runtime "PYTHON|3.11"
```

### 1.3 Create Storage Account (for KPI exports)

```bash
az storage account create \
  --name abacokpiexport \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --location eastus \
  --sku Standard_LRS

# Create container
az storage container create \
  --account-name abacokpiexport \
  --name kpi-exports \
  --auth-mode login

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name abacokpiexport \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --query connectionString -o tsv)

echo "AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONNECTION_STRING"
```

### 1.4 Create Application Insights (for tracing)

```bash
az monitor app-insights component create \
  --app abaco-dashboard-ai \
  --location eastus \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --application-type web

# Get connection string
APPINSIGHTS_CONNECTION=$(az monitor app-insights component show \
  --app abaco-dashboard-ai \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --query connectionString -o tsv)

echo "APPLICATIONINSIGHTS_CONNECTION_STRING=$APPINSIGHTS_CONNECTION"
```

### 1.5 Create Key Vault (optional, for secrets)

```bash
az keyvault create \
  --name abaco-kv \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --location eastus

# Grant access to App Service managed identity
az keyvault set-policy \
  --name abaco-kv \
  --object-id $(az webapp identity assign \
    --resource-group AI-MultiAgent-Ecosystem-RG \
    --name abaco-analytics-dashboard \
    --query principalId -o tsv) \
  --secret-permissions get list

# Store secrets
az keyvault secret set \
  --vault-name abaco-kv \
  --name supabase-url \
  --value "https://your-project.supabase.co"

az keyvault secret set \
  --vault-name abaco-kv \
  --name supabase-key \
  --value "your-supabase-anon-key"
```

## 2. Configure App Service Settings

### 2.1 Set Runtime Stack

```bash
az webapp config set \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --startup-file "python -m streamlit run dashboard/app.py --server.port=8000 --server.address=0.0.0.0 --server.headless=true"
```

### 2.2 Add Application Settings (Secrets)

```bash
az webapp config appsettings set \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --settings \
    SUPABASE_URL="https://your-project.supabase.co" \
    SUPABASE_ANON_KEY="your-anon-key" \
    AZURE_STORAGE_CONNECTION_STRING="$STORAGE_CONNECTION_STRING" \
    APPLICATIONINSIGHTS_CONNECTION_STRING="$APPINSIGHTS_CONNECTION" \
    OTEL_EXPORTER_OTLP_ENDPOINT="https://eastus.in.applicationinsights.azure.com/opentelemetry/v1/traces" \
    AZURE_KEY_VAULT_URL="https://abaco-kv.vault.azure.net/" \
    LOG_LEVEL="INFO" \
    PYTHON_ENABLE_WORKER_EXTENSIONS="1"
```

**Replace with your actual values**:

- `SUPABASE_URL` — your Supabase project URL
- `SUPABASE_ANON_KEY` — your Supabase anon key
- `APPLICATIONINSIGHTS_CONNECTION_STRING` — from App Insights creation above

### 2.3 Configure Health Check

```bash
az webapp config set \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --health-check-path "/?page=health"
```

### 2.4 Enable Managed Identity

If using Key Vault with managed identity (already done above, but verify):

```bash
az webapp identity show \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard
```

## 3. Generate GitHub Secrets

Create GitHub secrets for deployment in your repository:

**Setting → Secrets and variables → Actions → New repository secret**

### 3.1 Publish Profile (required for deployment)

```bash
az webapp deployment publish-profile \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --xml > publish-profile.xml

cat publish-profile.xml
# Copy entire contents → GitHub Secret: AZURE_WEBAPP_PUBLISH_PROFILE
```

### 3.2 Service Principal (optional, for health check automation)

Create a service principal for Azure operations in GitHub Actions:

```bash
az ad sp create-for-rbac \
  --name "github-abaco-analytics" \
  --role Contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/AI-MultiAgent-Ecosystem-RG
```

This outputs:

```json
{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}
```

Convert to JSON and save as GitHub Secret: `AZURE_CREDENTIALS`:

```bash
echo '{
  "clientId": "...",
  "clientSecret": "...",
  "subscriptionId": "...",
  "tenantId": "..."
}' | base64 > /dev/stdin
# Copy base64 output → GitHub Secret: AZURE_CREDENTIALS
```

### 3.3 Azure Static Web Apps token (SWA deploy)

Note: this section applies to the **`apps/web`** site (Next.js static site) which is deployed to **Azure Static Web Apps**. The rest of this document primarily covers the Streamlit dashboard (`/dashboard/app.py`) which is deployed to **Azure App Service**. They are separate deployment targets and may have separate CI/CD secrets and workflows.

If you deploy `apps/web` to Azure Static Web Apps, set a repository secret for the SWA deployment token. For public docs we recommend using a generic placeholder name `AZURE_STATIC_WEB_APPS_API_TOKEN` for clarity; the actual secret name in your organization may include the resource name or suffix. You can obtain the deployment token in the Azure portal (Static Web Apps → <your app> → Manage deployment token) or create one with the Azure CLI.

Set the secret using the GitHub UI (Settings → Secrets and variables → Actions) or via `gh` (replace `YOUR_ORG/YOUR_REPO` with your repository):

- Create/update interactively (prompts for input):

```bash
# Replace YOUR_ORG/YOUR_REPO with your github repository
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo YOUR_ORG/YOUR_REPO
```

- Non-interactive (from an environment variable `SWA_TOKEN`):

```bash
# Replace YOUR_ORG/YOUR_REPO with your github repository
echo "$SWA_TOKEN" | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN --repo YOUR_ORG/YOUR_REPO
```

- Verify the secret exists:

```bash
# Replace YOUR_ORG/YOUR_REPO with your github repository
gh secret list --repo YOUR_ORG/YOUR_REPO
```

If your organization uses resource-specific naming for secrets, you can substitute the actual name you use (for example `AZURE_STATIC_WEB_APPS_API_TOKEN_<RESOURCE_SUFFIX>`), but avoid publishing that exact name in public docs; store it in an internal runbook if it must be kept private.

Note: Secrets are not available to workflows triggered by forked pull requests. Use a branch on the main repository or a manual workflow dispatch to run deploy steps that require the secret.

## 4. GitHub Actions Deployment

### 4.1 Trigger Deployment

Push to `main` branch (or manually trigger `deploy-dashboard.yml`):

```bash
git push origin main
```

This automatically runs:

1. **deploy-dashboard.yml** — builds and deploys to App Service
2. **validate-deployment.yml** — validates health endpoint and tracing

### 4.2 Monitor Deployment

Check GitHub Actions workflow:

- **Actions** tab → **Deploy Abaco Analytics Dashboard to Azure Web App**
- Review logs for any errors
- After completion, **Validate Deployment Health** should run automatically

### 4.3 View App

After successful deployment:

```text
https://abaco-analytics-dashboard.azurewebsites.net
```

Health endpoint:

```text
https://abaco-analytics-dashboard.azurewebsites.net/?page=health
```

## 5. Verify Deployment

### 5.1 Check App Service Logs

```bash
az webapp log tail \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard
```

### 5.2 Test Health Endpoint

```bash
curl -i https://abaco-analytics-dashboard.azurewebsites.net/?page=health
# Expected: HTTP 200 with "ok" response
```

### 5.3 View Tracing in App Insights

1. Azure Portal → **Application Insights** → **abaco-dashboard-ai**
2. **Distributed Traces** or **Transaction Search**
3. Search for service: `abaco-dashboard`
4. View HTTP requests, database queries, custom spans

### 5.4 Validate Secrets

```bash
# Test Supabase connectivity
curl -H "apikey: $SUPABASE_ANON_KEY" \
  "https://your-project.supabase.co/rest/v1/kpi_values?limit=1"
# Expected: JSON array (or empty)
```

## 6. Troubleshooting

### App fails to start

**Symptoms**: Container doesn't start, HTTP 500/502

**Debug steps**:

```bash
# 1. Check recent logs
az webapp log tail --resource-group AI-MultiAgent-Ecosystem-RG --name abaco-analytics-dashboard

# 2. Verify startup command
az webapp config show --resource-group AI-MultiAgent-Ecosystem-RG --name abaco-analytics-dashboard

# 3. Check Python version
az webapp config show --resource-group AI-MultiAgent-Ecosystem-RG --name abaco-analytics-dashboard --query "linuxFxVersion"

# 4. Verify app settings
az webapp config appsettings list --resource-group AI-MultiAgent-Ecosystem-RG --name abaco-analytics-dashboard
```

**Common issues**:

- Missing `SUPABASE_URL` or `SUPABASE_ANON_KEY` → add via step 2.2
- Wrong Python version → ensure 3.11
- `requirements.txt` not found → verify in root directory (should delegate to `dashboard/requirements.txt`)

### Health endpoint returns 404

**Verify endpoint path**:

```bash
# Should be configured as /?page=health
az webapp config show \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --query "healthCheckPath"
```

If not set, reconfigure:

```bash
az webapp config set \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --health-check-path "/?page=health"
```

### Tracing not appearing in App Insights

1. **Verify connection string**:

   ```bash
   az webapp config appsettings list \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --name abaco-analytics-dashboard \
     | grep APPLICATIONINSIGHTS
   ```

2. **Check OTEL endpoint**:

   ```bash
   # Should be: https://<region>.in.applicationinsights.azure.com/opentelemetry/v1/traces
   az webapp config appsettings list \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --name abaco-analytics-dashboard \
     | grep OTEL_EXPORTER
   ```

3. **Restart app** to pick up settings:

   ```bash
   az webapp restart \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --name abaco-analytics-dashboard
   ```

### Validation workflow fails

Check GitHub Actions **Validate Deployment Health** workflow:

1. **Actions** → **Validate Deployment Health** → latest run
2. View step summaries and logs
3. Auto-created GitHub issue with troubleshooting steps

Common failures:

- App taking > 5 min to start → increase timeout in workflow
- Health endpoint not configured → see step 2.3
- Network firewall blocking OTEL endpoint → allow App Service egress to App Insights

## 7. Post-Deployment Checklist

- [ ] App Service created and running
- [ ] Health endpoint responds with 200/"ok"
- [ ] GitHub secrets set: `AZURE_WEBAPP_PUBLISH_PROFILE`, `AZURE_CREDENTIALS`
- [ ] App settings configured: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `APPLICATIONINSIGHTS_CONNECTION_STRING`
- [ ] Application Insights shows traces for `abaco-dashboard` service
- [ ] Dashboard accessible at `https://abaco-analytics-dashboard.azurewebsites.net`
- [ ] Health check path configured in App Service
- [ ] Validation workflow passing (auto-run after deploy)
- [ ] Logs monitored: `az webapp log tail ...`

## 8. Scaling & High Availability

### Enable Always On

```bash
az webapp update \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --set alwaysOn=true
```

### Scale to Multiple Instances

```bash
az appservice plan update \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-plan \
  --number-of-workers 2
```

### Enable Auto-Scale (optional)

```bash
az monitor autoscale create \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --resource-type "Microsoft.Web/serverFarms" \
  --resource abaco-analytics-plan \
  --min-count 2 \
  --max-count 4 \
  --count 2
```

## 9. Cost Optimization

- **B2 plan** ($0.17/hour) — suitable for development/testing
- **P1V2 plan** ($0.17/hour) — for production (includes better performance)
- **Reserved Instances** — 1-year or 3-year commitments for 35-72% savings
- **Application Insights** — free tier: 1 GB/month

## References

- [Azure App Service Python Quickstart](https://learn.microsoft.com/en-us/azure/app-service/quickstart-python)
- [Azure CLI Reference](https://learn.microsoft.com/en-us/cli/azure/)
- [Streamlit Deployment](https://docs.streamlit.io/deploy/tutorials/host-fast-api-in-streamlit-cloud)
- [Application Insights with OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
