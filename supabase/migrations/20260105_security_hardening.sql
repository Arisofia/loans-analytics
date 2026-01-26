-- Security Hardening: Enable RLS and set default policies
-- Date: 2026-01-05

BEGIN;

-- 1. Enable RLS on all public tables
ALTER TABLE public.customer_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.real_payment ENABLE ROW LEVEL SECURITY;

-- 2. Enable RLS on analytics schema tables
ALTER TABLE analytics.pipeline_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.raw_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.kpi_values ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.data_quality_results ENABLE ROW LEVEL SECURITY;

-- 3. Create policies for public access (Read-Only)
-- Assumption: The dashboard needs to read these tables using the anon key.

DO $$
DECLARE
    t text;
BEGIN
    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('customer_data', 'loan_data', 'real_payment')
    LOOP
        EXECUTE format('CREATE POLICY "Allow public read-only access" ON public.%I FOR SELECT USING (true);', t);
    END LOOP;

    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = 'analytics' AND table_name IN ('pipeline_runs', 'raw_artifacts', 'kpi_values', 'data_quality_results')
    LOOP
        EXECUTE format('CREATE POLICY "Allow public read-only access" ON analytics.%I FOR SELECT USING (true);', t);
    END LOOP;
END $$;

-- 4. Restrict Write Access
-- Only service_role or authenticated users with specific roles should write.
-- Since we are in a prototype phase, we leave Write policies for later implementation
-- but by enabling RLS and not providing a write policy, write access is denied for 'anon'.

COMMIT;
