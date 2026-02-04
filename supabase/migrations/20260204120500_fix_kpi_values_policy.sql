-- Harden RLS policies for monitoring.kpi_values
-- Date: 2026-02-04
-- Purpose: Replace overly permissive allow_insert policy
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- Drop old insecure policy (if present)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_schema = 'monitoring'
      AND table_name = 'kpi_values'
  ) THEN
    RAISE NOTICE 'Table monitoring.kpi_values does not exist, skipping policy changes.';
    RETURN;
  END IF;

  EXECUTE 'DROP POLICY IF EXISTS "allow_insert" ON monitoring.kpi_values';
END;
$$ LANGUAGE plpgsql;

-- Create policies safely (Postgres does not support CREATE POLICY IF NOT EXISTS)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_policies p
    WHERE p.policyname = 'service_role_insert_kpis'
      AND p.schemaname = 'monitoring'
      AND p.tablename = 'kpi_values'
  ) THEN
    CREATE POLICY "service_role_insert_kpis" ON monitoring.kpi_values
      FOR INSERT TO service_role
      USING (true)
      WITH CHECK ((auth.jwt() ->> 'role') = 'service_role');
  END IF;
EXCEPTION WHEN undefined_table THEN
  RAISE NOTICE 'Table monitoring.kpi_values does not exist, skipping policy creation.';
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_policies p
    WHERE p.policyname = 'internal_authenticated_insert_kpis'
      AND p.schemaname = 'monitoring'
      AND p.tablename = 'kpi_values'
  ) THEN
    CREATE POLICY "internal_authenticated_insert_kpis" ON monitoring.kpi_values
      FOR INSERT
      WITH CHECK (
        auth.role() = 'authenticated'
        AND auth.jwt()->>'email' LIKE '%@abaco.%'
      );
  END IF;
EXCEPTION WHEN undefined_table THEN
  RAISE NOTICE 'Table monitoring.kpi_values does not exist, skipping policy creation.';
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_catalog.pg_policies p
    WHERE p.policyname = 'authenticated_read_kpis'
      AND p.schemaname = 'monitoring'
      AND p.tablename = 'kpi_values'
  ) THEN
    CREATE POLICY "authenticated_read_kpis" ON monitoring.kpi_values
      FOR SELECT
      USING (auth.role() = 'authenticated');
  END IF;
EXCEPTION WHEN undefined_table THEN
  RAISE NOTICE 'Table monitoring.kpi_values does not exist, skipping policy creation.';
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Verification (run manually if needed):
-- SELECT policyname, cmd
-- FROM pg_policies
-- WHERE schemaname = 'monitoring' AND tablename = 'kpi_values'
-- ORDER BY policyname;
