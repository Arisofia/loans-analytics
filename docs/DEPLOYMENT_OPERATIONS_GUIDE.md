# Deployment Operations Guide

**Last Updated**: 2026-01-31  
**Status**: Production Ready  
**Environment**: Azure App Service (abaco-analytics-dashboard)

---

## Quick Reference

| Operation        | Command                                                                 | Time     |
| ---------------- | ----------------------------------------------------------------------- | -------- |
| **Deploy**       | `./scripts/deploy_to_azure.sh`                                          | 5-15 min |
| **Monitor**      | `./scripts/monitor_deployment.sh <url> <hours>`                         | Variable |
| **Rollback**     | `./scripts/rollback_deployment.sh [commits_back]`                       | 5-10 min |
| **Health Check** | `curl https://abaco-analytics-dashboard.azurewebsites.net/?page=health` | <1 sec   |

---

## Automated Deployment Flow

### Fully Automated (Recommended)

```bash
./scripts/deploy_to_azure.sh
```

**What it does**:

1. ✅ Validates local git state (no uncommitted changes, on main)
2. ✅ Syncs with remote (main branch aligned with origin/main)
3. ✅ Runs local tests (pytest)
4. ✅ Verifies GitHub secrets exist (AZURE_CREDENTIALS or AZURE_WEBAPP_PUBLISH_PROFILE)
5. 🚀 Triggers GitHub Actions workflow
6. 📊 Monitors workflow completion (5-15 minutes)
7. ⏳ Waits for App Service initialization (60 seconds)
8. 🔍 Performs health checks (up to 10 attempts)
9. 📈 Reports success/failure with app URL

**Expected Output**:

```
[Step 1] Validating local repository state...
✅ Local state is clean

[Step 2] Syncing with remote...
✅ main branch is synced with origin/main

[Step 3] Running local tests...
✅ All tests passed

[Step 4] Checking GitHub deployment secrets...
✅ Azure deployment secrets configured

[Step 5] Triggering GitHub Actions deployment...
✅ Workflow triggered: Run ID 12345678

[Step 6] Waiting for deployment to complete...
[60 dots = 10 minutes]
✅ Deployment workflow completed successfully

[Step 7] Waiting for Azure App Service to initialize...
✅ Initialization period complete

[Step 8] Running post-deployment health checks...
Health check attempt 1/10...
✅ Health check passed (HTTP 200)

✅ Deployment automation complete!
Access your dashboard: https://abaco-analytics-dashboard.azurewebsites.net
```

---

## Manual Deployment (Alternative)

If you prefer manual control over each step:

### 1. Local Validation

```bash
# Ensure main branch
git checkout main

# Verify clean state
git status  # Should show "nothing to commit, working tree clean"

# Sync with remote
git fetch origin main
git pull origin main

# Run tests
pytest tests/ -q
```

### 2. Verify GitHub Secrets

```bash
# Using GitHub CLI
gh secret list -R Arisofia/abaco-loans-analytics

# Look for: AZURE_CREDENTIALS or AZURE_WEBAPP_PUBLISH_PROFILE
```

### 3. Trigger Deployment

**Option A: Via GitHub CLI**

```bash
gh workflow run deploy_dashboard.yml \
  -R Arisofia/abaco-loans-analytics \
  --ref main
```

**Option B: Via GitHub Web UI**

1. Go to: https://github.com/Arisofia/abaco-loans-analytics/actions
2. Click: "Deploy Abaco Analytics Dashboard to Azure Web App"
3. Click: "Run workflow"
4. Select: Branch = main
5. Click: "Run workflow"

### 4. Monitor Deployment

```bash
# Watch workflow logs in real-time
gh run watch <RUN_ID>

# Or check status
gh run view <RUN_ID> -R Arisofia/abaco-loans-analytics
```

### 5. Health Check (after deployment)

```bash
curl -f https://abaco-analytics-dashboard.azurewebsites.net/?page=health

# Expected: HTTP 200 + response body with health status
```

---

## Post-Deployment Monitoring

### Immediate Check (30 seconds after deploy)

```bash
curl https://abaco-analytics-dashboard.azurewebsites.net/?page=health
```

### Automated 1-Hour Monitor

```bash
./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 1
```

### Automated 24-Hour Monitor

```bash
./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 24
```

**Monitor Script Output**:

- Checks every 60 seconds
- Tracks latency and response codes
- Reports success rate
- Suggests actions for failures

### Manual Monitoring (Azure Portal)

1. Go to: https://portal.azure.com
2. Navigate to: Resource Groups → AI-MultiAgent-Ecosystem-RG → abaco-analytics-dashboard
3. Check:
   - **Status**: Should be "Running" (green)
   - **Metrics**: CPU, memory, response time (healthy ranges)
   - **Logs**: Application Insights → Failures (should be 0)
   - **Recent Requests**: Monitor for 5xx errors

### Key Metrics to Monitor

| Metric                     | Healthy Range | Warning | Critical |
| -------------------------- | ------------- | ------- | -------- |
| **HTTP 5xx errors**        | 0             | >1%     | >5%      |
| **Response latency (p95)** | <1s           | 1-2s    | >2s      |
| **CPU**                    | <40%          | 40-70%  | >70%     |
| **Memory**                 | <50%          | 50-75%  | >75%     |
| **Success rate**           | 95%+          | 80-95%  | <80%     |

---

## Troubleshooting

### Deployment Fails at "Azure login"

**Cause**: AZURE_CREDENTIALS secret missing or invalid

**Fix**:

1. Go to GitHub Settings → Secrets and variables → Actions
2. Add/update AZURE_CREDENTIALS with service principal JSON:
   ```json
   {
     "clientId": "...",
     "clientSecret": "...",
     "subscriptionId": "...",
     "tenantId": "..."
   }
   ```
3. Re-run deployment

### Deployment Fails at "Deploy to Azure Web App"

**Cause**: AZURE_WEBAPP_PUBLISH_PROFILE missing or App Service misconfigured

**Fix**:

1. In Azure Portal, go to App Service → Get publish profile
2. Copy the entire XML content
3. Add as GitHub secret: AZURE_WEBAPP_PUBLISH_PROFILE
4. Re-run deployment

### Health Check Fails with "Connection refused"

**Cause**: App Service not ready, or startup command failed

**Fixes**:

1. Wait 2-3 minutes for full initialization
2. Check App Service logs: Insights → Logs → search "Error"
3. Verify startup.sh exists in repo root
4. Check environment variables in App Service → Configuration

### Health Check Fails with "HTTP 500"

**Cause**: Application error in Streamlit or dependencies

**Fixes**:

1. Check Application Insights → Failures for specific error
2. Review streaming app.py for syntax errors
3. Verify all environment variables set in App Service Configuration
4. Check Python version: should be 3.11
5. Review logs for missing dependencies

### App Loads But Shows "Module not found"

**Cause**: Missing dependencies in requirements.txt or virtual environment issue

**Fixes**:

1. Verify requirements.txt is in repo root
2. Check all dependencies are in requirements.txt
3. In App Service → Configuration, set: PYTHONUNBUFFERED=1
4. Redeploy to force fresh dependency install

---

## Rollback Procedures

### Rollback Last Deployment

```bash
./scripts/rollback_deployment.sh
```

### Rollback 3 Commits Back

```bash
./scripts/rollback_deployment.sh 3
```

**Rollback Script**:

1. ✅ Verifies on main branch
2. ✅ Resets git to target commit
3. ✅ Force-pushes to origin
4. 🚀 Re-triggers deployment from known-good state
5. 🔍 Validates health of rolled-back deployment

### Manual Rollback (Alternative)

```bash
# Find last known-good commit
git log --oneline | head -10

# Reset to specific commit
git reset --hard <COMMIT_HASH>

# Force push
git push --force-with-lease origin main

# Manually trigger deployment in GitHub Actions
```

---

## Scheduled Operations

### GitHub Actions Workflows (Auto-run)

**Every 24 hours**:

- `performance-monitoring.yml` - Runs latency benchmarks
- Data pipeline job (if configured) - Refreshes KPIs

**Every 6 hours** (if configured):

- Health check workflow - Validates deployment

### Manual Scheduling (Cron on your machine)

For 24-hour post-deployment monitoring:

```bash
# macOS/Linux
cat >> /tmp/abaco_deploy_monitor.sh << 'EOF'
#!/bin/bash
cd /path/to/abaco-loans-analytics
./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 24
EOF

chmod +x /tmp/abaco_deploy_monitor.sh

# Add to cron (runs at 2 AM daily)
(crontab -l 2>/dev/null; echo "0 2 * * * /tmp/abaco_deploy_monitor.sh") | crontab -
```

---

## Emergency Procedures

### Kill Deployment (Stop Workflow)

```bash
# Get run ID from GitHub Actions UI
gh run cancel <RUN_ID> -R Arisofia/abaco-loans-analytics
```

### Force Stop App Service

```bash
# Using Azure CLI
az webapp stop --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG
```

### Emergency Rollback to Last Known Good

```bash
./scripts/rollback_deployment.sh 1
# OR
./scripts/rollback_deployment.sh 3  # If recent commits are problematic
```

### Restart App Service (without code changes)

```bash
# Using Azure CLI
az webapp restart --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG
```

---

## Runbooks by Scenario

### Scenario 1: Deploying New Feature

1. **Develop & Test Locally**

   ```bash
   pytest tests/  # All tests pass
   git status     # Clean
   ```

2. **Deploy**

   ```bash
   ./scripts/deploy_to_azure.sh
   ```

3. **Verify**
   - ✅ Health check passes
   - ✅ Feature works in browser
   - ✅ No new errors in logs

4. **Monitor**
   ```bash
   ./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 1
   ```

### Scenario 2: Critical Bug Fix

1. **Create Fix Branch** (if needed)

   ```bash
   git checkout -b fix/critical-issue
   # ... make fix ...
   pytest tests/  # Verify fix
   ```

2. **Merge to Main**

   ```bash
   git checkout main
   git merge fix/critical-issue
   git push origin main
   ```

3. **Deploy Immediately**

   ```bash
   ./scripts/deploy_to_azure.sh
   ```

4. **Intensive Monitoring**
   ```bash
   ./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 4
   ```

### Scenario 3: Deployment Failed (Rollback)

1. **Stop Current Deployment** (if still running)

   ```bash
   # Find run ID from GitHub Actions, then:
   gh run cancel <RUN_ID>
   ```

2. **Rollback to Last Known Good**

   ```bash
   ./scripts/rollback_deployment.sh 1
   ```

3. **Verify Rollback Health**
   - ✅ Workflow completes
   - ✅ Health check passes
   - ✅ App loads in browser

4. **Investigate Root Cause**
   ```bash
   # Check logs, compare commits, review code changes
   gh run view <FAILED_RUN_ID> -R Arisofia/abaco-loans-analytics
   ```

### Scenario 4: Performance Degradation

1. **Check Metrics** (Azure Portal)
   - CPU, memory, latency trends

2. **Review Logs** (Application Insights)
   - Look for errors, slow queries

3. **Run Monitoring Script**

   ```bash
   ./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 2
   ```

4. **If Degradation Confirmed**
   - Check for runaway processes
   - Review recent deployments
   - Consider rollback if recent deployment caused it
   - Investigate database performance

---

## Success Criteria

✅ **Deployment is successful when**:

1. All workflow steps pass (green in GitHub Actions)
2. Health check returns HTTP 200
3. App loads in browser without 4xx/5xx errors
4. KPI cards display data
5. No new errors in Application Insights
6. Success rate ≥95% over 1 hour

✅ **Rollback is successful when**:

1. Workflow completes with green status
2. Health check passes immediately
3. App is accessible and responsive
4. Verified stable over 10+ minutes

---

## Need Help?

1. **Deployment documentation**: [DEPLOYMENT_READINESS_CHECKLIST.md](DEPLOYMENT_READINESS_CHECKLIST.md)
2. **Performance fixes**: [PERFORMANCE_CI_FIX_SUMMARY.md](PERFORMANCE_CI_FIX_SUMMARY.md)
3. **Architecture guide**: [DEPLOYMENT_EXECUTION_GUIDE.md](DEPLOYMENT_EXECUTION_GUIDE.md)
4. **GitHub Actions logs**: https://github.com/Arisofia/abaco-loans-analytics/actions
5. **Azure Portal**: https://portal.azure.com

---
