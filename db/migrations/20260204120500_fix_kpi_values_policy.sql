-- Migration: Harden RLS policies for monitoring.kpi_values
-- Date: 2026-02-04
-- Purpose: Fix overly permissive "allow_insert" policy
-- Severity: MEDIUM - Allows unrestricted inserts
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- ============================================================================
-- DROP INSECURE POLICY
-- ============================================================================

-- The original "allow_insert" policy had no restrictions (WITH CHECK (true)),
-- allowing any user to insert arbitrary KPI values. This violates least-privilege.

DROP POLICY IF EXISTS "allow_insert" ON monitoring.kpi_values;

-- ============================================================================
-- CREATE SECURE POLICIES
-- ============================================================================

-- Shared literal used by policies and trigger defaults.
CREATE OR REPLACE FUNCTION monitoring.service_role_name()
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
AS $$
    SELECT 'service_role'::TEXT
$$;

-- Policy 1: Service role has full access (for pipeline/backend)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_policies p
        WHERE p.policyname = 'Service role full access to KPIs'
        AND p.schemaname = 'monitoring'
        AND p.tablename = 'kpi_values'
    ) THEN
        CREATE POLICY "Service role full access to KPIs" ON monitoring.kpi_values
          FOR ALL
          USING (auth.jwt()->>'role' = monitoring.service_role_name())
          WITH CHECK (auth.jwt()->>'role' = monitoring.service_role_name());
    END IF;
END $$;

-- Policy 2: Authenticated internal users can insert (for manual corrections)
-- Restricted to @abaco.* email domain
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_policies p
        WHERE p.policyname = 'Internal users insert KPIs'
        AND p.schemaname = 'monitoring'
        AND p.tablename = 'kpi_values'
    ) THEN
        CREATE POLICY "Internal users insert KPIs" ON monitoring.kpi_values
          FOR INSERT
          WITH CHECK (
            auth.jwt()->>'role' = 'authenticated'
            AND auth.jwt()->>'email' LIKE '%@abaco.%'
          );
    END IF;
END $$;

-- Policy 3: Authenticated users can read KPIs (for dashboards)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_catalog.pg_policies p
        WHERE p.policyname = 'Authenticated users read KPIs'
        AND p.schemaname = 'monitoring'
        AND p.tablename = 'kpi_values'
    ) THEN
        CREATE POLICY "Authenticated users read KPIs" ON monitoring.kpi_values
          FOR SELECT
          USING (auth.jwt()->>'role' IN ('authenticated', monitoring.service_role_name()));
    END IF;
END $$;

-- ============================================================================
-- ADD AUDIT TRAIL
-- ============================================================================

-- Add created_by column if it doesn't exist (for accountability)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'monitoring'
        AND table_name = 'kpi_values'
        AND column_name = 'created_by'
    ) THEN
        ALTER TABLE monitoring.kpi_values ADD COLUMN created_by TEXT;
        COMMENT ON COLUMN monitoring.kpi_values.created_by IS 'User ID or service that created this KPI record';
    END IF;
END $$;

-- Add trigger to auto-populate created_by
CREATE OR REPLACE FUNCTION monitoring.set_created_by()
RETURNS TRIGGER AS $$
BEGIN
    NEW.created_by := COALESCE(
        auth.jwt()->>'sub',  -- User ID from JWT
        monitoring.service_role_name()  -- Default for service role
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = monitoring, public, pg_temp;

DROP TRIGGER IF EXISTS set_created_by_trigger ON monitoring.kpi_values;
CREATE TRIGGER set_created_by_trigger
    BEFORE INSERT ON monitoring.kpi_values
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.set_created_by();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    policy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE schemaname = 'monitoring'
    AND tablename = 'kpi_values';
    
    IF policy_count >= 3 THEN
        RAISE NOTICE 'KPI policies successfully hardened (% policies found)', policy_count;
    ELSE
        RAISE WARNING 'Expected at least 3 policies, found %', policy_count;
    END IF;
END $$;

-- Add metadata for audit trail
COMMENT ON TABLE monitoring.kpi_values IS 
  'KPI values table. RLS policies hardened on 2026-02-04 to restrict inserts to service_role and internal authenticated users.';

COMMIT;
