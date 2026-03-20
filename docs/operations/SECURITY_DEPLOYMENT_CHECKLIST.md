# Security Hardening Deployment Checklist

**Date**: 2026-02-04  
**Commit**: `2704f6ad8`  
**Status**: ⏳ Pending Deployment

---

## 📋 Pre-Deployment Verification

- [x] All migrations created and committed
- [x] Documentation reviewed and complete
- [x] Code pushed to main branch
- [x] CI/CD checks passing (with known python download issue)

---

## 🚀 Deployment Steps

### Step 1: Azure Provider Registration (5 minutes)

**Required**: Before alert rules can be deployed

```bash
# Set active subscription
az account set --subscription 695e4491-d568-4105-a1e1-8f2baf3b54df

# Register provider
az provider register --namespace Microsoft.AlertsManagement

# Verify (wait 1-2 minutes)
az provider show \
  --namespace Microsoft.AlertsManagement \
  --query "registrationState" \
  -o tsv
```

**Expected Output**: `Registered`

**Documentation**: [docs/OBSERVABILITY.md](../OBSERVABILITY.md)

---

### Step 2: Redeploy Azure Alert Rules (10 minutes)

**After** provider registration completes:

1. Navigate to [Azure Portal → abaco-rg → Deployments](https://portal.azure.com/#@/resource/subscriptions/695e4491-d568-4105-a1e1-8f2baf3b54df/resourceGroups/abaco-rg/deployments)

2. For each failed deployment:
   - `Failure-Anomalies-Alert-Rule-Deployment-{guid}` (3 instances)
   - Click deployment → **Redeploy** button
   - Verify deployment succeeds

3. Verify alerts are active:

   ```bash
   az monitor alert-rule list \
     --resource-group abaco-rg \
     --query "[?contains(name, 'Failure-Anomalies')].{Name:name, Enabled:enabled}" \
     -o table
   ```

**Expected**: 3 alert rules, all `Enabled=true`

---

### Step 3: Deploy Supabase Migrations (15 minutes)

**Critical**: Apply migrations in order

#### Option A: Supabase CLI (Recommended)

```bash
# Ensure you're in project root
cd /path/to/abaco-loans-analytics

# Link to project (if not already linked)
supabase link --project-ref goxdevkqozomyhsyxhte

# Push all migrations
supabase db push
```

#### Option B: Manual via SQL Editor

1. Go to [Supabase SQL Editor](https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql)

2. Run migrations **in this exact order**:

   a. **Enable RLS** (foundation):

   ```bash
   cat db/migrations/20260204_enable_rls.sql
   ```

   Copy output → Paste in SQL Editor → Click "Run"

   b. **Create Policies** (access control):

   ```bash
   cat db/migrations/20260204_rls_policies.sql
   ```

   Copy output → Paste in SQL Editor → Click "Run"

   c. **Fix Broadcast Trigger** (SQL injection fix):

   ```bash
   cat db/migrations/20260204_fix_broadcast_trigger.sql
   ```

   Copy output → Paste in SQL Editor → Click "Run"

   d. **Harden KPI Policy** (audit trail):

   ```bash
   cat db/migrations/20260204_fix_kpi_values_policy.sql
   ```

   Copy output → Paste in SQL Editor → Click "Run"

---

## ✅ Post-Deployment Verification

### Verify Supabase RLS (5 minutes)

Run these queries in [Supabase SQL Editor](https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql):

#### 1. Check RLS Enabled on All Tables

```sql
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname IN ('public', 'monitoring')
AND tablename IN (
  'financial_statements', 'payment_schedule', 'real_payment',
  'loan_data', 'customer_data', 'historical_kpis',
  'kpi_timeseries_daily', 'analytics_facts',
  'data_lineage', 'lineage_columns', 'lineage_dependencies',
  'lineage_audit_log', 'kpi_values'
)
ORDER BY schemaname, tablename;
```

**Expected**: All rows show `rowsecurity = t` (true)  
**If False**: Re-run migration `20260204_enable_rls.sql`

#### 2. Count Policies

```sql
SELECT
  schemaname,
  COUNT(*) as policy_count,
  array_agg(DISTINCT cmd::text ORDER BY cmd::text) as policy_types
FROM pg_policies
WHERE schemaname IN ('public', 'monitoring')
GROUP BY schemaname
ORDER BY schemaname;
```

**Expected**:

- `public`: 28+ policies (SELECT, INSERT, UPDATE, DELETE)
- `monitoring`: 3 policies (SELECT, INSERT, ALL)

**If Missing**: Re-run migration `20260204_rls_policies.sql`

#### 3. Verify Function Fix

```sql
SELECT
  p.proname AS function_name,
  CASE
    WHEN pg_get_functiondef(p.oid) LIKE '%SET search_path%'
    THEN '✅ search_path pinned'
    ELSE '❌ search_path NOT pinned'
  END AS security_status
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
AND p.proname = 'loan_data_broadcast_trigger';
```

**Expected**: `✅ search_path pinned`  
**If Not**: Re-run migration `20260204_fix_broadcast_trigger.sql`

#### 4. Check KPI Audit Trail

```sql
SELECT
  column_name,
  data_type,
  is_nullable
FROM information_schema.columns
WHERE table_schema = 'monitoring'
AND table_name = 'kpi_values'
AND column_name = 'created_by';
```

**Expected**: 1 row showing `created_by` column exists  
**If Empty**: Re-run migration `20260204_fix_kpi_values_policy.sql`

---

### Verify Azure Alerts (2 minutes)

```bash
# Check all alert rules
az monitor alert-rule list \
  --resource-group abaco-rg \
  --output table

# Should show 3+ alert rules with Enabled=true
```

---

### Test Application Access (10 minutes)

#### Test 1: Customer Can Read Own Data

```javascript
// In application code or Supabase client
const { data, error } = await supabase
  .from("loan_data")
  .select("*")
  .eq("customer_id", currentUser.id);

// Expected: Success with user's loan records
console.log("Test 1:", error ? "FAIL" : "PASS");
```

#### Test 2: Customer Cannot Read Others' Data

```javascript
const { data, error } = await supabase
  .from("customer_data")
  .select("*")
  .neq("user_id", currentUser.id);

// Expected: Empty array (RLS blocks access)
console.log("Test 2:", data?.length === 0 ? "PASS" : "FAIL");
```

#### Test 3: Service Role Has Full Access

```javascript
import { createClient } from "@supabase/supabase-js";

const supabaseAdmin = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY,
);

const { data, error } = await supabaseAdmin
  .from("customer_data")
  .select("count");

// Expected: Success with total count
console.log("Test 3:", error ? "FAIL" : "PASS");
```

---

## 🔍 Security Validation

### Check Supabase Dashboard

1. Go to [Supabase Dashboard → Database](https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/database/tables)

2. Navigate to **Security Advisor** or **Database → Policies**

3. Verify:
   - ✅ No warnings about tables without RLS
   - ✅ No warnings about functions with mutable search_path
   - ✅ All policies show in policy list

**Expected Result**: 0 security alerts

---

## 🚨 Rollback Plan (If Issues Occur)

### If Application Breaks After RLS Deployment

**Quick Fix** (temporarily disable RLS to restore service):

```sql
-- EMERGENCY ONLY - Disable RLS on critical tables
ALTER TABLE public.customer_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.real_payment DISABLE ROW LEVEL SECURITY;

-- Re-enable after fixing policies
```

### Proper Rollback

```bash
# Revert migrations via Supabase CLI
supabase db reset

# Or manually drop policies:
```

```sql
-- List all policies to drop
SELECT
  'DROP POLICY IF EXISTS "' || policyname || '" ON ' ||
  schemaname || '.' || tablename || ';'
FROM pg_policies
WHERE schemaname IN ('public', 'monitoring')
ORDER BY schemaname, tablename;

-- Copy output and run
```

---

## 📊 Monitoring Post-Deployment

### First 24 Hours

1. **Monitor Application Logs**:

   ```bash
   # Check for RLS policy violations
   tail -f logs/app.log | grep -i "permission denied\|row-level security"
   ```

2. **Check Supabase Logs**:
   - Go to [Supabase Dashboard → Logs](https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/logs/explorer)
   - Filter: `severity: error`
   - Look for: RLS errors, policy violations

3. **Monitor Azure Alerts**:
   - Verify alerts are triggering appropriately
   - Check Application Insights for anomalies

### First Week

- [ ] Review policy violation logs daily
- [ ] Monitor query performance (RLS may add slight overhead)
- [ ] Collect user feedback on access issues
- [ ] Run security audit to confirm all alerts resolved

---

## 📞 Support & Escalation

### If Deployment Issues Occur

1. **Check Documentation**:
  - [SUPABASE_RLS_HARDENING.md](../security/SUPABASE_RLS_HARDENING.md) - Troubleshooting section
  - [OBSERVABILITY.md](../OBSERVABILITY.md) - Azure/alerts setup references

2. **Email Channels**:
   - `infra-alerts@abaco.co` - Infrastructure issues
   - `security@abaco.co` - Security-related questions
   - `dev-support@abaco.co` - Application access issues

3. **Escalation Path**:
   - Level 1: DevOps team (`devops@abaco.co`)
   - Level 2: Security team (`security@abaco.co`)
   - Level 3: CTO (critical production issues)

---

## ✅ Deployment Sign-Off

| Step                           | Owner         | Status     | Date | Notes |
| ------------------------------ | ------------- | ---------- | ---- | ----- |
| Azure Provider Registration    | DevOps        | ⏳ Pending |      |       |
| Azure Alert Rules Redeployment | DevOps        | ⏳ Pending |      |       |
| Supabase Migrations            | Backend Team  | ⏳ Pending |      |       |
| Verification Tests             | QA            | ⏳ Pending |      |       |
| Security Review                | Security Team | ⏳ Pending |      |       |
| Production Monitoring          | On-Call       | ⏳ Pending |      |       |

---

**Created**: 2026-02-04  
**Last Updated**: 2026-02-04  
**Next Review**: After successful deployment
