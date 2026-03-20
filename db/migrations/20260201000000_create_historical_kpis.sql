-- Migration: Create historical_kpis table for Phase G4.2 Supabase integration
-- Date: 2026-02-01 (Consolidated from 2026-01-28 and 2026-02-01)
-- Purpose: Define schema for daily KPI time-series data
-- Grain: One row per (kpi_id, portfolio_id, product_code, segment_code, date)

BEGIN;

CREATE TABLE IF NOT EXISTS public.historical_kpis (
    id                BIGSERIAL PRIMARY KEY,

    -- Business identity
    kpi_id            TEXT        NOT NULL,  -- e.g. "npl_ratio", "cost_of_risk"
    portfolio_id      TEXT        NULL,      -- e.g. "retail", "sme", "mortgage"
    product_code      TEXT        NULL,      -- e.g. "PLN", "CC", "MTG"
    segment_code      TEXT        NULL,      -- e.g. "mass", "affluent", "micro"

    -- Time grain
    date              DATE        NOT NULL,  -- daily KPI date
    ts_utc            TIMESTAMPTZ NOT NULL DEFAULT NOW(), -- ingestion timestamp

    -- KPI values
    value_numeric     NUMERIC(18, 6) NULL,   -- main numeric KPI value (legacy alias: value)
    value_int         BIGINT       NULL,      -- optional count
    value_json        JSONB        NULL,      -- optional structured payload

    -- Quality and provenance
    source_system     TEXT         NULL,      -- e.g. "data_warehouse", "simulation"
    run_id            TEXT         NULL,      -- ETL run identifier
    is_final          BOOLEAN      NOT NULL DEFAULT TRUE,

    -- Audit
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Backward compatibility alias (if needed by old code using 'value' instead of 'value_numeric')
-- Note: It's better to update the code, but if needed:
-- ALTER TABLE public.historical_kpis ADD COLUMN IF NOT EXISTS value NUMERIC(18,6) GENERATED ALWAYS AS (value_numeric) STORED;

-- ============================================================================
-- Updated_at Trigger
-- ============================================================================

CREATE OR REPLACE FUNCTION public.update_historical_kpis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_historical_kpis_updated_at ON public.historical_kpis;
CREATE TRIGGER trg_historical_kpis_updated_at
    BEFORE UPDATE ON public.historical_kpis
    FOR EACH ROW
    EXECUTE FUNCTION public.update_historical_kpis_updated_at();

-- ============================================================================
-- Indices for Performance Optimization
-- ============================================================================

-- Core access pattern index: query by kpi + date range
CREATE INDEX IF NOT EXISTS idx_hkpi_kpi_date
    ON public.historical_kpis (kpi_id, date DESC);

-- Composite index for common query pattern: KPI + date + ts_utc
CREATE INDEX IF NOT EXISTS idx_hkpi_lookup 
    ON public.historical_kpis (kpi_id, date DESC, ts_utc DESC);

-- Additional filters
CREATE INDEX IF NOT EXISTS idx_hkpi_portfolio_date
    ON public.historical_kpis (portfolio_id, date);

CREATE INDEX IF NOT EXISTS idx_hkpi_product_date
    ON public.historical_kpis (product_code, date);

-- Enable Row Level Security
ALTER TABLE public.historical_kpis ENABLE ROW LEVEL SECURITY;

-- Default service role policy (restrictive)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'historical_kpis' 
        AND policyname = 'historical_kpis_service_role_access'
    ) THEN
        CREATE POLICY historical_kpis_service_role_access
            ON public.historical_kpis
            FOR ALL
            TO public
            USING (auth.role() = 'service_role')
            WITH CHECK (auth.role() = 'service_role');
    END IF;
END $$;

COMMIT;
