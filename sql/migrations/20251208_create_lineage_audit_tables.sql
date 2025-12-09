-- Migration: Create ingest_runs, data_quality_issues, agent_runs tables for data lineage and audit logging

CREATE TABLE IF NOT EXISTS ingest_runs (
  id UUID PRIMARY KEY,
  source_name VARCHAR(255),
  source_path VARCHAR(1000),
  run_timestamp TIMESTAMPTZ,
  row_count_input INT,
  row_count_output INT,
  data_hash VARCHAR(64),
  schema_version VARCHAR(10),
  status VARCHAR(20),
  error_message TEXT
);

CREATE TABLE IF NOT EXISTS data_quality_issues (
  id UUID PRIMARY KEY,
  ingest_run_id UUID REFERENCES ingest_runs(id),
  table_name VARCHAR(255),
  issue_type VARCHAR(50),
  row_count INT,
  description TEXT,
  severity VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS agent_runs (
  id UUID PRIMARY KEY,
  agent_name VARCHAR(255),
  run_timestamp TIMESTAMPTZ,
  kpi_snapshot_id UUID,
  prompt_version VARCHAR(10),
  model_used VARCHAR(100),
  input_data_hash VARCHAR(64),
  output_markdown TEXT,
  citations JSONB
);
