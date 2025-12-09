-- Drop and create ingest_runs table
IF OBJECT_ID('dbo.ingest_runs', 'U') IS NOT NULL
    DROP TABLE dbo.ingest_runs;
CREATE TABLE dbo.ingest_runs (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    source_name VARCHAR(255),
    source_path VARCHAR(1000),
    run_timestamp DATETIMEOFFSET,
    row_count_input INT,
    row_count_output INT,
    data_hash VARCHAR(64),
    schema_version VARCHAR(10),
    status VARCHAR(20),
    error_message NVARCHAR(MAX)
);

-- Drop and create data_quality_issues table
IF OBJECT_ID('dbo.data_quality_issues', 'U') IS NOT NULL
    DROP TABLE dbo.data_quality_issues;
CREATE TABLE dbo.data_quality_issues (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    ingest_run_id UNIQUEIDENTIFIER FOREIGN KEY REFERENCES dbo.ingest_runs(id),
    table_name VARCHAR(255),
    issue_type VARCHAR(50),
    row_count INT,
    description NVARCHAR(MAX),
    severity VARCHAR(20)
);

-- Drop and create agent_runs table
IF OBJECT_ID('dbo.agent_runs', 'U') IS NOT NULL
    DROP TABLE dbo.agent_runs;
CREATE TABLE dbo.agent_runs (
    id UNIQUEIDENTIFIER PRIMARY KEY,
    agent_name VARCHAR(255),
    run_timestamp DATETIMEOFFSET,
    kpi_snapshot_id UNIQUEIDENTIFIER,
    prompt_version VARCHAR(10),
    model_used VARCHAR(100),
    input_data_hash VARCHAR(64),
    output_markdown NVARCHAR(MAX),
    citations NVARCHAR(MAX)
);
