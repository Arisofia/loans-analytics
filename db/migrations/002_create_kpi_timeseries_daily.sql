-- Migration: Create kpi_timeseries_daily table for pipeline KPI tracking
-- Date: 2026-01-31
-- Purpose: Store daily KPI calculations from the data pipeline

-- Create table for KPI time series data
CREATE TABLE IF NOT EXISTS kpi_timeseries_daily (
    id BIGSERIAL PRIMARY KEY,
    kpi_name VARCHAR(255) NOT NULL,
    kpi_value DOUBLE PRECISION,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_date DATE NOT NULL,
    source VARCHAR(100) DEFAULT 'pipeline_v2',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_kpi_timeseries_kpi_name 
    ON kpi_timeseries_daily(kpi_name);

CREATE INDEX IF NOT EXISTS idx_kpi_timeseries_run_date 
    ON kpi_timeseries_daily(run_date DESC);

CREATE INDEX IF NOT EXISTS idx_kpi_timeseries_timestamp 
    ON kpi_timeseries_daily(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_kpi_timeseries_kpi_name_run_date 
    ON kpi_timeseries_daily(kpi_name, run_date DESC);

-- Create composite index for dashboard queries
CREATE INDEX IF NOT EXISTS idx_kpi_timeseries_dashboard 
    ON kpi_timeseries_daily(kpi_name, run_date DESC, timestamp DESC);

-- Add comments for documentation
COMMENT ON TABLE kpi_timeseries_daily IS 'Daily KPI calculations from the data pipeline (v2.0)';
COMMENT ON COLUMN kpi_timeseries_daily.kpi_name IS 'Name of the KPI metric (e.g., par_30, portfolio_rotation)';
COMMENT ON COLUMN kpi_timeseries_daily.kpi_value IS 'Calculated value of the KPI';
COMMENT ON COLUMN kpi_timeseries_daily.timestamp IS 'Exact time when the KPI was calculated';
COMMENT ON COLUMN kpi_timeseries_daily.run_date IS 'Date of the pipeline run (for daily aggregation)';
COMMENT ON COLUMN kpi_timeseries_daily.source IS 'Pipeline version or source system identifier';
COMMENT ON COLUMN kpi_timeseries_daily.metadata IS 'Additional context or debugging information (JSON)';

-- Create trigger for updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_kpi_timeseries_updated_at
    BEFORE UPDATE ON kpi_timeseries_daily
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security (RLS)
ALTER TABLE kpi_timeseries_daily ENABLE ROW LEVEL SECURITY;

-- Policy: Allow all operations for service role
CREATE POLICY "Service role has full access" ON kpi_timeseries_daily
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Authenticated users can read all data
CREATE POLICY "Authenticated users can read KPIs" ON kpi_timeseries_daily
    FOR SELECT
    TO authenticated
    USING (true);

-- Policy: Anon users can read recent data only (last 30 days)
CREATE POLICY "Anon users can read recent KPIs" ON kpi_timeseries_daily
    FOR SELECT
    TO anon
    USING (run_date >= CURRENT_DATE - INTERVAL '30 days');
