-- Migration: Create historical_kpis table for G4.2
-- Purpose: Store historical KPI values for multi-agent system trend analysis
-- Author: G4.2 Deployment
-- Date: 2026-01-28

-- ============================================================================
-- Table: historical_kpis
-- ============================================================================
-- Stores historical KPI observations with portfolio context and calculation metadata
-- Supports daily/weekly/monthly grain for flexible time-series analysis

CREATE TABLE IF NOT EXISTS historical_kpis (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- KPI identification (matches SupabaseHistoricalBackend expectation: kpi_id)
    kpi_id VARCHAR(255) NOT NULL,

    -- KPI value (DECIMAL for precision; matches expected column name: value)
    value DECIMAL(18,6) NOT NULL,

    -- Temporal dimensions (matches expected column name: date)
    date DATE NOT NULL,

    -- Timestamp for the observation (matches expected column name: timestamp)
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional metadata (versioning, lineage, etc.)
    metadata JSONB
);

-- ============================================================================
-- Indices for Performance Optimization
-- ============================================================================

-- Primary lookup index: query by KPI and date range
CREATE INDEX IF NOT EXISTS idx_historical_kpis_kpi_date 
    ON historical_kpis(kpi_id, date DESC);

-- Composite index for common query pattern: KPI + date + timestamp
CREATE INDEX IF NOT EXISTS idx_historical_kpis_lookup 
    ON historical_kpis(kpi_id, date DESC, "timestamp" DESC);

-- Additional indexes can be added here if query patterns evolve
-- (e.g., indexes on date alone or timestamp alone for time-based scans).

-- Grain-specific queries (e.g., monthly aggregations)
[...]
CREATE INDEX IF NOT EXISTS idx_historical_kpis_grain 
    ON historical_kpis(grain, calculation_date DESC);

-- ============================================================================
-- Row-Level Security (RLS)
-- ============================================================================
-- Enable RLS for multi-tenant security
-- Uncomment and customize based on your authentication setup

-- ALTER TABLE historical_kpis ENABLE ROW LEVEL SECURITY;

-- Example policy: Users can only see their own portfolio KPIs
-- CREATE POLICY "Users can view their portfolio KPIs"
--     ON historical_kpis FOR SELECT
--     USING (auth.uid() IN (
--         SELECT user_id FROM portfolios WHERE id = historical_kpis.portfolio_id
--     ));

-- Example policy: Service role can insert/update KPIs
-- CREATE POLICY "Service role can manage KPIs"
--     ON historical_kpis FOR ALL
--     USING (auth.role() = 'service_role');

-- ============================================================================
-- Partitioning Strategy (Future Enhancement)
-- ============================================================================
-- For large-scale deployments with multi-year history, consider partitioning
-- by calculation_date (year-based) for improved query performance and 
-- easier data retention/archival management.
--
-- Example (requires PostgreSQL 10+):
-- 
-- ALTER TABLE historical_kpis 
--     PARTITION BY RANGE (EXTRACT(YEAR FROM calculation_date));
-- 
-- CREATE TABLE historical_kpis_2024 
--     PARTITION OF historical_kpis 
--     FOR VALUES FROM (2024) TO (2025);
-- 
-- CREATE TABLE historical_kpis_2025 
--     PARTITION OF historical_kpis 
--     FOR VALUES FROM (2025) TO (2026);
-- 
-- CREATE TABLE historical_kpis_2026 
--     PARTITION OF historical_kpis 
--     FOR VALUES FROM (2026) TO (2027);

-- ============================================================================
-- Updated_at Trigger
-- ============================================================================
-- Automatically update updated_at timestamp on row modifications

CREATE OR REPLACE FUNCTION update_historical_kpis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_historical_kpis_updated_at
    BEFORE UPDATE ON historical_kpis
    FOR EACH ROW
    EXECUTE FUNCTION update_historical_kpis_updated_at();

-- ============================================================================
-- Sample Data (Optional - for testing/development)
-- ============================================================================
-- Uncomment to insert sample historical KPIs for testing

-- INSERT INTO historical_kpis (portfolio_id, kpi_name, kpi_value, calculation_date, grain)
-- VALUES 
--     (gen_random_uuid(), 'default_rate', 0.0245, '2026-01-01', 'monthly'),
--     (gen_random_uuid(), 'disbursements', 1500000.50, '2026-01-15', 'daily'),
--     (gen_random_uuid(), 'portfolio_balance', 125000000.00, '2026-01-01', 'monthly');

-- ============================================================================
-- Verification Queries
-- ============================================================================
-- Verify table creation and indices

-- SELECT 
--     tablename, 
--     indexname, 
--     indexdef 
-- FROM pg_indexes 
-- WHERE tablename = 'historical_kpis';

-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable 
-- FROM information_schema.columns 
-- WHERE table_name = 'historical_kpis'
-- ORDER BY ordinal_position;
