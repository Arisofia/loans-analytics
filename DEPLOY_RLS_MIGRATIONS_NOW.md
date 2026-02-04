# 🚨 URGENT: Deploy RLS Migrations to Production

**Status**: 🔴 **CRITICAL - IMMEDIATE ACTION REQUIRED**  
**Risk Level**: HIGH - Data exposure vulnerability active  
**Time Estimate**: 5-10 minutes

---

## ⚠️ Current Situation

**8 security alerts are ACTIVE** in Supabase:
- All sensitive tables (customer_data, loan_data, financial_statements, etc.) are accessible without Row Level Security
- Anyone with the anon key can read/write data
- SQL injection vulnerability in loan_data_broadcast_trigger function
- Overly permissive KPI insertion policy

**Migrations are ready but NOT deployed to production database.**

---

## 🛠️ Deployment Methods

### **Option 1: Supabase CLI (Recommended)**

```bash
# 1. Login to Supabase (if not already logged in)
supabase login

# 2. Link to your project
supabase link --project-ref goxdevkqozomyhsyxhte

# 3. Deploy all pending migrations
supabase db push

# 4. Verify deployment
supabase db diff --linked
```

**Troubleshooting**:
- If login fails: Get access token from <https://supabase.com/dashboard/account/tokens>
- If link fails: Check you have owner/admin permissions on project

---

### **Option 2: Manual SQL Execution (SQL Editor)**

1. Open Supabase SQL Editor: <https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql/new>

2. **Run migrations in this exact order**:

#### Step 1: Enable RLS (REQUIRED FIRST)

```sql
-- From: db/migrations/20260204_enable_rls.sql
BEGIN;

ALTER TABLE public.financial_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.real_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.historical_kpis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.kpi_timeseries_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analytics_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_lineage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lineage_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lineage_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lineage_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitoring.kpi_values ENABLE ROW LEVEL SECURITY;

COMMIT;
```

**Verify Step 1**:
```sql
-- Should return 0 rows (all tables have RLS enabled)
SELECT schemaname, tablename 
FROM pg_tables 
WHERE schemaname IN ('public', 'monitoring')
AND tablename IN (
  'financial_statements', 'payment_schedule', 'real_payment', 
  'loan_data', 'customer_data', 'historical_kpis',
  'kpi_timeseries_daily', 'analytics_facts',
  'data_lineage', 'lineage_columns', 'lineage_dependencies', 
  'lineage_audit_log', 'kpi_values'
)
AND rowsecurity = false;
```

#### Step 2: Create RLS Policies

```sql
-- From: db/migrations/20260204_rls_policies.sql
BEGIN;

-- Customer Data Policies
CREATE POLICY "customer_read_own" ON public.customer_data
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "service_role_manage_customers" ON public.customer_data
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Loan Data Policies
CREATE POLICY "authenticated_read_loans" ON public.loan_data
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_loans" ON public.loan_data
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Payment Schedule Policies
CREATE POLICY "authenticated_read_payment_schedule" ON public.payment_schedule
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_payment_schedule" ON public.payment_schedule
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Real Payment Policies
CREATE POLICY "authenticated_read_payments" ON public.real_payment
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_payments" ON public.real_payment
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Financial Statements Policies
CREATE POLICY "authenticated_read_financial" ON public.financial_statements
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_financial" ON public.financial_statements
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Historical KPIs Policies
CREATE POLICY "authenticated_read_historical_kpis" ON public.historical_kpis
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_historical_kpis" ON public.historical_kpis
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- KPI Timeseries Policies
CREATE POLICY "authenticated_read_kpi_timeseries" ON public.kpi_timeseries_daily
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_kpi_timeseries" ON public.kpi_timeseries_daily
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Analytics Facts Policies
CREATE POLICY "authenticated_read_analytics_facts" ON public.analytics_facts
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_analytics_facts" ON public.analytics_facts
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Lineage Policies (Read-only for authenticated, manage for service_role)
CREATE POLICY "authenticated_read_lineage" ON public.data_lineage
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_lineage" ON public.data_lineage
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "authenticated_read_lineage_columns" ON public.lineage_columns
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_lineage_columns" ON public.lineage_columns
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "authenticated_read_lineage_deps" ON public.lineage_dependencies
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_lineage_deps" ON public.lineage_dependencies
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "authenticated_read_lineage_audit" ON public.lineage_audit_log
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "service_role_manage_lineage_audit" ON public.lineage_audit_log
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

COMMIT;
```

**Verify Step 2**:
```sql
-- Check that policies were created
SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname IN ('public', 'monitoring')
ORDER BY tablename, policyname;
-- Should show 26+ policies
```

#### Step 3: Fix Function Security

```sql
-- From: db/migrations/20260204_fix_broadcast_trigger.sql
BEGIN;

ALTER FUNCTION public.loan_data_broadcast_trigger() 
  SET search_path = public, pg_temp;

COMMIT;
```

**Verify Step 3**:
```sql
-- Check function configuration
SELECT proname, proconfig
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname = 'loan_data_broadcast_trigger';
-- proconfig should include: {search_path=public,pg_temp}
```

#### Step 4: Harden KPI Policy

```sql
-- From: db/migrations/20260204_fix_kpi_values_policy.sql
BEGIN;

-- Drop overly permissive policy
DROP POLICY IF EXISTS "allow_insert" ON monitoring.kpi_values;

-- Create restricted policies
CREATE POLICY "service_role_insert_kpis" ON monitoring.kpi_values
  FOR INSERT WITH CHECK (auth.jwt()->>'role' = 'service_role');

CREATE POLICY "internal_authenticated_insert_kpis" ON monitoring.kpi_values
  FOR INSERT WITH CHECK (
    auth.role() = 'authenticated' 
    AND auth.jwt()->>'email' LIKE '%@abaco.%'
  );

CREATE POLICY "authenticated_read_kpis" ON monitoring.kpi_values
  FOR SELECT USING (auth.role() = 'authenticated');

-- Add audit trail column (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'monitoring'
          AND table_name = 'kpi_values'
          AND column_name = 'created_by'
    ) THEN
        ALTER TABLE monitoring.kpi_values
        ADD COLUMN created_by UUID REFERENCES auth.users(id);
    END IF;
END $$;

-- Create trigger to auto-populate created_by
CREATE OR REPLACE FUNCTION monitoring.set_kpi_creator()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.created_by IS NULL THEN
        NEW.created_by := auth.uid();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = monitoring, public, pg_temp;

DROP TRIGGER IF EXISTS set_kpi_creator_trigger ON monitoring.kpi_values;
CREATE TRIGGER set_kpi_creator_trigger
  BEFORE INSERT ON monitoring.kpi_values
  FOR EACH ROW
  EXECUTE FUNCTION monitoring.set_kpi_creator();

COMMIT;
```

**Verify Step 4**:
```sql
-- Check KPI policies
SELECT policyname, cmd, qual, with_check
FROM pg_policies
WHERE schemaname = 'monitoring' AND tablename = 'kpi_values';
-- Should NOT show "allow_insert" policy
```

---

## ✅ Post-Deployment Verification

After running ALL migrations, verify security alerts are cleared:

### 1. Check Supabase Dashboard
Navigate to: <https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte>

- Security Advisor should show **0 issues** (down from 8)
- All tables should have "RLS Enabled" badge

### 2. Run Final Verification Query

```sql
-- Final check: All tables should have RLS enabled and policies defined
SELECT 
  t.schemaname,
  t.tablename,
  t.rowsecurity AS rls_enabled,
  COUNT(p.policyname) AS policy_count
FROM pg_tables t
LEFT JOIN pg_policies p ON t.schemaname = p.schemaname AND t.tablename = p.tablename
WHERE t.schemaname IN ('public', 'monitoring')
  AND t.tablename IN (
    'financial_statements', 'payment_schedule', 'real_payment',
    'loan_data', 'customer_data', 'historical_kpis',
    'kpi_timeseries_daily', 'analytics_facts',
    'data_lineage', 'lineage_columns', 'lineage_dependencies',
    'lineage_audit_log', 'kpi_values'
  )
GROUP BY t.schemaname, t.tablename, t.rowsecurity
ORDER BY t.schemaname, t.tablename;
```

**Expected Results**:
- `rls_enabled` = `true` for ALL tables
- `policy_count` ≥ 2 for each table (read + write policies)

### 3. Test Access Control

```bash
# Test that anon key CANNOT insert data (should return 403)
curl -X POST '***REMOVED***/rest/v1/customer_data' \
  -H "apikey: $SUPABASE_ANON_KEY" \
  -H "Authorization: Bearer $SUPABASE_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'

# Test that service_role CAN insert data (should return 201)
curl -X POST '***REMOVED***/rest/v1/customer_data' \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Service"}'
```

---

## 🔄 Post-Deployment Actions

After successful deployment:

1. **Update Status Report**:
   ```bash
   # Change status in docs/SECURITY_STATUS_REPORT.md
   # From: 🔴 CRITICAL - DEPLOYMENT REQUIRED
   # To: ✅ DEPLOYED - VERIFICATION COMPLETE
   ```

2. **Verify Application Access**:
   - Check that dashboards still load data (authenticated read access)
   - Verify backend pipelines can write data (service_role access)
   - Confirm no unauthorized data access attempts

3. **Monitor for 24 Hours**:
   - Watch for RLS policy violations in Supabase logs
   - Check application logs for unexpected 403 errors
   - Verify no functionality regressions

---

## 🆘 Rollback Plan (Emergency Only)

If RLS causes critical application failures:

```sql
-- EMERGENCY ROLLBACK - Use only if absolutely necessary
BEGIN;

-- Disable RLS (temporarily exposes data again)
ALTER TABLE public.financial_statements DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_schedule DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.real_payment DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.customer_data DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.historical_kpis DISABLE ROW LEVEL SECURITY;

COMMIT;
```

**⚠️ WARNING**: This re-exposes data. Only use if critical business functions are blocked. Immediately investigate and redeploy with corrected policies.

---

## 📞 Support

- **Supabase Support**: <support@supabase.com>
- **Internal Escalation**: #infra-alerts Slack channel
- **Documentation**: See `docs/security/SUPABASE_RLS_HARDENING.md`

---

**Last Updated**: 2026-02-04  
**Next Action**: Deploy migrations IMMEDIATELY using Option 1 or Option 2 above
