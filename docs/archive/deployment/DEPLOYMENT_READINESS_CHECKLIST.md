# Pre-Deployment & Deployment Checklist

**Status**: Ready for Production Deployment  
**Date**: 2026-01-31  
**Target**: abaco-analytics-dashboard (Azure App Service)

---

## ✅ Step 1: Local Validation Complete

| Item                           | Status  |
| ------------------------------ | ------- |
| pytest (95 passed, 11 skipped) | ✅ PASS |
| flake8 (whitespace cleaned)    | ✅ PASS |
| pylint (9.30/10)               | ✅ PASS |
| Git status (clean, pushed)     | ✅ PASS |

**Main branch**: `bcfce351e` (all changes pushed to origin/main)

---

## 📋 Step 2: Pre-Deployment Configuration

### 2.1 GitHub Secrets Verification

**Location**: GitHub → Settings → Secrets and variables → Actions

**Required Secret** (ONE of the following):

```
Option A: AZURE_CREDENTIALS (service principal JSON)
- Type: Large multi-line JSON object
- Used by: azure/login@v2
- Format example:
  {
    "clientId": "...",
    "clientSecret": "...",
    "subscriptionId": "...",
    "tenantId": "..."
  }

Option B: AZURE_WEBAPP_PUBLISH_PROFILE (publish profile XML)
- Type: XML file content
- Used by: azure/webapps-deploy@v3
- Source: Azure Portal → App Service → Get publish profile (download XML)
```

**Action Required**:

- [ ] **Confirm** that at least ONE of these secrets exists in GitHub
- [ ] **Document** which method you're using (A or B)
- [ ] If creating new secrets: Use values from Azure CLI or Azure Portal

**Workflow behavior**:

- If AZURE_CREDENTIALS exists: Uses `azure/login` + `az` CLI commands
- If AZURE_WEBAPP_PUBLISH_PROFILE exists: Uses direct deployment
- If neither exists: Workflow skips deployment with message "Skipping deployment: credentials required"

---

### 2.2 Azure App Service Configuration

**Location**: Azure Portal → Resource Groups → AI-MultiAgent-Ecosystem-RG → abaco-analytics-dashboard

\*\*Required Settings in "Configuration" → "Application settings":

**Environment Variables to Verify/Add**:

```
✓ STREAMLIT_SERVER_PORT=8000
✓ STREAMLIT_SERVER_ADDRESS=0.0.0.0
✓ STREAMLIT_SERVER_HEADLESS=true
✓ STREAMLIT_LOGGER_LEVEL=info

✓ SUPABASE_URL=<your_supabase_url>
✓ SUPABASE_ANON_KEY=<your_supabase_anon_key>
✓ SUPABASE_SECRET_API_KEY=<your_supabase_secret_key>

✓ PYTHON_VERSION=3.11
✓ PYTHONUNBUFFERED=1

✓ (Optional) LLM_API_KEY=<stored_in_azure_key_vault>
✓ (Optional) DASHBOARD_WEBHOOK_URL=<if_using_webhook_refresh>
```

**IMPORTANT: All sensitive values (API keys, tokens) should be stored in Azure Key Vault, not directly in App Service settings.**

**Action Required**:

- [ ] In Azure Portal, open App Service Configuration
- [ ] Add/verify each environment variable listed above
- [ ] **DO NOT** include secrets in this checklist; reference the secure values from:
  - Azure Key Vault (recommended), OR
  - GitHub Secrets synced to Azure
- [ ] Click "Save" after adding/updating any settings
- [ ] Verify "Application is stopped" indicator is gone (confirms settings applied)

**Startup Command Verification**:

- [ ] In "General settings" section, confirm Startup command is: `bash startup.sh`
- [ ] This file exists in repo root and configures Streamlit before launch

---

### 2.3 Deployment Workflow Configuration

**Location**: GitHub → Actions → "Deploy Abaco Analytics Dashboard to Azure Web App"

**Verify Trigger Settings**:

The workflow is configured to trigger on:

- [ ] **Push to main branch** with changes to:
  - streamlit_app.py
  - src/\*\* (any Python source)
  - config/\*\* (any config)
  - requirements.txt
  - startup.sh
  - .github/workflows/deploy_dashboard.yml
- [ ] **Manual trigger** (workflow_dispatch) - available in Actions tab

**Expected Workflow Steps**:

1. ✅ Checkout repository
2. ✅ Set up Python 3.11
3. ✅ Assert core files exist (streamlit_app.py, requirements.txt, startup.sh)
4. ✅ Install dependencies
5. ✅ Check Azure credentials (AZURE_CREDENTIALS or AZURE_WEBAPP_PUBLISH_PROFILE)
6. ✅ Deploy to Azure Web App
7. ✅ Post-deployment health check (curl to `/?page=health`)
8. ✅ Notify on failure

**Action Required**:

- [ ] View the workflow file: `.github/workflows/deploy_dashboard.yml`
- [ ] Confirm environment variables are correct:
  - WEBAPP_NAME: `abaco-analytics-dashboard`
  - RESOURCE_GROUP: `AI-MultiAgent-Ecosystem-RG`
  - HEALTH_CHECK_PATH: `/?page=health`
  - STARTUP_CMD: `bash startup.sh`
  - PYTHON_VERSION: `3.11`

---

## 🚀 Step 3: Deployment Execution

### 3.1 Pre-Deployment Checks

**Before pushing to main**:

- [ ] Confirm local all tests pass: `pytest` ✅ DONE
- [ ] Confirm no uncommitted changes: `git status` ✅ CLEAN
- [ ] Confirm main is pushed: `git push origin main` ✅ DONE
- [ ] Confirm GitHub secrets are in place (Step 2.1) ⏳ **PENDING YOUR ACTION**
- [ ] Confirm Azure App Service env vars are set (Step 2.2) ⏳ **PENDING YOUR ACTION**

### 3.2 Trigger Deployment

**Option A: Automatic Deployment (on next push to main)**

```bash
# Any of these will trigger the workflow:
git commit -m "feat: trigger deployment"
git push origin main

# The workflow will run automatically
# Check GitHub → Actions → Deploy Abaco Analytics Dashboard to Azure Web App
```

**Option B: Manual Trigger (immediate)**

1. Go to GitHub → Actions
2. Click "Deploy Abaco Analytics Dashboard to Azure Web App"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"
6. Watch the real-time logs

### 3.3 Monitor Deployment

**In GitHub Actions**:

- Watch logs as workflow executes
- Expected duration: 5-15 minutes
- Success = all steps green ✅

**Steps to monitor**:

1. ✅ Build (dependencies install)
2. ✅ Health check path configuration
3. ✅ Deploy (files transferred to App Service)
4. ✅ Post-deploy health check (curl test)

**If deployment fails**:

- [ ] Check GitHub Actions logs for error details
- [ ] Common issues:
  - Missing AZURE_CREDENTIALS or AZURE_WEBAPP_PUBLISH_PROFILE
  - Azure App Service down or misconfigured
  - Startup script error (check startup.sh)
  - Environment variables not set in App Service
- [ ] Remediate and re-run workflow manually

---

## 🔍 Step 4: Post-Deployment Verification

### 4.1 Health Check (Immediate - ~30 seconds after deploy completes)

```bash
# Test health endpoint (should return HTTP 200 + "ok")
curl -f "https://abaco-analytics-dashboard.azurewebsites.net/?page=health"

# Expected response:
# HTTP 200
# Body contains: "ok" or similar health indicator
```

### 4.2 Browser Verification (1-2 minutes after deploy)

**Visit**: https://abaco-analytics-dashboard.azurewebsites.net

**Verify**:

- [ ] App loads without 404 or 500 errors
- [ ] Streamlit UI renders (sidebar visible)
- [ ] Dashboard pages load (Home, Analysis, etc.)
- [ ] No JavaScript console errors (F12 → Console)
- [ ] Logo and styling render correctly

### 4.3 Azure Portal Monitoring

**Location**: Azure Portal → App Service → abaco-analytics-dashboard

**Check**:

- [ ] Status: "Running" (green indicator)
- [ ] Recent activity shows successful deployment
- [ ] Logs (Log stream or Application Insights) show no 5xx errors
- [ ] Request count and latency metrics normal

### 4.4 Functionality Spot Check

**In the app**:

- [ ] Navigate to "Data Upload" and verify CSV upload UI renders
- [ ] Navigate to "Analysis" and check if KPI cards display
- [ ] Check "Logs" page to see pipeline run history
- [ ] Try uploading a small test CSV (if applicable)

### 4.5 24-Hour Post-Deployment Monitoring

**Scheduled workflows** (run daily by GitHub Actions):

- [ ] `performance-monitoring.yml` → runs on schedule, confirms latency benchmarks pass
- [ ] Data pipeline (if configured) → runs and populates new KPI data
- [ ] Health checks → continue to pass

**Success indicators**:

- [ ] No spike in App Service error rate (Azure Portal → Metrics)
- [ ] Response times remain <2s on average
- [ ] Memory/CPU usage stable
- [ ] Logs show normal Streamlit/Python operations

---

## 📊 Summary

| Phase             | Status       | Owner                | Timeline |
| ----------------- | ------------ | -------------------- | -------- |
| Local Validation  | ✅ Complete  | Agent                | Done     |
| GitHub Secrets    | ⏳ Pending   | **You**              | 5 min    |
| Azure Config      | ⏳ Pending   | **You**              | 10 min   |
| Deploy            | ⏳ Ready     | Agent/GitHub Actions | 5-15 min |
| Post-Deploy Check | ⏳ Ready     | **You**              | 10 min   |
| 24h Monitoring    | ⏳ Scheduled | GitHub Actions       | 24 hours |

**Next Action**: Complete Step 2 (GitHub Secrets + Azure Config), then I can trigger Step 3 deployment.

---

## 🔗 Quick Links

- **GitHub Secrets**: https://github.com/Arisofia/abaco-loans-analytics/settings/secrets/actions
- **Azure Portal (App Service)**: https://portal.azure.com/#@example.onmicrosoft.com/resource/subscriptions/.../resourceGroups/AI-MultiAgent-Ecosystem-RG/providers/Microsoft.Web/sites/abaco-analytics-dashboard
- **GitHub Actions (Deploy Workflow)**: https://github.com/Arisofia/abaco-loans-analytics/actions/workflows/deploy_dashboard.yml
- **Production URL (after deploy)**: https://abaco-analytics-dashboard.azurewebsites.net
