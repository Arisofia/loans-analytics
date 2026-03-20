-- Migration: Harden broadcast trigger security
-- Date: 2026-02-04
-- Purpose: Address security findings in the monitoring.broadcast_kpi_values trigger
-- Severity: MEDIUM - Potential for unauthorized trigger execution
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- ============================================================================
-- DROP AND RECREATE FUNCTION WITH SECURITY DEFINER
-- ============================================================================

-- The original function did not specify a security context or search_path,
-- which can be exploited if the search_path is manipulated.
-- SECURITY DEFINER ensures it runs as the owner (postgres).
-- SET search_path ensures it only looks in monitoring, public, and pg_temp.

CREATE OR REPLACE FUNCTION monitoring.broadcast_kpi_values()
RETURNS TRIGGER AS $$
BEGIN
    -- Only broadcast if the value has changed or it's a new insert
    IF (TG_OP = 'INSERT') OR (NEW.value IS DISTINCT FROM OLD.value) THEN
        PERFORM pg_notify(
            'monitoring_kpi_update',
            json_build_object(
                'id', NEW.id,
                'name', NEW.name,
                'value', NEW.value,
                'as_of', NEW.as_of
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = monitoring, public, pg_temp;

-- ============================================================================
-- RECREATE TRIGGER SAFELY
-- ============================================================================

DROP TRIGGER IF EXISTS broadcast_kpi_values_trigger ON monitoring.kpi_values;

CREATE TRIGGER broadcast_kpi_values_trigger
    AFTER INSERT OR UPDATE ON monitoring.kpi_values
    FOR EACH ROW
    EXECUTE FUNCTION monitoring.broadcast_kpi_values();

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    trigger_exists BOOLEAN;
    is_security_definer BOOLEAN;
BEGIN
    -- Check if trigger exists
    SELECT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'broadcast_kpi_values_trigger'
    ) INTO trigger_exists;
    
    -- Check if function is security definer
    SELECT prosecdef INTO is_security_definer
    FROM pg_proc
    WHERE proname = 'broadcast_kpi_values';
    
    IF trigger_exists AND is_security_definer THEN
        RAISE NOTICE 'Broadcast trigger successfully hardened with SECURITY DEFINER';
    ELSE
        IF NOT trigger_exists THEN RAISE WARNING 'Trigger broadcast_kpi_values_trigger not found'; END IF;
        IF NOT is_security_definer THEN RAISE WARNING 'Function broadcast_kpi_values is NOT security definer'; END IF;
    END IF;
END $$;

-- Add metadata for audit trail
COMMENT ON FUNCTION monitoring.broadcast_kpi_values() IS 
  'KPI broadcast trigger. Hardened on 2026-02-04 with SECURITY DEFINER and explicit search_path.';

COMMIT;
