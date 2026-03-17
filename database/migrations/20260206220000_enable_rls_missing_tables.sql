-- Enable RLS on financial_statements and payment_schedule
-- Date: 2026-02-06
-- Purpose: Fix gap where these tables had policies but RLS was not enabled

BEGIN;

ALTER TABLE IF EXISTS public.financial_statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.payment_schedule ENABLE ROW LEVEL SECURITY;

COMMIT;
