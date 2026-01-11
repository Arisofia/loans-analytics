# Complete Transformation Deliverables Package

**Abaco Loans Analytics - Engineering Excellence Transformation**
**Delivered**: January 1, 2026, 9:15 AM CET
**Prepared by**: Engineering Excellence Audit Team
**Status**: Production System Recovery + Long-term Modernization

---

## 📑 Package Contents

- Incident Runbooks (3 Critical Scenarios)
- Monitoring & Alerting Automation
- Week 2-4 Transformation Roadmap
- GitHub Secrets Configuration Guide
- Architecture Decision Records (ADRs)
- Quick-Reference Checklists

---

## 1️⃣ Incident Runbooks

### RUNBOOK #1: Dashboard Down / Inaccessible

**Trigger**: Users report dashboard unavailable, NXDOMAIN, or error page

#### Symptoms

- DNS resolution failure
- HTTP 5xx errors
- Blank page / infinite loading
- "Application Error" page

#### Diagnostic Flow

```text
START: Dashboard inaccessible
│
├─> Test correct URL: https://abaco-analytics-dashboard-gbbjege0gxcbhyg9.canadacentral-01.azurewebsites.net
│   │
│   ├─> NXDOMAIN Error?
│   │   └─> Azure Portal → App Service → Verify resource exists
│   │       ├─> Resource missing → Restore from backup / redeploy
│   │       └─> Resource exists → Check from different network (phone hotspot)
│   │
│   ├─> HTTP 503 Service Unavailable?
│   │   └─> Azure Portal → App Service → Overview
│   │       ├─> Status: Stopped → Click "Start"
│   │       └─> Status: Running → Check "Instances" tab
│   │           └─> Instance "Desconocido" → Click "Reparar" → "Reiniciar"
│   │
│   ├─> HTTP 500 Internal Server Error?
│   │   └─> Azure Portal → Log Stream
│   │       ├─> ModuleNotFoundError → Check requirements.txt, redeploy
│   │       ├─> Connection timeout → Verify external API availability
│   │       └─> Startup timeout → Scale up App Service Plan (Basic B1 → Standard S1)
│   │
│   └─> Page loads but broken/blank?
│       └─> Check browser console for JavaScript errors
│           ├─> CORS error → Verify allowed origins in Azure config
│           ├─> API call failed → Check backend health
│           └─> Missing assets → Check deployment completed successfully
│
END: Issue resolved or escalated
```

#### Step-by-Step Resolution

**Step 1: Verify Service Status (2 minutes)**

Azure Portal Navigation:

1. Go to: `AI-MultiAgent-Ecosystem-RG` → `abaco-analytics-dashboard`
2. Check "Estado": Should show "En ejecución" (Running)
3. Check "Estado en tiempo de ejecución": Should NOT show "Problemas detectados"
4. If stopped → Click "Iniciar" (Start) button in top toolbar

**Step 2: Check Deployment Status (2 minutes)**

In Azure Portal:

1. Deployment Center → Logs
2. Find most recent deployment
3. Status should be "Success"
4. If "Failed" → Click to see error logs
5. Common issues:
   - Build timeout (increase timeout in workflow)
   - Missing dependencies (check requirements.txt)
   - Health check failed (verify health check URL matches actual URL)

**Step 3: Inspect Application Logs (3 minutes)**

In Azure Portal:

1. Log stream (under Monitoring section)
2. Look for errors in last 30 minutes
3. Key patterns:
   - `ModuleNotFoundError: No module named 'X'` → Add X to requirements.txt, redeploy
   - `FileNotFoundError: [Errno 2] No such file or directory: 'data/archives/looker_exports'` → Verify CSV files deployed, check .gitignore doesn't exclude them
   - `Address already in use` → Restart app service
   - `Timeout waiting for response` → Scale up to higher tier (S1 or better)

**Step 4: Emergency Rollback (5 minutes)**

If recent deployment broke the app:

1. GitHub Actions → Find last successful "Deploy Abaco Analytics Dashboard" run
2. Note the commit SHA
3. Git: `git revert <broken-commit-sha>`
4. Push to main → Triggers automatic redeploy

#### Prevention Measures

- Set up Application Insights alerts for HTTP 5xx errors
- Enable Always On (requires Standard tier or higher)
- Add health check endpoint monitoring
- Document correct production URL in repo README

---

### RUNBOOK #2: Data Pipeline Failure

**Trigger**: Scheduled workflow fails, stale data in dashboard, missing KPI updates

#### Symptoms

- GitHub Actions shows red X on scheduled workflows
- Dashboard shows outdated "last updated" timestamp
- Slack notifications of pipeline failure (if configured)

#### Diagnostic Flow

```text
START: Pipeline failed notification
│
├─> GitHub Actions → Click failed workflow run
│   │
│   ├─> Failure in "Install Dependencies" step? (< 30 seconds runtime)
│   │   └─> Expand step → Read error message
│   │       ├─> "Could not find a version that satisfies requirement X==Y.Z"
│   │       │   Fix: Update requirements.txt, change X==Y.Z to compatible version
│   │       │
│   │       ├─> "Cannot find name 'describe'/'it'/'expect'" (TypeScript)
│   │       │   Fix: Add @types/jest to package.json OR use tsc --skipLibCheck
│   │       │
│   │       └─> "ERROR: No matching distribution found for X"
│   │           Fix: Package removed from PyPI, find alternative
│   │
│   ├─> Failure in "Run [Pipeline]" step? (> 30 seconds runtime)
│   │   └─> Expand step → Search for "Error:", "Failed:", "Exception:"
│   │       ├─> "KeyError: 'DATABASE_URL'" / "Environment variable not found"
│   │       │   Fix: Add missing secret in GitHub → Settings → Secrets
│   │       │
│   │       ├─> "AuthenticationError" / "401 Unauthorized" / "403 Forbidden"
│   │       │   Fix: Rotate API key (HubSpot/Meta/OpenAI), update GitHub secret
│   │       │
│   │       ├─> "TimeoutError" / "Connection refused"
│   │       │   Fix: Check external API status, verify network rules
│   │       │
│   │       ├─> "psycopg2.OperationalError: could not connect to server"
│   │       │   Fix: Verify DATABASE_URL, check Supabase project is running
│   │       │
│   │       └─> "ValidationError" / "AssertionError" (Great Expectations)
│   │           Fix: Data quality issue - investigate source data
│   │
│   └─> Failure in "Upload to Azure" / "Load to warehouse"?
│       └─> Check Azure credentials, verify storage account accessible
│
END: Pipeline re-run successfully OR root cause identified for fix
```

#### Step-by-Step Resolution

**Step 1: Identify Failure Point (2 minutes)**

GitHub Actions:

1. Navigate to failed workflow run
2. Look at job duration:
   - `< 30 sec` → Dependency/build issue
   - `30 sec - 5 min` → Auth/config issue
   - `> 5 min` → Data processing/validation issue
3. Click into failed job → Expand failed step

**Step 2: Common Fixes by Error Pattern**

**Pattern A: Missing Secrets**

Error:

```text
KeyError: 'DATABASE_URL'
Environment variable 'META_ACCESS_TOKEN' not found
```

Fix:

1. GitHub → Settings → Secrets and variables → Actions
2. New repository secret:
   - Name: `DATABASE_URL` (or missing secret name)
   - Value: [obtain from Supabase/service dashboard]
3. Re-run workflow

**Pattern B: Expired API Keys**

Error:

```text
401 Unauthorized
Invalid API key
```

Fix:

1. Visit service dashboard (HubSpot/Meta/OpenAI)
2. Generate new API key
3. Update GitHub Secret with new value
4. Re-run workflow

**Pattern C: Rate Limiting**

Error:

```text
429 Too Many Requests
Rate limit exceeded
```

Fix:

1. Adjust workflow schedule (reduce frequency)
2. Add exponential backoff to API calls
3. Request rate limit increase from API provider

**Pattern D: Data Validation Failure**

Error:

```text
ValidationError: Expected X rows, got Y
AssertionError: Column 'amount' has null values
```

Fix:

1. This is a DATA QUALITY issue, not a code issue
2. Investigate source system (Looker/HubSpot/Meta)
3. Decide: Accept new data shape OR fix source
4. Update Great Expectations suite if shape intentionally changed

**Step 3: Re-run Pipeline (1 minute)**

After applying fix:

1. GitHub Actions → Failed workflow run → "Re-run jobs" (top right)
2. Monitor new run for success

**Step 4: Verify Data Updated (2 minutes)**

After successful pipeline run:

1. Check dashboard for updated "Last refreshed" timestamp
2. Spot-check a few KPI values look reasonable
3. Verify row counts in warehouse (if applicable)

#### Prevention Measures

- Set up Slack notifications for workflow failures
- Add retry logic with exponential backoff to API calls
- Implement data quality monitoring dashboard
- Schedule key rotation reminders (every 90 days)
- Document all required secrets in repository README

---

### RUNBOOK #3: Deployment Blocked / CI/CD Failure

**Trigger**: Cannot merge PR, GitHub Actions fails on every commit, deployment stuck

#### Symptoms

- All CI checks failing with red X
- "Merge pull request" button disabled
- Deployment workflow never completes

#### Diagnostic Flow

```text
START: Cannot deploy code
│
├─> Check GitHub Actions status page
│   └─> GitHub experiencing outage? → Wait for resolution
│
├─> Check specific workflow failure
│   │
│   ├─> "Invalid workflow file" annotation?
│   │   └─> Syntax error in .github/workflows/*.yml
│   │       Fix: Validate YAML syntax, fix reported line/column
│   │
│   ├─> Workflow never starts / shows "Queued"?
│   │   └─> Check GitHub Actions minutes quota
│   │       ├─> Quota exceeded → Upgrade plan OR wait for reset
│   │       └─> Workflow disabled → Re-enable in Actions settings
│   │
│   ├─> Fails immediately with "secrets.X not found"?
│   │   └─> Check workflow trigger context
│   │       ├─> Pull request from fork → Secrets not available for security
│   │       │   Fix: Add 'if' condition to skip steps requiring secrets on forks
│   │       └─> Secret truly missing → Add in Settings → Secrets
│   │
│   ├─> Health check fails after successful deployment?
│   │   └─> Workflow pinging wrong URL
│   │       Fix: Update health_check_url in workflow to match actual URL
│   │
│   └─> Hangs at "Waiting for deployment"?
│       └─> Azure deployment stuck
│           Fix: Cancel workflow, manually restart App Service, re-run
│
END: CI/CD restored
```

#### Step-by-Step Resolution

**Step 1: Identify CI/CD Blocker (2 minutes)**

Check multiple signals:

1. GitHub → Actions tab → Latest workflow runs
2. Pull request → Checks tab → See which check failed
3. Branch protection → See which required checks missing

**Step 2: Fix Workflow Syntax Errors**

If "Invalid workflow file" annotation:

1. Click annotation to see exact line/column
2. Common issues:
   - Incorrect indentation (YAML is indent-sensitive)
   - Missing quotes around special characters
   - Invalid expression syntax (check `${{ }}` blocks)
   - Accessing unavailable context (e.g., secrets in pull_request)

Fix template:

```yaml
# Before (broken):
steps:
  - run: echo ${{secrets.API_KEY}}  # Fails if secret unavailable

# After (fixed):
steps:
  - name: Use API key
    if: github.event_name != 'pull_request'
    run: echo "${{ secrets.API_KEY }}"
```

**Step 3: Handle Fork PR Security**

Workflows triggered by PRs from forks cannot access secrets. Add this condition to steps that need secrets:

```yaml
jobs:
  deploy:
    # Only run on pushes OR PRs from same repo (not forks)
    if: github.event_name == 'push' || github.event.pull_request.head.repo.full_name == github.repository
    steps:
      - uses: actions/checkout@v4
      - name: Deploy with secrets
        run: deploy.sh
        env:
          API_KEY: ${{ secrets.API_KEY }}
```

**Step 4: Emergency Deploy Bypass**

If CI is completely broken but you need to deploy urgently:

**Option A: Temporarily disable branch protection**

1. Settings → Branches → Edit protection rule for 'main'
2. Uncheck "Require status checks to pass"
3. Merge PR manually
4. RE-ENABLE protection immediately after

**Option B: Manual Azure deployment**

1. Build locally: `npm run build` / `python -m build`
2. Azure Portal → App Service → Deployment Center
3. Upload `.zip` of built files
4. Manual deploy (not recommended for production long-term)

#### Prevention Measures

- Test workflows in feature branches before merging to main
- Use workflow validation tools (act, GitHub CLI)
- Separate required vs optional CI checks
- Document manual deployment procedure for emergencies
- Set up monitoring for CI/CD pipeline health

---

## 2️⃣ Monitoring & Alerting Automation

### Azure Monitor Alert Rules (ARM Template)

**File**: `infrastructure/azure-monitor-alerts.json`

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appServiceName": {
      "type": "string",
      "defaultValue": "abaco-analytics-dashboard"
    },
    "actionGroupId": {
      "type": "string",
      "metadata": {
        "description": "Resource ID of the action group for notifications"
      }
    }
  },
  "resources": [
    {
      "type": "Microsoft.Insights/metricAlerts",
      "apiVersion": "2018-03-01",
      "name": "Dashboard-HTTP-5xx-Errors",
      "location": "global",
      "properties": {
        "description": "Alert when dashboard returns HTTP 5xx errors",
        "severity": 1,
        "enabled": true,
        "scopes": [
          "[resourceId('Microsoft.Web/sites', parameters('appServiceName'))]"
        ],
        "evaluationFrequency": "PT5M",
        "windowSize": "PT5M",
        "criteria": {
          "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
          "allOf": [
            {
              "name": "Http5xx",
              "metricName": "Http5xx",
              "operator": "GreaterThan",
              "threshold": 10,
              "timeAggregation": "Total"
            }
          ]
        },
        "actions": [
          {
            "actionGroupId": "[parameters('actionGroupId')]"
          }
        ]
      }
    },
    {
      "type": "Microsoft.Insights/metricAlerts",
      "apiVersion": "2018-03-01",
      "name": "Dashboard-CPU-High",
      "location": "global",
      "properties": {
        "description": "Alert when CPU usage exceeds 80%",
        "severity": 2,
        "enabled": true,
        "scopes": [
          "[resourceId('Microsoft.Web/serverfarms', parameters('appServiceName'))]"
        ],
        "evaluationFrequency": "PT5M",
        "windowSize": "PT15M",
        "criteria": {
          "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
          "allOf": [
            {
              "name": "CpuPercentage",
              "metricName": "CpuPercentage",
              "operator": "GreaterThan",
              "threshold": 80,
              "timeAggregation": "Average"
            }
          ]
        },
        "actions": [
          {
            "actionGroupId": "[parameters('actionGroupId')]"
          }
        ]
      }
    },
    {
      "type": "Microsoft.Insights/metricAlerts",
      "apiVersion": "2018-03-01",
      "name": "Dashboard-Memory-High",
      "location": "global",
      "properties": {
        "description": "Alert when memory usage exceeds 85%",
        "severity": 2,
        "enabled": true,
        "scopes": [
          "[resourceId('Microsoft.Web/serverfarms', parameters('appServiceName'))]"
        ],
        "evaluationFrequency": "PT5M",
        "windowSize": "PT15M",
        "criteria": {
          "odata.type": "Microsoft.Azure.Monitor.SingleResourceMultipleMetricCriteria",
          "allOf": [
            {
              "name": "MemoryPercentage",
              "metricName": "MemoryPercentage",
              "operator": "GreaterThan",
              "threshold": 85,
              "timeAggregation": "Average"
            }
          ]
        },
        "actions": [
          {
            "actionGroupId": "[parameters('actionGroupId')]"
          }
        ]
      }
    }
  ]
}
```

### GitHub Actions Failure Notifications

Add to `.github/workflows/notifications.yml`:

```yaml
name: Notify on Workflow Failures

on:
  workflow_run:
    workflows: ["Pipeline", "Deploy"]
    types: [completed]

jobs:
  slack-notify:
    runs-on: ubuntu-latest
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    steps:
      - name: Send Slack notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ github.event.workflow_run.conclusion }}
          text: 'Workflow "${{ github.event.workflow_run.name }}" failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK_URL }}
          fields: repo,message,commit,author
```

---

## 3️⃣ Week 2-4 Transformation Roadmap

### Week 2: Stabilization & Observability

| Task | Owner | Effort | Acceptance Criteria |
|------|-------|--------|-------------------|
| Deploy Azure Monitor alerts | DevOps | 1 day | All 3 alert rules active, test notifications working |
| Set up GitHub workflow notifications | DevOps | 4 hours | Slack messages on pipeline failures |
| Document all required GitHub secrets | Engineering | 4 hours | README lists every secret, no missing values |
| Create runbook testing procedure | SRE | 8 hours | At least 1 runbook tested with real incident |
| Review & harden branch protection rules | Engineering | 4 hours | Main branch requires all critical checks to pass |

### Week 3: Performance & Reliability

| Task | Owner | Effort | Acceptance Criteria |
|------|-------|--------|-------------------|
| Implement data pipeline retry logic | Data Eng | 2 days | Failed jobs automatically retry up to 3x with backoff |
| Add health check endpoints | Backend | 1 day | `/health` returns 200 with status JSON |
| Optimize slow KPI calculations | Data Eng | 2 days | P95 pipeline time < 10 minutes |
| Scale App Service to Standard tier | DevOps | 4 hours | Always On enabled, auto-scaling configured |
| Load testing on dashboard | QA | 1 day | Supports 100 concurrent users without degradation |

### Week 4: Automation & Self-Healing

| Task | Owner | Effort | Acceptance Criteria |
|------|-------|--------|-------------------|
| Auto-rollback on failed health check | DevOps | 1 day | Dashboard auto-recovers from bad deployments |
| Automated secrets rotation script | DevOps | 1 day | Script runs monthly, updates GitHub secrets |
| Database backup automation | DevOps | 1 day | Daily backups, 30-day retention, tested restore |
| Cost optimization review | FinOps | 1 day | Identify 20%+ cost reduction opportunities |
| Knowledge transfer & documentation | All | 4 hours | Wiki updated, team trained on runbooks |

---

## 4️⃣ GitHub Secrets Configuration Guide

### Required Secrets for Pipeline

Add these to GitHub → Settings → Secrets and variables → Actions:

| Secret Name | Source | Rotation Frequency | Test Method |
|-------------|--------|-------------------|------------|
| `DATABASE_URL` | Supabase → Project Settings → Connection Strings | 90 days | Try `psql $DATABASE_URL -c "SELECT 1"` |
| `META_ACCESS_TOKEN` | Meta Business Suite → Settings → API Tokens | 90 days | Call `/me` endpoint |
| `HUBSPOT_API_KEY` | HubSpot → Settings → API Key | 90 days | Call `hubspot.crm.contacts.basicApi.getPage()` |
| `OPENAI_API_KEY` | OpenAI → API Keys → Create New | 90 days | Call `openai.ChatCompletion.create()` |
| `SLACK_WEBHOOK_URL` | Slack → Apps → Incoming Webhooks | 180 days | Post test message |
| `AZURE_CREDENTIALS` | Azure → Service Principals | 90 days | `az login --service-principal` |

### Secrets Rotation Procedure

```bash
# 1. Generate new API key in source system
# 2. Test the new key locally before updating
# 3. Update GitHub secret:
#    Settings → Secrets and variables → Actions → [secret name] → Update
# 4. Re-run last 3 pipeline runs to confirm
# 5. Document rotation date in rotation log
```

### Emergency Secret Rotation

If a secret is compromised:

```bash
# 1. Revoke immediately in source system
# 2. Generate new key
# 3. Update GitHub secret (within 5 minutes)
# 4. Re-run active workflows
# 5. Monitor logs for auth failures
# 6. File incident report
```

---

## 5️⃣ Quick-Reference Checklists

### Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Code review approved
- [ ] Branch protection checks pass
- [ ] Database migrations tested on staging
- [ ] Secrets verified (no hardcoded credentials)
- [ ] Documentation updated
- [ ] Team notified of deployment time
- [ ] Rollback procedure documented

### Post-Incident Checklist

- [ ] Incident logged with timestamp & impact
- [ ] Root cause identified
- [ ] Fix implemented & tested
- [ ] Deployment to production
- [ ] Monitoring confirms resolution
- [ ] Post-mortem scheduled (within 24 hours)
- [ ] Preventive measures documented
- [ ] Team trained on new runbook

### Monthly Operations Review

- [ ] Review incident logs for patterns
- [ ] Test all 3 runbooks (at least 1)
- [ ] Rotate all API keys
- [ ] Review & optimize alert thresholds
- [ ] Audit GitHub access & secrets usage
- [ ] Performance review (P50, P95, P99 metrics)
- [ ] Cost analysis & optimization opportunities
- [ ] Team feedback on processes

---

## 📋 Summary

This deliverables package provides:

✅ **Immediate Response**: 3 runbooks for fastest incident resolution
✅ **Proactive Prevention**: Monitoring rules & automated alerts
✅ **Structured Scaling**: 3-week roadmap for reliability improvements
✅ **Operational Security**: Secrets management & rotation procedures
✅ **Team Readiness**: Checklists & procedures for consistent execution

**Next Steps**:

1. Implement incident runbooks in team Slack/wiki
2. Deploy Azure Monitor alerts using ARM template
3. Begin Week 2 stabilization phase
4. Schedule team training on new procedures

---

*For questions or clarifications, refer to the specific runbook or contact the DevOps team.*
