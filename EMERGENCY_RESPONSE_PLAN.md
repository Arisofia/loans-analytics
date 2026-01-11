# 🚨 Emergency Response Plan - Production Outage

**Date**: January 1, 2026, 7:00 AM CET
**Status**: CRITICAL - All 3 P0 systems down
**Owner**: DevOps / Data Engineering Lead

---

## SITUATION REPORT

### P0 Issues (CRITICAL - Fix Immediately)

| Issue | Status | Impact | Owner |
|-------|--------|--------|-------|
| **PROD-001: Dashboard Offline** | DNS_PROBE_FINISHED_NXDOMAIN | Users cannot access system | DevOps |
| **PROD-002: CI/CD Pipeline Broken** | 🔧 **FIXED** - Redeploying | Blocks all code deployments | DevOps |
| **PROD-003: Data Pipelines Failing** | Unknown root cause | No data refresh, stale metrics | Data Eng |

---

## IMMEDIATE ACTIONS (Next 30 Minutes)

### 1️⃣ Deploy CI/CD Fix

**Status**: ✅ **COMPLETE** - Fixed `.github/workflows/deploy-dashboard.yml`

**Fix Applied**:

- Replaced invalid `if: ${{ secrets.AZURE_CREDENTIALS != '' }}` syntax
- Added proper GitHub Actions output check: `steps.check_creds.outputs.has_creds == 'true'`
- Added health check validation after deployment
- Added failure notifications

**Next Step**: Commit and push to main

```bash
git add .github/workflows/deploy-dashboard.yml
git commit -m "fix(ci): correct github actions secrets context syntax (P0 PROD-002)"
git push origin main
```

**Expected Result**: Workflow runs without syntax errors on next push to main

---

### 2️⃣ Restore Dashboard Service (Parallel Task)

**Owner**: DevOps
**Timeline**: 30 minutes

**Diagnosis Steps**:

1. Azure Portal → App Services → `abaco-analytics-dashboard`
2. Check "Overview" → Is status "Running"?
   - If **Stopped** → Click "Start"
   - If **Running** → Continue to step 3
3. Click "Diagnose and solve problems" → Run "Availability" check
4. If startup errors → Check "Log stream" for Python/dependency errors

**Common Issues & Fixes**:

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError` | Check `dashboard/requirements.txt` installed all deps |
| `Port already in use` | Restart app service |
| `Connection timeout` | Check Azure Storage/DB connection string in App Settings |
| DNS NXDOMAIN | Check if custom domain configured, or use `*.azurewebsites.net` domain |

**Success Criteria**: Dashboard loads without DNS error at <https://abaco-analytics-dashboard.azurewebsites.net>

---

### 3️⃣ Diagnose Data Pipeline Failures (Parallel Task)

**Owner**: Data Engineering
**Timeline**: 45 minutes

**Root Cause Investigation**:

1. GitHub Actions → View latest failed run (e.g., "Daily Data Ingestion")
2. Click into job logs and search for actual error message
3. Look for patterns:
   - **Auth failure** → API key expired, check Key Vault
   - **Connection timeout** → Network/firewall blocking, check NSG rules
   - **Module not found** → Dependency missing from `requirements.txt`
   - **Data validation** → Great Expectations test failed

**Immediate Mitigation**:

- If **single source failed**: Retry manually or use fallback data
- If **multiple sources failed**: Likely authentication issue → Rotate API keys in Key Vault
- If **transformation error**: Hotfix code in `src/` and redeploy

**Success Criteria**: At least 1 data pipeline completes successfully

---

## HOUR 2-4: STABILIZATION

### 4️⃣ Set Up Basic Monitoring

**Owner**: DevOps
**Timeline**: 30 minutes

**Azure Portal Actions**:

```text
Application Insights → Alerts → Create Alert Rule
- Metric: Response time > 5 seconds
- Action: Email to team

Application Insights → Alerts → Create Alert Rule
- Metric: Failed requests > 10 in 5 minutes
- Action: Email to team

App Service → Health Check
- Path: /?page=health
- Enable health check monitoring
```

**GitHub Actions**:

```text
Repository Settings → Notifications
- Workflows: Enable email on workflow failure
- Add Slack webhook if configured
```

---

### 5️⃣ Enable Branch Protection

**Owner**: DevOps
**Timeline**: 10 minutes

**GitHub → Settings → Branches → Add Rule**:

- Branch name: `main`
- ✅ Require PR before merging
- ✅ Require status checks to pass (select CI workflows)
- ✅ Require code review (1 approval)

**Effect**: Prevents direct commits that break production

---

## ESCALATION MATRIX

| Scenario | Action | Contact |
|----------|--------|---------|
| Dashboard still down after restart | Escalate to Azure Support | CTO |
| Pipeline fix doesn't resolve issue | Check API vendor status | Integration Lead |
| Cannot fix in 4 hours | Activate disaster recovery | CTO + Head of Data |

---

## SUCCESS METRICS (Target: EOD)

| Metric | Current | Target |
|--------|---------|--------|
| Dashboard Uptime | 0% | 95%+ |
| CI/CD Success Rate | 0% | 80%+ |
| Data Pipelines Running | 0/4 | 3/4 |
| Monitoring Alerts | 0 | 5+ |
| Incident Documentation | Partial | Complete |

---

## POST-INCIDENT (Next 24 Hours)

1. **Root Cause Analysis**: Document why all 3 systems failed simultaneously
2. **Timeline**: Create detailed timeline of failure detection and response
3. **Preventive Measures**:
   - Add better alerting to catch failures earlier
   - Implement health checks for each component
   - Add runbooks for common failure patterns
4. **Team Debrief**: 30-min meeting to review learnings

---

## RUNBOOKS REFERENCED

- `docs/runbooks/pipeline-delay.md` → For data pipeline diagnosis
- `docs/runbooks/data-loss.md` → If data corruption suspected
- `docs/RISK_REGISTER.md` → Severity and escalation rules

---

## KEY CONTACTS

| Role | Name | Contact | Status |
|------|------|---------|--------|
| DevOps Lead | [Name] | [Slack/Email] | On-call |
| Data Eng Lead | [Name] | [Slack/Email] | On-call |
| CTO (Escalation) | [Name] | [Slack/Email] | Available |

---

**Last Updated**: 2026-01-01 07:00 CET
**Status**: EMERGENCY RESPONSE IN PROGRESS
**Next Review**: 30 minutes
