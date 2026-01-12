-- Enable public read access for analytics_facts table and figma_dashboard view
-- Date: 2026-01-12

BEGIN;

-- 1. Ensure RLS is enabled on analytics_facts
ALTER TABLE public.analytics_facts ENABLE ROW LEVEL SECURITY;

-- 2. Create policy to allow public read access
-- This allows anyone with the anon key (or via Edge Functions) to read the data
DROP POLICY IF EXISTS "Allow public read-only access" ON public.analytics_facts;
CREATE POLICY "Allow public read-only access" ON public.analytics_facts
    FOR SELECT USING (true);

-- 3. Grant select on the view and table to anon and authenticated roles
GRANT SELECT ON public.analytics_facts TO anon, authenticated;
GRANT SELECT ON public.figma_dashboard TO anon, authenticated;

COMMIT;
