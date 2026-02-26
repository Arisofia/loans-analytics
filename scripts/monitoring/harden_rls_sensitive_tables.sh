#!/usr/bin/env bash

set -euo pipefail

# Apply RLS hardening for sensitive tables while preserving public KPI views.
# Usage:
#   DATABASE_URL=postgres://... ./scripts/monitoring/harden_rls_sensitive_tables.sh
#
# Notes:
# - Requires psql.
# - Applies only policy/grant changes (no schema migrations).

if ! command -v psql >/dev/null 2>&1; then
  echo "Missing required command: psql" >&2
  exit 1
fi

DB_URL="${DATABASE_URL:-${SUPABASE_DB_URL:-${POSTGRES_URL:-}}}"
if [[ -z "${DB_URL}" ]]; then
  echo "Set DATABASE_URL (or SUPABASE_DB_URL / POSTGRES_URL) before running." >&2
  exit 1
fi

psql "${DB_URL}" -v ON_ERROR_STOP=1 <<'SQL'
BEGIN;

DO $$
DECLARE
  p RECORD;
BEGIN
  FOR p IN
    SELECT schemaname, tablename, policyname
    FROM pg_policies
    WHERE schemaname IN ('public', 'analytics')
      AND cmd = 'SELECT'
      AND lower(regexp_replace(COALESCE(qual, ''), '\s+', '', 'g')) IN ('true', '(true)')
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS %I ON %I.%I', p.policyname, p.schemaname, p.tablename);
  END LOOP;
END;
$$;

DO $$
DECLARE
  t RECORD;
BEGIN
  FOR t IN
    SELECT * FROM (VALUES
      ('public', 'customer_data'),
      ('public', 'loan_data'),
      ('public', 'real_payment'),
      ('public', 'analytics_facts'),
      ('public', 'financial_statements'),
      ('public', 'payment_schedule'),
      ('public', 'historical_kpis'),
      ('public', 'data_lineage'),
      ('public', 'lineage_columns'),
      ('public', 'lineage_dependencies'),
      ('public', 'lineage_audit_log'),
      ('analytics', 'pipeline_runs'),
      ('analytics', 'raw_artifacts'),
      ('analytics', 'kpi_values'),
      ('analytics', 'data_quality_results')
    ) AS sensitive_tables(schema_name, table_name)
  LOOP
    IF EXISTS (
      SELECT 1
      FROM pg_tables
      WHERE schemaname = t.schema_name
        AND tablename = t.table_name
    ) THEN
      EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', t.schema_name, t.table_name);
      EXECUTE format('REVOKE ALL ON TABLE %I.%I FROM anon, authenticated', t.schema_name, t.table_name);
      EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE %I.%I TO service_role', t.schema_name, t.table_name);

      IF NOT EXISTS (
        SELECT 1
        FROM pg_policies
        WHERE schemaname = t.schema_name
          AND tablename = t.table_name
          AND policyname = 'service_role_full_access'
      ) THEN
        EXECUTE format(
          'CREATE POLICY service_role_full_access ON %I.%I FOR ALL TO service_role USING (auth.role() = ''service_role'') WITH CHECK (auth.role() = ''service_role'')',
          t.schema_name,
          t.table_name
        );
      END IF;
    END IF;
  END LOOP;
END;
$$;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'monitoring' AND tablename = 'kpi_values') THEN
    ALTER TABLE monitoring.kpi_values ENABLE ROW LEVEL SECURITY;
    DROP POLICY IF EXISTS monitoring_read_all ON monitoring.kpi_values;
    DROP POLICY IF EXISTS authenticated_read_kpis ON monitoring.kpi_values;
    DROP POLICY IF EXISTS internal_authenticated_insert_kpis ON monitoring.kpi_values;
    REVOKE ALL ON TABLE monitoring.kpi_values FROM anon, authenticated;
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE monitoring.kpi_values TO service_role;
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'monitoring'
        AND tablename = 'kpi_values'
        AND policyname = 'service_role_full_access'
    ) THEN
      CREATE POLICY service_role_full_access
        ON monitoring.kpi_values
        FOR ALL
        TO service_role
        USING (auth.role() = 'service_role')
        WITH CHECK (auth.role() = 'service_role');
    END IF;
  END IF;

  IF EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'monitoring' AND tablename = 'kpi_definitions') THEN
    ALTER TABLE monitoring.kpi_definitions ENABLE ROW LEVEL SECURITY;
    REVOKE ALL ON TABLE monitoring.kpi_definitions FROM anon, authenticated;
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE monitoring.kpi_definitions TO service_role;
    IF NOT EXISTS (
      SELECT 1 FROM pg_policies
      WHERE schemaname = 'monitoring'
        AND tablename = 'kpi_definitions'
        AND policyname = 'service_role_full_access'
    ) THEN
      CREATE POLICY service_role_full_access
        ON monitoring.kpi_definitions
        FOR ALL
        TO service_role
        USING (auth.role() = 'service_role')
        WITH CHECK (auth.role() = 'service_role');
    END IF;
  END IF;
END;
$$;

DROP VIEW IF EXISTS public.kpi_values CASCADE;
CREATE VIEW public.kpi_values AS
SELECT
  id, kpi_id, kpi_key, as_of_date, value, value_num, value_json,
  status, "timestamp", computed_at, snapshot_id, run_id, inputs_hash,
  created_at, updated_at
FROM monitoring.kpi_values;

DROP VIEW IF EXISTS public.kpi_definitions CASCADE;
CREATE VIEW public.kpi_definitions AS
SELECT
  kpi_key, id, name, display_name, description, formula, category, unit,
  direction, "window", basis, green, yellow, red, threshold_warning,
  threshold_critical, owner_agent, source_tables, version, created_at, updated_at
FROM monitoring.kpi_definitions;

GRANT SELECT ON public.kpi_values TO anon, authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON public.kpi_values TO service_role;
GRANT SELECT ON public.kpi_definitions TO anon, authenticated, service_role;

REVOKE ALL ON FUNCTION monitoring.upsert_daily_kpi_snapshot(DATE, TEXT, TEXT) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION monitoring.upsert_daily_kpi_snapshot(DATE, TEXT, TEXT) TO service_role;

COMMIT;
SQL

echo "RLS hardening applied successfully."
