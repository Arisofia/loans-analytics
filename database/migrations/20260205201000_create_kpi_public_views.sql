-- Create public schema views for monitoring data access
-- Date: 2026-02-05
-- Purpose: Expose monitoring schema tables via public schema (PostgREST API accessible)
-- This allows RLS tests to access monitoring schema without manually configuring "Exposed schemas"

BEGIN;

-- Create kpi_values view in public schema
DROP VIEW IF EXISTS public.kpi_values CASCADE;
CREATE VIEW public.kpi_values AS
  SELECT * FROM monitoring.kpi_values;

-- Grant SELECT to service_role and authenticated
GRANT SELECT ON public.kpi_values TO service_role, authenticated;

-- Create kpi_definitions view in public schema  
DROP VIEW IF EXISTS public.kpi_definitions CASCADE;
CREATE VIEW public.kpi_definitions AS
  SELECT * FROM monitoring.kpi_definitions;

-- Grant SELECT to service_role and authenticated
GRANT SELECT ON public.kpi_definitions TO service_role, authenticated;

COMMIT;

-- Verification (manual):
-- SELECT schemaname, viewname FROM information_schema.views WHERE schemaname = 'public' AND viewname LIKE 'kpi%';
-- SELECT table_privileges FROM information_schema.table_privileges WHERE table_schema = 'public' AND table_name LIKE 'kpi%';
