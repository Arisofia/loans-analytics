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
-- STEP 2: CREATE RLS POLICIES (IDEMPOTENT)
-- ============================================================================
BEGIN;

-- Public schema: read-only for anon/authenticated users
DO $$
DECLARE
  t text;
  policy_exists boolean;
BEGIN
  FOR t IN
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
      AND table_name NOT LIKE 'pg_%'
  LOOP
    SELECT EXISTS (
      SELECT 1
      FROM pg_policies
      WHERE schemaname = 'public'
        AND tablename = t
        AND policyname = 'Allow public read-only access'
    ) INTO policy_exists;

    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Allow public read-only access" ON public.%I FOR SELECT USING (true);', t);
    END IF;
  END LOOP;
END $$;

-- Analytics schema: read-only policies
DO $$
DECLARE
  t text;
  policy_exists boolean;
BEGIN
  FOR t IN
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'analytics'
      AND table_type = 'BASE TABLE'
  LOOP
    SELECT EXISTS (
      SELECT 1
      FROM pg_policies
      WHERE schemaname = 'analytics'
        AND tablename = t
        AND policyname = 'Allow public read-only access'
    ) INTO policy_exists;

    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Allow public read-only access" ON analytics.%I FOR SELECT USING (true);', t);
    END IF;
  END LOOP;
END $$;

-- Public schema: service_role write policies
DO $$
DECLARE
  t text;
  policy_exists boolean;
BEGIN
  FOR t IN
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
      AND table_name NOT LIKE 'pg_%'
  LOOP
    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'public' AND tablename = t
        AND policyname = 'Service role can insert'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can insert" ON public.%I FOR INSERT WITH CHECK (auth.role() = ''service_role'');', t);
    END IF;

    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'public' AND tablename = t
        AND policyname = 'Service role can update'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can update" ON public.%I FOR UPDATE USING (auth.role() = ''service_role'');', t);
    END IF;

    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'public' AND tablename = t
        AND policyname = 'Service role can delete'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can delete" ON public.%I FOR DELETE USING (auth.role() = ''service_role'');', t);
    END IF;
  END LOOP;
END $$;

-- Analytics schema: service_role write policies
DO $$
DECLARE
  t text;
  policy_exists boolean;
BEGIN
  FOR t IN
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'analytics'
      AND table_type = 'BASE TABLE'
  LOOP
    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'analytics' AND tablename = t
        AND policyname = 'Service role can insert'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can insert" ON analytics.%I FOR INSERT WITH CHECK (auth.role() = ''service_role'');', t);
    END IF;

    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'analytics' AND tablename = t
        AND policyname = 'Service role can update'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can update" ON analytics.%I FOR UPDATE USING (auth.role() = ''service_role'');', t);
    END IF;

    SELECT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'analytics' AND tablename = t
        AND policyname = 'Service role can delete'
    ) INTO policy_exists;
    IF NOT policy_exists THEN
      EXECUTE format('CREATE POLICY "Service role can delete" ON analytics.%I FOR DELETE USING (auth.role() = ''service_role'');', t);
    END IF;
  END LOOP;
END $$;

COMMIT;

-- VERIFY: Should show 2+ policies per table
SELECT schemaname, tablename, COUNT(*) as policy_count
FROM pg_policies
WHERE schemaname IN ('public', 'analytics')
GROUP BY schemaname, tablename
ORDER BY schemaname, tablename;
```

**Expected Result**: Each table has at least 2 policies

---

## Step 3: Fix Function Security (Copy this entire block)

```sql
-- ============================================================================
-- STEP 3: FIX FUNCTION SEARCH_PATH VULNERABILITY
-- ============================================================================
BEGIN;

DO $$
DECLARE
  func_oid oid;
BEGIN
  SELECT p.oid
  INTO func_oid
  FROM pg_proc p
  JOIN pg_namespace n ON n.oid = p.pronamespace
  WHERE n.nspname = 'public'
    AND p.proname = 'loan_data_broadcast_trigger'
    AND p.prorettype = 'pg_catalog.trigger'::regtype;

  IF func_oid IS NOT NULL THEN
    EXECUTE 'ALTER FUNCTION public.loan_data_broadcast_trigger() SET search_path = public, pg_temp';
  END IF;
END;
$$ LANGUAGE plpgsql;

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

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'monitoring'
      AND table_name = 'kpi_values'
  ) THEN
    EXECUTE 'DROP POLICY IF EXISTS "allow_insert" ON monitoring.kpi_values';

    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'monitoring'
        AND tablename = 'kpi_values'
        AND policyname = 'service_role_insert_kpis'
    ) THEN
      EXECUTE 'CREATE POLICY "service_role_insert_kpis" ON monitoring.kpi_values FOR INSERT WITH CHECK (auth.jwt()->>''role'' = ''service_role'')';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'monitoring'
        AND tablename = 'kpi_values'
        AND policyname = 'internal_authenticated_insert_kpis'
    ) THEN
      EXECUTE 'CREATE POLICY "internal_authenticated_insert_kpis" ON monitoring.kpi_values FOR INSERT WITH CHECK (auth.role() = ''authenticated'' AND auth.jwt()->>''email'' LIKE ''%@abaco.%'')';
    END IF;

    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'monitoring'
        AND tablename = 'kpi_values'
        AND policyname = 'authenticated_read_kpis'
    ) THEN
      EXECUTE 'CREATE POLICY "authenticated_read_kpis" ON monitoring.kpi_values FOR SELECT USING (auth.role() = ''authenticated'')';
    END IF;
  END IF;
END $$;

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
