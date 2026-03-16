-- =============================================================================
-- Star Schema — DuckDB variant (local / zero-cost analytics)
-- Target: DuckDB ≥ 0.10
-- Version: 1.0  |  2026-03-16
--
-- Differences vs. PostgreSQL version
--   - SERIAL → SEQUENCE / integer primary key with nextval()
--   - GENERATED ALWAYS AS … STORED → regular columns populated at insert time
--   - No FK enforcement (DuckDB skips FK checks for performance)
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. DIMENSION: dim_time
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_time START 1;

CREATE TABLE IF NOT EXISTS dim_time (
    time_id          INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_time'),
    snapshot_month   DATE         NOT NULL UNIQUE,
    year             SMALLINT     NOT NULL,
    month            SMALLINT     NOT NULL,
    quarter          SMALLINT     NOT NULL,
    year_month       VARCHAR(7)   NOT NULL   -- 'YYYY-MM'
);

-- ---------------------------------------------------------------------------
-- 2. DIMENSION: dim_client
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_client START 1;

CREATE TABLE IF NOT EXISTS dim_client (
    client_sk        INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_client'),
    client_id        VARCHAR        NOT NULL UNIQUE,
    client_name      VARCHAR,
    identity_number  VARCHAR,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 3. DIMENSION: dim_loan
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_dim_loan START 1;

CREATE TABLE IF NOT EXISTS dim_loan (
    loan_sk              INTEGER PRIMARY KEY DEFAULT nextval('seq_dim_loan'),
    lend_id              VARCHAR        NOT NULL UNIQUE,
    numero_desembolso    VARCHAR,
    client_sk            INTEGER,
    product_type         VARCHAR,
    branch_code          VARCHAR,
    currency             VARCHAR(3)     NOT NULL DEFAULT 'USD',
    disbursement_date    DATE,
    maturity_date        DATE,
    original_principal   DECIMAL(18,4),
    interest_rate        DECIMAL(8,6),
    term_months          SMALLINT,
    created_at           TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dim_loan_numero ON dim_loan (numero_desembolso);
CREATE INDEX IF NOT EXISTS idx_dim_loan_client ON dim_loan (client_sk);

-- ---------------------------------------------------------------------------
-- 4. FACT: fact_disbursement
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fact_disb START 1;

CREATE TABLE IF NOT EXISTS fact_disbursement (
    disbursement_sk      INTEGER PRIMARY KEY DEFAULT nextval('seq_fact_disb'),
    loan_sk              INTEGER        NOT NULL,
    client_sk            INTEGER        NOT NULL,
    time_id              INTEGER        NOT NULL,
    disbursement_date    DATE           NOT NULL,
    principal_amount     DECIMAL(18,4)  NOT NULL,
    currency             VARCHAR(3)     NOT NULL DEFAULT 'USD',
    channel              VARCHAR,
    product_type         VARCHAR,
    branch_code          VARCHAR,
    loaded_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fct_disb_loan ON fact_disbursement (loan_sk);
CREATE INDEX IF NOT EXISTS idx_fct_disb_time ON fact_disbursement (time_id);
CREATE INDEX IF NOT EXISTS idx_fct_disb_date ON fact_disbursement (disbursement_date);

-- ---------------------------------------------------------------------------
-- 5. FACT: fact_payment
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fact_pay START 1;

CREATE TABLE IF NOT EXISTS fact_payment (
    payment_sk           INTEGER PRIMARY KEY DEFAULT nextval('seq_fact_pay'),
    loan_sk              INTEGER        NOT NULL,
    client_sk            INTEGER        NOT NULL,
    time_id              INTEGER        NOT NULL,
    payment_date         DATE           NOT NULL,
    principal_paid       DECIMAL(18,4)  NOT NULL DEFAULT 0,
    interest_paid        DECIMAL(18,4)  NOT NULL DEFAULT 0,
    fees_paid            DECIMAL(18,4)  NOT NULL DEFAULT 0,
    total_paid           DECIMAL(18,4),  -- populated at insert
    currency             VARCHAR(3)     NOT NULL DEFAULT 'USD',
    payment_method       VARCHAR,
    loaded_at            TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fct_pay_loan ON fact_payment (loan_sk);
CREATE INDEX IF NOT EXISTS idx_fct_pay_time ON fact_payment (time_id);
CREATE INDEX IF NOT EXISTS idx_fct_pay_date ON fact_payment (payment_date);

-- ---------------------------------------------------------------------------
-- 6. FACT: fact_monthly_snapshot
-- ---------------------------------------------------------------------------
CREATE SEQUENCE IF NOT EXISTS seq_fact_snap START 1;

CREATE TABLE IF NOT EXISTS fact_monthly_snapshot (
    snapshot_sk            INTEGER PRIMARY KEY DEFAULT nextval('seq_fact_snap'),
    loan_sk                INTEGER        NOT NULL,
    client_sk              INTEGER        NOT NULL,
    time_id                INTEGER        NOT NULL,
    snapshot_month         DATE           NOT NULL,

    -- Balance sheet
    principal_outstanding  DECIMAL(18,4),
    total_overdue_amount   DECIMAL(18,4),
    interest_outstanding   DECIMAL(18,4),
    fees_outstanding       DECIMAL(18,4),

    -- Mora / credit quality
    dpd                    SMALLINT,
    mora_bucket            VARCHAR(16),
    is_overdue             BOOLEAN,       -- dpd > 0

    -- PAR flags
    par_1                  BOOLEAN,
    par_30                 BOOLEAN,
    par_60                 BOOLEAN,
    par_90                 BOOLEAN,

    -- Vintage
    months_on_book         SMALLINT,
    monthly_income         DECIMAL(18,4),

    -- Metadata
    source                 VARCHAR,
    loaded_at              TIMESTAMPTZ    NOT NULL DEFAULT NOW(),

    UNIQUE (loan_sk, time_id)
);

CREATE INDEX IF NOT EXISTS idx_snap_loan ON fact_monthly_snapshot (loan_sk);
CREATE INDEX IF NOT EXISTS idx_snap_time ON fact_monthly_snapshot (time_id);
CREATE INDEX IF NOT EXISTS idx_snap_month ON fact_monthly_snapshot (snapshot_month);
CREATE INDEX IF NOT EXISTS idx_snap_bucket ON fact_monthly_snapshot (mora_bucket);
