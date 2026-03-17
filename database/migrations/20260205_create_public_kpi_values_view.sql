CREATE OR REPLACE VIEW public.kpi_values AS
SELECT * FROM monitoring.kpi_values;

ALTER VIEW public.kpi_values OWNER TO postgres;

GRANT SELECT ON public.kpi_values TO anon, authenticated, service_role;
