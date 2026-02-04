-- Enable RLS on All Public Tables (Addressing Supabase Security Alerts)
-- Date: 2026-02-04
-- Purpose: Address 8 security alerts by enabling RLS on all public tables

BEGIN;

-- ============================================================================
-- ENABLE RLS ON ALL PUBLIC TABLES
-- ============================================================================

-- Core data tables
ALTER TABLE IF EXISTS public.customer_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.loan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.real_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.analytics_facts ENABLE ROW LEVEL SECURITY;

-- KPI and historical tables
ALTER TABLE IF EXISTS public.kpi_timeseries_daily ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.historical_kpis ENABLE ROW LEVEL SECURITY;

-- Lineage and audit tables
ALTER TABLE IF EXISTS public.data_lineage ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_columns ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_dependencies ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.lineage_audit_log ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ENABLE RLS ON ANALYTICS SCHEMA TABLES
-- ============================================================================

ALTER TABLE IF EXISTS analytics.pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analytics.raw_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analytics.kpi_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS analytics.data_quality_results ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- CREATE READ-ONLY POLICIES FOR PUBLIC/ANON USERS
-- ============================================================================

-- Public schema tables: Allow read-only access for anon/authenticated users
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
        -- Check if policy already exists
        SELECT EXISTS (
            SELECT 1 
            FROM pg_policies 
            WHERE schemaname = 'public' 
            AND tablename = t 
            AND policyname = 'Allow public read-only access'
        ) INTO policy_exists;
        
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "Allow public read-only access" ON public.%I FOR SELECT USING (true);', t);
            RAISE NOTICE 'Created read policy for public.%', t;
        END IF;
    END LOOP;
END $$;

-- Analytics schema tables: Allow read-only access
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
            RAISE NOTICE 'Created read policy for analytics.%', t;
        END IF;
    END LOOP;
END $$;

-- ============================================================================
-- CREATE WRITE POLICIES FOR SERVICE_ROLE ONLY
-- ============================================================================

-- Public schema: Only service_role can INSERT/UPDATE/DELETE
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
        -- INSERT policy
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' AND tablename = t 
            AND policyname = 'Service role can insert'
        ) INTO policy_exists;
        
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "Service role can insert" ON public.%I FOR INSERT WITH CHECK (auth.role() = ''service_role'');', t);
        END IF;
        
        -- UPDATE policy
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'public' AND tablename = t 
            AND policyname = 'Service role can update'
        ) INTO policy_exists;
        
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "Service role can update" ON public.%I FOR UPDATE USING (auth.role() = ''service_role'');', t);
        END IF;
        
        -- DELETE policy
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

-- Analytics schema: Only service_role can write
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
        -- INSERT policy
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'analytics' AND tablename = t 
            AND policyname = 'Service role can insert'
        ) INTO policy_exists;
        
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "Service role can insert" ON analytics.%I FOR INSERT WITH CHECK (auth.role() = ''service_role'');', t);
        END IF;
        
        -- UPDATE policy
        SELECT EXISTS (
            SELECT 1 FROM pg_policies 
            WHERE schemaname = 'analytics' AND tablename = t 
            AND policyname = 'Service role can update'
        ) INTO policy_exists;
        
        IF NOT policy_exists THEN
            EXECUTE format('CREATE POLICY "Service role can update" ON analytics.%I FOR UPDATE USING (auth.role() = ''service_role'');', t);
        END IF;
        
        -- DELETE policy
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

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================

-- Run this to verify RLS is enabled on all tables:
-- SELECT schemaname, tablename, rowsecurity 
-- FROM pg_tables 
-- WHERE schemaname IN ('public', 'analytics') 
-- AND rowsecurity = false;

COMMIT;

-- ============================================================================
-- POST-DEPLOYMENT VERIFICATION
-- ============================================================================

-- Expected result: No rows (all tables have RLS enabled)
-- If any tables show up, they need RLS enabled manually

COMMENT ON TABLE public.customer_data IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.loan_data IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.real_payment IS 'RLS enabled: 2026-02-04';
