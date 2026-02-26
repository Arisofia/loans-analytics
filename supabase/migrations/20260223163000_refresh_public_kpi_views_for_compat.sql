-- Refresh public KPI views so PostgREST schema cache includes compatibility columns
-- added to monitoring.kpi_definitions / monitoring.kpi_values.

BEGIN;

DROP VIEW IF EXISTS public.kpi_values CASCADE;
CREATE VIEW public.kpi_values AS
SELECT * FROM monitoring.kpi_values;

DROP VIEW IF EXISTS public.kpi_definitions CASCADE;
CREATE VIEW public.kpi_definitions AS
SELECT * FROM monitoring.kpi_definitions;

GRANT SELECT ON public.kpi_values TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON public.kpi_values TO service_role;
GRANT SELECT ON public.kpi_definitions TO anon, authenticated, service_role;

COMMIT;
