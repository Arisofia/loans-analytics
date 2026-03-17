-- Fix loan_data_broadcast_trigger search_path vulnerability
-- Date: 2026-02-04
-- Purpose: Prevent SQL injection via mutable search_path on SECURITY DEFINER trigger function
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- Safe: set search_path for loan_data_broadcast_trigger if it exists (trigger function)
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

-- Verification (run manually if needed):
-- SELECT proname, proconfig
-- FROM pg_proc p
-- JOIN pg_namespace n ON p.pronamespace = n.oid
-- WHERE n.nspname = 'public'
--   AND p.proname = 'loan_data_broadcast_trigger';
