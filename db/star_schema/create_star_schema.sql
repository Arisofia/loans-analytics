-- =============================================================================
-- Star Schema — Abaco Loans Analytics
-- Target: Supabase / PostgreSQL (free tier)
-- Version: 1.0  |  2026-03-16
--
-- Tables
--   dim_loan             Loan master attributes (SCD Type 1)
--   dim_client           Client/borrower master data
--   dim_time             Calendar dimension
--   fact_disbursement    One row per disbursement event
--   fact_payment         One row per payment received
--   fact_monthly_snapshot  One row per (loan, month) for portfolio reporting
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. DIMENSION: dim_time
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_time (
    time_id          SERIAL PRIMARY KEY,
    snapshot_month   DATE         NOT NULL UNIQUE,
    year             SMALLINT     NOT NULL,
    month            SMALLINT     NOT NULL,
    quarter          SMALLINT     NOT NULL,
    year_month       CHAR(7)      NOT NULL,  -- 'YYYY-MM'
    is_month_end     BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------------
-- 2. DIMENSION: dim_client
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_client (
    client_sk        SERIAL PRIMARY KEY,
    client_id        VARCHAR(64)  NOT NULL,
    client_name      VARCHAR(255),
    identity_number  VARCHAR(64),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (client_id)
);

-- ---------------------------------------------------------------------------
-- 3. DIMENSION: dim_loan
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_loan (
    loan_sk              SERIAL PRIMARY KEY,
    lend_id              VARCHAR(64)  NOT NULL,
    numero_desembolso    VARCHAR(64),
    client_sk            INT          REFERENCES dim_client(client_sk),
    product_type         VARCHAR(64),
    branch_code          VARCHAR(32),
    currency             CHAR(3)      NOT NULL DEFAULT 'USD',
    disbursement_date    DATE,
    maturity_date        DATE,
    original_principal   NUMERIC(18,4),
    interest_rate        NUMERIC(8,6),
    term_months          SMALLINT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (lend_id)
);

CREATE INDEX IF NOT EXISTS idx_dim_loan_numero_desembolso
    ON dim_loan (numero_desembolso);
CREATE INDEX IF NOT EXISTS idx_dim_loan_client_sk
    ON dim_loan (client_sk);

-- ---------------------------------------------------------------------------
-- 4. FACT: fact_disbursement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_disbursement (
    disbursement_sk      SERIAL PRIMARY KEY,
    loan_sk              INT          NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INT          NOT NULL REFERENCES dim_client(client_sk),
    time_id              INT          NOT NULL REFERENCES dim_time(time_id),
    disbursement_date    DATE         NOT NULL,
    principal_amount     NUMERIC(18,4) NOT NULL,
    currency             CHAR(3)       NOT NULL DEFAULT 'USD',
    channel              VARCHAR(64),
    product_type         VARCHAR(64),
    branch_code          VARCHAR(32),
    loaded_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_disb_loan_sk  ON fact_disbursement (loan_sk);
CREATE INDEX IF NOT EXISTS idx_fact_disb_time_id  ON fact_disbursement (time_id);
CREATE INDEX IF NOT EXISTS idx_fact_disb_date     ON fact_disbursement (disbursement_date);

-- ---------------------------------------------------------------------------
-- 5. FACT: fact_payment
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_payment (
    payment_sk           SERIAL PRIMARY KEY,
    loan_sk              INT          NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INT          NOT NULL REFERENCES dim_client(client_sk),
    time_id              INT          NOT NULL REFERENCES dim_time(time_id),
    payment_date         DATE         NOT NULL,
    principal_paid       NUMERIC(18,4) NOT NULL DEFAULT 0,
    interest_paid        NUMERIC(18,4) NOT NULL DEFAULT 0,
    fees_paid            NUMERIC(18,4) NOT NULL DEFAULT 0,
    total_paid           NUMERIC(18,4) GENERATED ALWAYS AS
                             (principal_paid + interest_paid + fees_paid) STORED,
    currency             CHAR(3)       NOT NULL DEFAULT 'USD',
    payment_method       VARCHAR(64),
    loaded_at            TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_pay_loan_sk  ON fact_payment (loan_sk);
CREATE INDEX IF NOT EXISTS idx_fact_pay_time_id  ON fact_payment (time_id);
CREATE INDEX IF NOT EXISTS idx_fact_pay_date     ON fact_payment (payment_date);

-- ---------------------------------------------------------------------------
-- 6. FACT: fact_monthly_snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_monthly_snapshot (
    snapshot_sk          SERIAL PRIMARY KEY,
    loan_sk              INT          NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INT          NOT NULL REFERENCES dim_client(client_sk),
    time_id              INT          NOT NULL REFERENCES dim_time(time_id),
    snapshot_month       DATE         NOT NULL,

    -- Balance sheet
    principal_outstanding  NUMERIC(18,4),
    total_overdue_amount   NUMERIC(18,4),
    interest_outstanding   NUMERIC(18,4),
    fees_outstanding       NUMERIC(18,4),

    -- Mora / credit quality
    dpd                  SMALLINT,
    mora_bucket          VARCHAR(16),   -- 'current','1-30','31-60','61-90','91-180','181-360','360+'
    is_overdue           BOOLEAN        GENERATED ALWAYS AS (dpd > 0) STORED,

    -- PAR flags (true if loan DPD >= threshold)
    par_1                BOOLEAN,
    par_30               BOOLEAN,
    par_60               BOOLEAN,
    par_90               BOOLEAN,

    -- Vintage / lifecycle
    months_on_book       SMALLINT,
    monthly_income       NUMERIC(18,4),

    -- Metadata
    source               VARCHAR(64),   -- 'control_mora', 'pipeline', etc.
    loaded_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    UNIQUE (loan_sk, time_id)
);

CREATE INDEX IF NOT EXISTS idx_snap_loan_sk     ON fact_monthly_snapshot (loan_sk);
CREATE INDEX IF NOT EXISTS idx_snap_time_id     ON fact_monthly_snapshot (time_id);
CREATE INDEX IF NOT EXISTS idx_snap_month       ON fact_monthly_snapshot (snapshot_month);
CREATE INDEX IF NOT EXISTS idx_snap_mora_bucket ON fact_monthly_snapshot (mora_bucket);
CREATE INDEX IF NOT EXISTS idx_snap_dpd         ON fact_monthly_snapshot (dpd);
