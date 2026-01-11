# 🔍 ROOT CAUSE ANALYSIS - Production Failures

**Date**: January 1, 2026, 7:25 AM CET
**Status**: CRITICAL - All P0 issues traced to configuration gaps
**Impact**: Dashboard offline, pipelines failing, data not flowing

---

## EXECUTIVE SUMMARY

All three P0 production failures are rooted in **missing database configuration**:

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| **PROD-001: Dashboard Down** | Azure App Service instance restart + missing DB connection string | Restart instance + add SUPABASE_URL env var |
| **PROD-003: Pipelines Failing** | ⚠️ **SUPABASE_URL & SUPABASE_SERVICE_ROLE not set in GitHub Actions** | Add secrets to GitHub repository |
| **PROD-002: CI/CD Broken** | ✅ **FIXED** - Secrets context syntax error corrected |  Deploy fix (COMPLETE) |

---

## ROOT CAUSE #1: PIPELINE DATABASE CONNECTION MISSING 🔴

### Evidence

**Pipeline code explicitly requires Supabase**:

- `src/abaco_pipeline/output/supabase_writer.py` - Writes pipeline metadata to Supabase
- `src/abaco_pipeline/settings.py` - Expects `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE` env vars
- `src/abaco_pipeline/main.py` (line 15) - Imports `SupabaseAuth, SupabaseWriter`

### Expected Environment Variables

```python
# From settings.py
supabase_url: str | None = os.getenv("SUPABASE_URL")
supabase_service_role_key: str | None = os.getenv("SUPABASE_SERVICE_ROLE") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
cascade_token: str | None = os.getenv("CASCADE_TOKEN")
```

### Current Status

- **SUPABASE_URL**: ❌ NOT SET in GitHub Actions
- **SUPABASE_SERVICE_ROLE**: ❌ NOT SET in GitHub Actions
- **CASCADE_TOKEN**: ❌ NOT SET in GitHub Actions
- App Service config: ❌ NO database connections configured

### Failure Sequence

```text
1. GitHub Actions pipeline runs
2. Python code imports supabase_writer.py
3. Tries to initialize SupabaseWriter
4. SUPABASE_URL env var missing → SupabaseAuth(url=None)
5. All Supabase API calls fail → 401/500 errors
6. Pipeline exits within 11-19 seconds
7. Logs show: "Missing required environment variable: SUPABASE_URL"
```

### Fix

**Option A: Set up Supabase (Recommended for production)**

```bash
# 1. Create Supabase project at https://supabase.com
# 2. Get credentials:
#    - SUPABASE_URL: https://xxxxx.supabase.co
#    - SUPABASE_SERVICE_ROLE: sbp_xxxxxxxx...

# 3. Add to GitHub secrets:
gh secret set SUPABASE_URL --body "https://xxxxx.supabase.co"
gh secret set SUPABASE_SERVICE_ROLE --body "sbp_xxxxxxxx..."
gh secret set CASCADE_TOKEN --body "your_cascade_api_token"

# 4. Add to Azure App Service configuration:
az webapp config appsettings set \
  --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --settings SUPABASE_URL="https://xxxxx.supabase.co" \
             SUPABASE_SERVICE_ROLE="sbp_xxxxxxxx..."
```

**Option B: Modify pipeline to not require Supabase (Fallback)**

- Edit `src/abaco_pipeline/main.py` to skip Supabase writer if env vars missing
- Store outputs to Azure Blob Storage instead
- Less ideal for audit trail compliance

---

## ROOT CAUSE #2: DASHBOARD DATABASE NOT CONFIGURED 🔴

### Evidence

**App Service Configuration** (Azure Portal → App Settings):

- HUBSPOT_API_KEY ✅
- OPENAI_API_KEY ✅
- SCM_DO_BUILD_DURING_DEPLOYMENT=1 ✅
- **DATABASE_URL**: ❌ MISSING
- **SUPABASE_URL**: ❌ MISSING

**Dashboard code expects database connection**:

- `dashboard/utils/ingestion.py` imports database modules
- Likely tries to fetch KPIs from database on startup
- Fails with connection error → app doesn't respond to health checks

### Failure Sequence

```text
1. App Service restarts with new code
2. startup.sh runs: bash startup.sh
3. app.py imports and tries to connect to database
4. DATABASE_URL env var not set
5. Connection fails
6. Health check endpoint (/?page=health) not responding
7. Azure marks app as unhealthy
8. Users see DNS error (actually: service not responding)
```

### Fix

```bash
# Add Supabase connection to Azure App Service
az webapp config appsettings set \
  --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --settings SUPABASE_URL="https://xxxxx.supabase.co" \
             SUPABASE_SERVICE_ROLE="sbp_xxxxxxxx..."
```

---

## ROOT CAUSE #3: MISSING SUPABASE TABLES 🟡

### Evidence

**Expected Supabase Schema** (`supabase_writer.py` lines 10-12):

```text
Database: analytics (schema)
Tables:
  - pipeline_runs
  - raw_artifacts
  - kpi_values
  - data_quality_results
```

**Database Migrations** found in repo:

- `supabase/migrations/00_init_base_tables.sql` ← CREATE TABLE statements
- `supabase/migrations/20251231_pipeline_audit_tables.sql` ← Audit tables
- `supabase/migrations/20260101_analytics_kpi_views.sql` ← KPI views

### Current Status

🤔 **Unknown** - Migrations exist but unclear if applied to production Supabase

### Fix

```bash
# 1. Log into Supabase dashboard
# 2. Go to SQL Editor
# 3. Run migration scripts in order:
#    - 00_init_base_tables.sql
#    - 20251231_pipeline_audit_tables.sql
#    - 20260101_analytics_kpi_views.sql

# Or via CLI (if Supabase CLI is installed):
supabase migration up --db-url "postgres://[user]:[password]@db.xxx.supabase.co:5432/postgres"
```

---

## ROOT CAUSE #4: APP SERVICE INSTANCE RESTART NEEDED 🟡

### Current State

- **Instance**: LW1SDLWK0006XP
- **Status**: "Desconocido" (Disconnected/Unknown)
- **Action Taken**: Restart initiated ~20 minutes ago
- **Expected**: Should recover within 5-10 minutes

### Diagnosis

```text
Azure Portal → App Services → abaco-analytics-dashboard → Instances
Look for: Instance status should change to "En ejecución" (Running)
If still "Desconocido" after 10 minutes: Click "Reparar" again
If persistent: Click "Reemplazar instancia" for full replacement
```

---

## COMPLETE REMEDIATION PLAN

### Immediate (Next 30 Minutes)

```text
1. ✅ PROD-002 (CI/CD): FIXED - deploy-dashboard.yml corrected
2. Verify PROD-001 (Dashboard): Check Azure Portal for instance recovery
3. Identify Supabase status:
   - Is Supabase already provisioned?
   - If yes: Get SUPABASE_URL and SUPABASE_SERVICE_ROLE
   - If no: Create new Supabase project
4. Add GitHub secrets:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE
   - CASCADE_TOKEN
5. Add Azure App Service config:
   - SUPABASE_URL
   - SUPABASE_SERVICE_ROLE
```

### Short Term (Next 2 Hours)

```text
1. Apply Supabase migrations (if new project)
2. Manually trigger pipeline from GitHub Actions
3. Verify pipeline logs show successful Supabase connection
4. Check dashboard loads and can query KPIs
5. Create monitoring dashboards for pipeline health
```

### Medium Term (This Week)

```text
1. Document data architecture (COMPLETE: docs/ARCHITECTURE.md)
2. Set up automated backups for Supabase
3. Configure alerting for missing env vars
4. Upgrade App Service tier (Basic B1 → Standard S1)
5. Enable branch protection on main
```

---

## CRITICAL QUESTIONS FOR NEXT STEP

**1. Supabase Status**

- [ ] Is Supabase already provisioned for this project?
- [ ] If yes: What is the SUPABASE_URL and SERVICE ROLE KEY?
- [ ] If no: Should we create new Supabase project, or use PostgreSQL instead?

**2. Data Architecture**

- [ ] Are there other databases we should know about?
- [ ] Is data currently being stored anywhere (even if not working)?
- [ ] What is the desired data flow: Cascade → Supabase → Dashboard?

**3. Integration Status**

- [ ] Is HubSpot API integration working?
- [ ] Is Cascade API integration working?
- [ ] Any API keys need rotation?

**4. App Service Instance**

- [ ] Has the instance recovered to "En ejecución" status yet?
- [ ] Any startup errors in the log stream?

---

## MONITORING & PREVENTION

### Alert on Missing Environment Variables

```bash
# GitHub Actions: Check env vars before running pipeline
- name: Validate pipeline configuration
  run: |
    if [ -z "${{ secrets.SUPABASE_URL }}" ]; then
      echo "❌ SUPABASE_URL not configured"
      exit 1
    fi
    echo "✅ Required secrets present"
```

### Automated Secret Scanning (Already Implemented)

- `.github/workflows/security-secret-scan.yml` prevents committing secrets
- But doesn't prevent missing required secrets

### Platform certificate warnings

- During App Service startup you may see messages like: `rehash: warning: skipping duplicate certificate in azl_*.pem`.
- These warnings are generated by the platform's certificate update step and are benign in most cases; no immediate action is required.
- If these warnings are persistent and you need them removed, consider one of:
  - Set `WEBSITES_INCLUDE_CLOUD_CERTS=true` in App Service settings to include platform certs explicitly, or
  - Contact Azure support to remove duplicate certificates from the platform image.

### Configuration Validation Test

- Add pytest test to verify all required env vars set before pipeline runs
- Location: `tests/test_pipeline_config.py`

---

## REFERENCES

- 📄 **Architecture Doc**: `docs/ARCHITECTURE.md` (sections 1, 3, 6)
- 📄 **Risk Register**: `docs/RISK_REGISTER.md` (R-001: Data Loss, R-002: Security)
- 📄 **Audit Integration**: `src/pipeline/AUDIT_INTEGRATION_GUIDE.md`
- 🔧 **Supabase Writer**: `src/abaco_pipeline/output/supabase_writer.py`
- ⚙️ **Settings**: `src/abaco_pipeline/settings.py`
- 📊 **Migrations**: `supabase/migrations/`

---

**Next Action**: Respond to critical questions above so we can proceed with Supabase setup and final recovery steps.
