-- Migration: Create historical_kpis table for Phase G4.2 Supabase integration
-- Date: 2026-02-01
-- Purpose: Define schema for daily KPI time-series data
-- Grain: One row per (kpi_id, portfolio_id, product_code, segment_code, date)

create table if not exists public.historical_kpis (
    id                bigserial primary key,

    -- Business identity
    kpi_id            text        not null,  -- e.g. "npl_ratio", "cost_of_risk"
    portfolio_id      text        null,      -- e.g. "retail", "sme", "mortgage"
    product_code      text        null,      -- e.g. "PLN", "CC", "MTG"
    segment_code      text        null,      -- e.g. "mass", "affluent", "micro"

    -- Time grain
    date              date        not null,  -- daily KPI date
    ts_utc            timestamptz not null default now(), -- ingestion timestamp

    -- KPI values
    value_numeric     numeric(18, 6) null,   -- main numeric KPI value
    value_int         bigint       null,      -- optional count
    value_json        jsonb        null,      -- optional structured payload

    -- Quality and provenance
    source_system     text         null,      -- e.g. "data_warehouse", "simulation"
    run_id            text         null,      -- ETL run identifier
    is_final          boolean      not null default true,

    -- Audit
    created_at        timestamptz  not null default now(),
    updated_at        timestamptz  not null default now()
);

-- Core access pattern index: query by kpi + date range
create index if not exists idx_hkpi_kpi_date
    on public.historical_kpis (kpi_id, date);

-- Additional filters (optional but recommended)
create index if not exists idx_hkpi_portfolio_date
    on public.historical_kpis (portfolio_id, date);

create index if not exists idx_hkpi_product_date
    on public.historical_kpis (product_code, date);

-- Uniqueness guard at KPI grain (optional, if you enforce 1 value per day)
-- Uncomment if enforcing uniqueness per day per dimension combination
-- create unique index if not exists ux_hkpi_kpi_portfolio_product_segment_date
--     on public.historical_kpis (kpi_id, portfolio_id, product_code, segment_code, date);

-- Enable Row Level Security (optional, for multi-tenant isolation)
-- alter table public.historical_kpis enable row level security;
