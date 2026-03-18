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

-- Add metadata comments for audit trail using a single literal definition.
DO $$
DECLARE
    audit_comment CONSTANT TEXT := 'RLS enabled: 2026-02-04';
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY ARRAY[
        'financial_statements',
        'payment_schedule',
        'real_payment',
        'loan_data',
        'customer_data',
        'historical_kpis'
    ]
    LOOP
        IF to_regclass(format('public.%I', table_name)) IS NOT NULL THEN
            EXECUTE format('COMMENT ON TABLE public.%I IS %L', table_name, audit_comment);
        END IF;
    END LOOP;
END $$;

COMMIT;
