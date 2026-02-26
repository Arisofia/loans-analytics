-- Migration: Enable Row Level Security on sensitive tables
-- Date: 2026-02-04
-- Purpose: Address Supabase security alerts - enable RLS on all public tables
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- ============================================================================
-- ENABLE RLS ON PUBLIC SCHEMA TABLES
-- ============================================================================

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

-- ============================================================================
-- ENABLE RLS ON MONITORING SCHEMA TABLES
-- ============================================================================

ALTER TABLE IF EXISTS monitoring.kpi_values ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- This query should return no rows (all tables have RLS enabled)
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM pg_tables
    WHERE schemaname IN ('public', 'monitoring')
    AND rowsecurity = false
    AND tablename NOT LIKE 'pg_%'
    AND tablename NOT LIKE 'sql_%';
    
    IF table_count > 0 THEN
        RAISE WARNING 'Found % tables without RLS enabled', table_count;
    ELSE
        RAISE NOTICE 'RLS successfully enabled on all sensitive tables';
    END IF;
END $$;

-- Add metadata comments for audit trail
COMMENT ON TABLE public.financial_statements IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.payment_schedule IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.real_payment IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.loan_data IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.customer_data IS 'RLS enabled: 2026-02-04';
COMMENT ON TABLE public.historical_kpis IS 'RLS enabled: 2026-02-04';

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERY
-- ============================================================================

-- Run this to verify RLS is enabled:
--
-- SELECT schemaname, tablename, rowsecurity
-- FROM pg_tables
-- WHERE schemaname IN ('public', 'monitoring')
-- AND tablename IN (
--   'financial_statements', 'payment_schedule', 'real_payment',
--   'loan_data', 'customer_data', 'historical_kpis', 'kpi_values'
-- )
-- ORDER BY schemaname, tablename;
--
-- Expected: rowsecurity = true for all rows
