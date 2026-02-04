-- Create monitoring schema explicitly
-- Date: 2026-02-04
-- Purpose: Define monitoring schema and tables for KPI tracking
-- Related: docs/SECURITY_STATUS_REPORT.md

BEGIN;

-- Create monitoring schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS "monitoring"
  AUTHORIZATION postgres;

ALTER SCHEMA "monitoring" OWNER TO "postgres";

-- Create kpi_definitions table
CREATE TABLE IF NOT EXISTS "monitoring"."kpi_definitions" (
  kpi_key text PRIMARY KEY,
  display_name text NOT NULL,
  description text,
  formula text,
  category text,
  unit text,
  threshold_warning numeric,
  threshold_critical numeric,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);

ALTER TABLE "monitoring"."kpi_definitions" OWNER TO "postgres";
ALTER TABLE "monitoring"."kpi_definitions" ENABLE ROW LEVEL SECURITY;

-- Create kpi_values table
CREATE TABLE IF NOT EXISTS "monitoring"."kpi_values" (
  id bigserial PRIMARY KEY,
  kpi_key text NOT NULL REFERENCES "monitoring"."kpi_definitions"(kpi_key) ON DELETE RESTRICT,
  as_of_date date NOT NULL,
  value numeric NOT NULL,
  snapshot_id uuid,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  UNIQUE(as_of_date, kpi_key, snapshot_id)
);

ALTER TABLE "monitoring"."kpi_values" OWNER TO "postgres";
ALTER TABLE "monitoring"."kpi_values" ENABLE ROW LEVEL SECURITY;

-- Create indexes for performance
CREATE UNIQUE INDEX IF NOT EXISTS kpi_definitions_pkey ON "monitoring"."kpi_definitions" USING btree (kpi_key);
CREATE UNIQUE INDEX IF NOT EXISTS kpi_values_as_of_date_kpi_key_snapshot_id_key 
  ON "monitoring"."kpi_values" USING btree (as_of_date, kpi_key, snapshot_id);
CREATE UNIQUE INDEX IF NOT EXISTS kpi_values_pkey ON "monitoring"."kpi_values" USING btree (id);

-- Create indexes for queries
CREATE INDEX IF NOT EXISTS idx_kpi_values_kpi_key ON "monitoring"."kpi_values" (kpi_key);
CREATE INDEX IF NOT EXISTS idx_kpi_values_as_of_date ON "monitoring"."kpi_values" (as_of_date);

COMMIT;

-- NOTE: RLS policies are applied in separate migration (20260204120500_fix_kpi_values_policy.sql)
-- This ensures schema creation happens before policy creation, maintaining proper migration order.
