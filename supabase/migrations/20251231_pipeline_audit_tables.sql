-- =====================================================================
-- Abaco Analytics - Pipeline lineage + audit tables (minimal)
-- Schema: analytics
-- Date: 2025-12-31
--
-- Goals:
-- - point-in-time reconstruction
-- - deterministic backfills
-- - audit-ready KPI provenance
-- =====================================================================
BEGIN;
CREATE SCHEMA IF NOT EXISTS analytics;
-- Needed for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;
SET search_path TO public,
    analytics;
-- ---------------------------------------------------------------------
-- 1) PIPELINE RUNS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.pipeline_runs (
    run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at TIMESTAMPTZ,
    config_version TEXT NOT NULL,
    git_sha TEXT NOT NULL,
    status TEXT NOT NULL,
    CONSTRAINT pipeline_runs_status_chk CHECK (
        status IN ('running', 'success', 'failed', 'canceled')
    )
);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at ON analytics.pipeline_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON analytics.pipeline_runs(status);
-- ---------------------------------------------------------------------
-- 2) RAW ARTIFACTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.raw_artifacts (
    artifact_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES analytics.pipeline_runs(run_id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    as_of TIMESTAMPTZ,
    sha256 TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_artifacts_run_id ON analytics.raw_artifacts(run_id);
CREATE INDEX IF NOT EXISTS idx_raw_artifacts_as_of ON analytics.raw_artifacts(as_of);
CREATE INDEX IF NOT EXISTS idx_raw_artifacts_sha256 ON analytics.raw_artifacts(sha256);
-- ---------------------------------------------------------------------
-- 3) KPI VALUES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.kpi_values (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES analytics.pipeline_runs(run_id) ON DELETE CASCADE,
    as_of TIMESTAMPTZ NOT NULL,
    kpi_name TEXT NOT NULL,
    value_numeric NUMERIC,
    precision INT NOT NULL,
    raw_sha256 TEXT,
    raw_artifact_id UUID REFERENCES analytics.raw_artifacts(artifact_id),
    kpi_def_version TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_kpi_values_run_id ON analytics.kpi_values(run_id);
CREATE INDEX IF NOT EXISTS idx_kpi_values_as_of ON analytics.kpi_values(as_of);
CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_name ON analytics.kpi_values(kpi_name);
CREATE UNIQUE INDEX IF NOT EXISTS uq_kpi_values_run_asof_name_def ON analytics.kpi_values(run_id, as_of, kpi_name, kpi_def_version);
-- ---------------------------------------------------------------------
-- 4) DATA QUALITY RESULTS
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analytics.data_quality_results (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES analytics.pipeline_runs(run_id) ON DELETE CASCADE,
    completeness NUMERIC,
    freshness_hours NUMERIC,
    referential_integrity_pass BOOLEAN,
    notes_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_data_quality_results_run_id ON analytics.data_quality_results(run_id);
COMMIT;
