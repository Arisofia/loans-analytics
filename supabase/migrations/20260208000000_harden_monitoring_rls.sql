-- Harden monitoring RLS (defense-in-depth)
--
-- RLS is already enabled via 20260207100000_create_operational_events_commands.sql.
-- This idempotent migration serves as an explicit audit checkpoint:
--   1. Re-affirms RLS is enabled on both monitoring tables.
--   2. Adds INSERT-only policy for service_role on operational_events
--      (the original migration grants ALL; this is a no-op safety net).
--
-- Safe to run multiple times — all statements are idempotent.

-- Re-affirm RLS enablement (idempotent)
ALTER TABLE IF EXISTS monitoring.operational_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS monitoring.commands ENABLE ROW LEVEL SECURITY;

-- Idempotent: create INSERT-specific policy only if it doesn't already exist.
-- Uses DO block because CREATE POLICY lacks IF NOT EXISTS.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE schemaname = 'monitoring'
          AND tablename  = 'operational_events'
          AND policyname = 'service_role_insert_events'
    ) THEN
        CREATE POLICY service_role_insert_events
            ON monitoring.operational_events
            FOR INSERT
            TO service_role
            WITH CHECK (true);
    END IF;
END;
$$;
