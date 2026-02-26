-- Create idempotent daily KPI snapshot upsert function and schedule.
-- Safe behavior:
--   1) Upserts one row per KPI definition for a target date.
--   2) If pg_cron is unavailable, function is still created and scheduling is skipped.

BEGIN;

CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE OR REPLACE FUNCTION monitoring.upsert_daily_kpi_snapshot(
  p_target_date DATE DEFAULT CURRENT_DATE,
  p_snapshot_id TEXT DEFAULT 'auto-daily',
  p_run_id TEXT DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = monitoring, public
AS $$
DECLARE
  v_rows INTEGER := 0;
  v_effective_run_id TEXT := COALESCE(p_run_id, 'daily_snapshot_' || to_char(p_target_date, 'YYYYMMDD'));
BEGIN
  WITH latest AS (
    SELECT DISTINCT ON (kv.kpi_key)
      kv.kpi_key,
      kv.kpi_id,
      COALESCE(kv.value_num, kv.value) AS effective_value,
      kv.status,
      kv."timestamp" AS source_timestamp
    FROM monitoring.kpi_values kv
    WHERE COALESCE(kv.value_num, kv.value) IS NOT NULL
    ORDER BY kv.kpi_key, kv.as_of_date DESC, kv.computed_at DESC NULLS LAST, kv.created_at DESC NULLS LAST
  ),
  upserted AS (
    INSERT INTO monitoring.kpi_values (
      kpi_id,
      kpi_key,
      value,
      value_num,
      "timestamp",
      computed_at,
      as_of_date,
      status,
      snapshot_id,
      run_id,
      inputs_hash
    )
    SELECT
      COALESCE(l.kpi_id, kd.id) AS kpi_id,
      kd.kpi_key,
      l.effective_value AS value,
      l.effective_value AS value_num,
      COALESCE(l.source_timestamp, NOW()) AS "timestamp",
      NOW() AS computed_at,
      p_target_date AS as_of_date,
      COALESCE(l.status, 'green') AS status,
      p_snapshot_id AS snapshot_id,
      v_effective_run_id AS run_id,
      'auto-snapshot-v1' AS inputs_hash
    FROM monitoring.kpi_definitions kd
    LEFT JOIN latest l ON l.kpi_key = kd.kpi_key
    WHERE l.kpi_key IS NOT NULL
    ON CONFLICT (as_of_date, kpi_key, snapshot_id)
    DO UPDATE SET
      kpi_id = EXCLUDED.kpi_id,
      value = EXCLUDED.value,
      value_num = EXCLUDED.value_num,
      "timestamp" = EXCLUDED."timestamp",
      computed_at = EXCLUDED.computed_at,
      status = EXCLUDED.status,
      run_id = EXCLUDED.run_id,
      inputs_hash = EXCLUDED.inputs_hash
    RETURNING 1
  )
  SELECT COUNT(*) INTO v_rows FROM upserted;

  RETURN COALESCE(v_rows, 0);
END;
$$;

COMMENT ON FUNCTION monitoring.upsert_daily_kpi_snapshot(DATE, TEXT, TEXT)
IS 'Upserts one KPI snapshot row per definition for a target date using latest known KPI values.';

DO $$
DECLARE
  v_job_id BIGINT;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pg_cron') THEN
    RAISE NOTICE 'pg_cron extension not available; skipping cron schedule setup.';
    RETURN;
  END IF;

  BEGIN
    CREATE EXTENSION IF NOT EXISTS pg_cron;
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Could not enable pg_cron: %', SQLERRM;
    RETURN;
  END;

  IF to_regclass('cron.job') IS NULL THEN
    RAISE NOTICE 'cron.job relation unavailable; skipping cron schedule setup.';
    RETURN;
  END IF;

  SELECT jobid INTO v_job_id
  FROM cron.job
  WHERE jobname = 'monitoring_daily_kpi_snapshot'
  ORDER BY jobid DESC
  LIMIT 1;

  IF v_job_id IS NOT NULL THEN
    PERFORM cron.unschedule(v_job_id);
  END IF;

  PERFORM cron.schedule(
    'monitoring_daily_kpi_snapshot',
    '15 3 * * *',
    'SELECT monitoring.upsert_daily_kpi_snapshot(CURRENT_DATE, ''auto-daily'', NULL);'
  );
END;
$$;

COMMIT;
