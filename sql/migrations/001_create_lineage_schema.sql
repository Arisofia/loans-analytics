-- Data lineage and audit schema
CREATE TABLE IF NOT EXISTS ingest_runs (
    id BIGSERIAL PRIMARY KEY,
    source_system TEXT NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    status TEXT NOT NULL,
    records_loaded BIGINT DEFAULT 0,
    input_hash TEXT,
    details JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS data_quality_issues (
    id BIGSERIAL PRIMARY KEY,
    ingest_run_id BIGINT REFERENCES ingest_runs(id) ON DELETE CASCADE,
    detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity TEXT NOT NULL,
    kpi_id TEXT,
    issue_type TEXT NOT NULL,
    issue_payload JSONB DEFAULT '{}'::jsonb,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id BIGSERIAL PRIMARY KEY,
    kpi_id TEXT NOT NULL,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    value NUMERIC NOT NULL,
    calculation_version TEXT NOT NULL,
    source_table TEXT,
    lineage JSONB DEFAULT '{}'::jsonb,
    ingest_run_id BIGINT REFERENCES ingest_runs(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS kpi_calculation_lineage (
    id BIGSERIAL PRIMARY KEY,
    kpi_snapshot_id BIGINT REFERENCES kpi_snapshots(id) ON DELETE CASCADE,
    step_order INT NOT NULL,
    step_name TEXT NOT NULL,
    input_table TEXT,
    transformation TEXT,
    checksum TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_runs (
    id BIGSERIAL PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    input_data_hash TEXT,
    prompt_version TEXT,
    model_used TEXT,
    output_markdown TEXT,
    citations JSONB DEFAULT '[]'::jsonb,
    accuracy_score NUMERIC,
    requires_human_review BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    kpi_snapshot_id BIGINT REFERENCES kpi_snapshots(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_kpi_snapshots_kpi_id ON kpi_snapshots(kpi_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_kpi_snapshot_id ON agent_runs(kpi_snapshot_id);
CREATE INDEX IF NOT EXISTS idx_dq_issues_ingest_run_id ON data_quality_issues(ingest_run_id);
