-- Migration: Fix loan_data_broadcast_trigger search_path vulnerability
-- Date: 2026-02-04
-- Purpose: Prevent SQL injection via mutable search_path
-- Severity: HIGH - Supabase security alert
-- Related: SECURITY_STATUS_2026_02_04.md

BEGIN;

-- ============================================================================
-- FIX: Pin search_path to prevent SQL injection
-- ============================================================================

-- The function loan_data_broadcast_trigger() previously had a mutable search_path,
-- which could allow an attacker to manipulate schema resolution and inject malicious code.
--
-- By setting search_path to 'public, pg_temp', we ensure:
-- 1. Only objects in the 'public' schema are resolved
-- 2. Temporary objects are in pg_temp (standard practice)
-- 3. No user-controlled schemas can intercept function calls

ALTER FUNCTION public.loan_data_broadcast_trigger()
  SET search_path = public, pg_temp;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    func_search_path text;
BEGIN
    SELECT pg_get_functiondef(oid)
    INTO func_search_path
    FROM pg_proc
    WHERE proname = 'loan_data_broadcast_trigger'
    AND pronamespace = 'public'::regnamespace;
    
    IF func_search_path LIKE '%SET search_path%' THEN
        RAISE NOTICE 'Function search_path successfully pinned';
    ELSE
        RAISE WARNING 'Function search_path may not be properly set';
    END IF;
END $$;

-- Add audit metadata
COMMENT ON FUNCTION public.loan_data_broadcast_trigger() IS 
  'Broadcasts loan_data changes. Search path pinned on 2026-02-04 to prevent SQL injection.';

COMMIT;

-- ============================================================================
-- SECURITY ADVISORY
-- ============================================================================

-- What was the vulnerability?
-- -------------------------
-- Functions without a pinned search_path can be exploited if an attacker:
-- 1. Creates a schema they control
-- 2. Sets search_path to include their schema
-- 3. Creates functions/tables with names that match those used by the target function
-- 4. Tricks the function into calling their malicious code instead
--
-- Example attack:
--   CREATE SCHEMA evil;
--   CREATE FUNCTION evil.pg_notify(...) RETURNS void AS $$ ... malicious code ... $$;
--   SET search_path = evil, public;
--   -- Now any call to pg_notify() goes to evil.pg_notify() instead
--
-- The fix:
-- --------
-- By setting `search_path = public, pg_temp`, the function always resolves:
-- - public.* functions and tables (expected behavior)
-- - pg_temp.* temporary objects (standard practice)
-- - Nothing from user-controlled schemas
--
-- References:
-- -----------
-- - https://www.postgresql.org/docs/current/ddl-schemas.html#DDL-SCHEMAS-PATH
-- - https://supabase.com/docs/guides/database/postgres/security#search-path-injection

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Run this to confirm the fix:
--
-- SELECT 
--   p.proname AS function_name,
--   pg_get_functiondef(p.oid) AS definition
-- FROM pg_proc p
-- JOIN pg_namespace n ON p.pronamespace = n.oid
-- WHERE n.nspname = 'public'
-- AND p.proname = 'loan_data_broadcast_trigger';
--
-- Expected: definition contains "SET search_path = public, pg_temp"
