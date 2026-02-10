-- Create fact_loans table for denormalized loan-level analytics
-- Migration: 20260208_create_fact_loans.sql
-- This is the core fact table referenced by views, KPI queries, and monitoring

CREATE TABLE IF NOT EXISTS public.fact_loans (
    id              BIGSERIAL PRIMARY KEY,
    loan_id         TEXT NOT NULL,
    borrower_id     TEXT,
    customer_id     TEXT,
    company         TEXT,
    product_type    TEXT DEFAULT 'factoring',
    
    -- Dates
    origination_date    DATE,
    maturity_date       DATE,
    disbursement_date   DATE,
    
    -- Financials (always NUMERIC, never float)
    principal_amount        NUMERIC(18,2),
    outstanding_balance     NUMERIC(18,2),
    interest_rate           NUMERIC(8,6),      -- annualized decimal (e.g. 0.0775)
    origination_fee         NUMERIC(18,2),
    origination_fee_taxes   NUMERIC(18,2),
    tpv                     NUMERIC(18,2),     -- total processed volume
    currency                TEXT DEFAULT 'USD',
    
    -- Term
    term_months     INTEGER,
    term_unit       TEXT DEFAULT 'days',
    payment_frequency TEXT,
    
    -- Risk
    days_past_due   INTEGER DEFAULT 0,
    credit_score    INTEGER,
    status          TEXT,                       -- normalized: active, paid_off, defaulted, etc.
    current_status  TEXT,                       -- raw status from source
    
    -- Classification
    client_type     TEXT,
    industry        TEXT,
    sales_channel   TEXT,
    collateral_type TEXT,
    collateral_value NUMERIC(18,2),
    
    -- Geography
    city            TEXT,
    state           TEXT,
    country         TEXT,
    
    -- Payments
    last_payment_date   DATE,
    last_payment_amount NUMERIC(18,2),
    current_balance     NUMERIC(18,2),
    
    -- Metadata
    data_ingest_ts  TIMESTAMPTZ DEFAULT NOW(),
    run_id          TEXT,
    tenant_id       TEXT,
    
    -- Constraints
    CONSTRAINT uq_fact_loans_loan_id UNIQUE (loan_id)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_fact_loans_status ON public.fact_loans(status);
CREATE INDEX IF NOT EXISTS idx_fact_loans_origination_date ON public.fact_loans(origination_date);
CREATE INDEX IF NOT EXISTS idx_fact_loans_disbursement_date ON public.fact_loans(disbursement_date);
CREATE INDEX IF NOT EXISTS idx_fact_loans_dpd ON public.fact_loans(days_past_due);
CREATE INDEX IF NOT EXISTS idx_fact_loans_customer ON public.fact_loans(customer_id);
CREATE INDEX IF NOT EXISTS idx_fact_loans_borrower ON public.fact_loans(borrower_id);
CREATE INDEX IF NOT EXISTS idx_fact_loans_tenant ON public.fact_loans(tenant_id);

-- Enable RLS
ALTER TABLE public.fact_loans ENABLE ROW LEVEL SECURITY;

-- RLS policies
CREATE POLICY anon_readonly ON public.fact_loans
    FOR SELECT TO anon
    USING (tenant_id = current_setting('app.tenant_id', true));

CREATE POLICY service_all ON public.fact_loans
    FOR ALL TO service_role
    USING (true)
    WITH CHECK (true);

-- Comments
COMMENT ON TABLE public.fact_loans IS 'Denormalized loan-level fact table for analytics. Source: ETL pipeline Phase 2 output.';
COMMENT ON COLUMN public.fact_loans.interest_rate IS 'Annualized decimal rate (e.g. 0.0775 = 7.75%). Normalized from monthly % in transformation phase.';
COMMENT ON COLUMN public.fact_loans.tpv IS 'Total Processed Volume - key metric for factoring operations.';
