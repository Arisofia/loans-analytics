# 🚨 MANUAL DEPLOYMENT - Copy & Paste into Supabase SQL Editor

**Open**: <https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/sql/new>

---

## Step 1: Enable RLS (Copy this entire block)

```sql
-- ============================================================================
-- STEP 1: ENABLE RLS ON ALL SENSITIVE TABLES
-- ============================================================================
BEGIN;

-- Financial and operational tables
ALTER TABLE IF EXISTS public.financial_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.payment_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.real_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.loan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.customer_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.historical_kpis ENABLE ROW LEVEL SECURITY;

-- Analytics and KPI tables  
ALTER TABLE IF EXISTS public.kpi_timeseries_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.analytics_facts ENABLE ROW LEVEL SECURITY;

-- Lineage and audit tables
ALTER TABLE IF EXISTS public.data_lineage ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_audit_log ENABLE ROW LEVEL SECURITY;

-- Monitoring tables
ALTER TABLE IF EXISTS monitoring.kpi_values ENABLE ROW LEVEL SECURITY;

COMMIT;

-- VERIFY: Should return TRUE for all tables
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname IN ('public', 'monitoring')
AND tablename IN (
  'financial_statements', 'payment_schedule', 'real_payment',
  'loan_data', 'customer_data', 'historical_kpis', 'kpi_values'
)
ORDER BY schemaname, tablename;
```

**Expected Result**: All tables show `rowsecurity = true`

---

## Step 2: Create RLS Policies (Copy this entire block)

```sql
-- ============================================================================
-- STEP 2: CREATE RLS POLICIES
-- ============================================================================
BEGIN;

-- Customer Data Policies (user-owned data)
CREATE POLICY IF NOT EXISTS "customer_read_own" ON public.customer_data
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY IF NOT EXISTS "service_role_manage_customers" ON public.customer_data
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Loan Data Policies (internal read, service write)
CREATE POLICY IF NOT EXISTS "authenticated_read_loans" ON public.loan_data
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_loans" ON public.loan_data
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Payment Schedule Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_payment_schedule" ON public.payment_schedule
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_payment_schedule" ON public.payment_schedule
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Real Payment Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_payments" ON public.real_payment
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_payments" ON public.real_payment
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Financial Statements Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_financial" ON public.financial_statements
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_financial" ON public.financial_statements
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Historical KPIs Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_historical_kpis" ON public.historical_kpis
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_historical_kpis" ON public.historical_kpis
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- KPI Timeseries Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_kpi_timeseries" ON public.kpi_timeseries_daily
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_kpi_timeseries" ON public.kpi_timeseries_daily
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Analytics Facts Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_analytics_facts" ON public.analytics_facts
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_analytics_facts" ON public.analytics_facts
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

-- Lineage Policies
CREATE POLICY IF NOT EXISTS "authenticated_read_lineage" ON public.data_lineage
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_lineage" ON public.data_lineage
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "authenticated_read_lineage_columns" ON public.lineage_columns
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_lineage_columns" ON public.lineage_columns
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "authenticated_read_lineage_deps" ON public.lineage_dependencies
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_lineage_deps" ON public.lineage_dependencies
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "authenticated_read_lineage_audit" ON public.lineage_audit_log
  FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "service_role_manage_lineage_audit" ON public.lineage_audit_log
  FOR ALL USING (auth.jwt()->>'role' = 'service_role');

COMMIT;

-- VERIFY: Should show 2+ policies per table
SELECT schemaname, tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname = 'public'
GROUP BY schemaname, tablename
ORDER BY tablename;
```

**Expected Result**: Each table has at least 2 policies

---

## Step 3: Fix Function Security (Copy this entire block)

```sql
-- ============================================================================
-- STEP 3: FIX FUNCTION SEARCH_PATH VULNERABILITY
-- ============================================================================
BEGIN;

ALTER FUNCTION IF EXISTS public.loan_data_broadcast_trigger() 
  SET search_path = public, pg_temp;

COMMIT;

-- VERIFY: Should show search_path configuration
SELECT proname, proconfig
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname = 'loan_data_broadcast_trigger';
```

**Expected Result**: `proconfig` includes `{search_path=public,pg_temp}`

---

## Step 4: Harden KPI Policy (Copy this entire block)

```sql
-- ============================================================================
-- STEP 4: FIX KPI_VALUES OVERLY PERMISSIVE POLICY
-- ============================================================================
BEGIN;

-- Drop old insecure policy
DROP POLICY IF EXISTS "allow_insert" ON monitoring.kpi_values;

-- Create restricted policies
CREATE POLICY IF NOT EXISTS "service_role_insert_kpis" ON monitoring.kpi_values
  FOR INSERT WITH CHECK (auth.jwt()->>'role' = 'service_role');

CREATE POLICY IF NOT EXISTS "internal_authenticated_insert_kpis" ON monitoring.kpi_values
  FOR INSERT WITH CHECK (
    auth.role() = 'authenticated' 
    AND auth.jwt()->>'email' LIKE '%@abaco.%'
  );

CREATE POLICY IF NOT EXISTS "authenticated_read_kpis" ON monitoring.kpi_values
  FOR SELECT USING (auth.role() = 'authenticated');

COMMIT;

-- VERIFY: Should NOT show "allow_insert" policy
SELECT policyname, cmd
FROM pg_policies
WHERE schemaname = 'monitoring' AND tablename = 'kpi_values'
ORDER BY policyname;
```

**Expected Result**: No "allow_insert" policy; shows 3 new policies

---

## ✅ FINAL VERIFICATION

```sql
-- Check all RLS-enabled tables and policy counts
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
    'loan_data', 'customer_data', 'historical_kpis', 'kpi_values'
  )
GROUP BY t.schemaname, t.tablename, t.rowsecurity
ORDER BY t.schemaname, t.tablename;
```

**Expected Result**:
- `rls_enabled` = `true` for ALL tables
- `policy_count` ≥ 2 for each table

---

## 🎉 Success Checklist

After running all 4 steps:

- [ ] All verification queries passed
- [ ] Supabase Security Advisor shows 0 issues (was 8)
- [ ] No "allow_insert" policy on kpi_values
- [ ] Function search_path is pinned
- [ ] Update `docs/SECURITY_STATUS_REPORT.md` status to ✅ DEPLOYED

---

**Deployment Time**: ~2 minutes  
**Last Updated**: 2026-02-04
