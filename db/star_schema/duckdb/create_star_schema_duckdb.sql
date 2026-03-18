-- =============================================================================
-- Star Schema — Abaco Loans Analytics (DuckDB Version)
-- Target: DuckDB / Local Parquet
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. DIMENSION: dim_time
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_time (
    time_id          INTEGER PRIMARY KEY,
    snapshot_month   DATE         NOT NULL UNIQUE,
    year             SMALLINT     NOT NULL,
    month            SMALLINT     NOT NULL,
    quarter          SMALLINT     NOT NULL,
    year_month       VARCHAR      NOT NULL,  -- 'YYYY-MM'
    is_month_end     BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------------
-- 2. DIMENSION: dim_client
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_client (
    client_sk        INTEGER PRIMARY KEY,
    client_id        VARCHAR      NOT NULL,
    client_name      VARCHAR,
    identity_number  VARCHAR,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (client_id)
);

-- ---------------------------------------------------------------------------
-- 3. DIMENSION: dim_loan
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_loan (
    loan_sk              INTEGER PRIMARY KEY,
    lend_id              VARCHAR      NOT NULL,
    numero_desembolso    VARCHAR,
    client_sk            INTEGER      REFERENCES dim_client(client_sk),
    product_type         VARCHAR,
    branch_code          VARCHAR,
    currency             VARCHAR      NOT NULL DEFAULT 'USD',
    disbursement_date    DATE,
    maturity_date        DATE,
    original_principal   DECIMAL(18,4),
    interest_rate        DECIMAL(8,6),
    term_months          SMALLINT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lend_id)
);

-- ---------------------------------------------------------------------------
-- 4. FACT: fact_disbursement
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_disbursement (
    disbursement_sk      INTEGER PRIMARY KEY,
    loan_sk              INTEGER      NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INTEGER      NOT NULL REFERENCES dim_client(client_sk),
    time_id              INTEGER      NOT NULL REFERENCES dim_time(time_id),
    disbursement_date    DATE         NOT NULL,
    principal_amount     DECIMAL(18,4) NOT NULL,
    currency             VARCHAR       NOT NULL DEFAULT 'USD',
    channel              VARCHAR,
    product_type         VARCHAR,
    branch_code          VARCHAR,
    loaded_at            TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- 5. FACT: fact_payment
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_payment (
    payment_sk           INTEGER PRIMARY KEY,
    loan_sk              INTEGER      NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INTEGER      NOT NULL REFERENCES dim_client(client_sk),
    time_id              INTEGER      NOT NULL REFERENCES dim_time(time_id),
    payment_date         DATE         NOT NULL,
    principal_paid       DECIMAL(18,4) NOT NULL DEFAULT 0,
    interest_paid        DECIMAL(18,4) NOT NULL DEFAULT 0,
    fees_paid            DECIMAL(18,4) NOT NULL DEFAULT 0,
    total_paid           DECIMAL(18,4) GENERATED ALWAYS AS (principal_paid + interest_paid + fees_paid),
    currency             VARCHAR       NOT NULL DEFAULT 'USD',
    payment_method       VARCHAR,
    loaded_at            TIMESTAMPTZ   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------------
-- 6. FACT: fact_monthly_snapshot
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_monthly_snapshot (
    snapshot_sk          INTEGER PRIMARY KEY,
    loan_sk              INTEGER      NOT NULL REFERENCES dim_loan(loan_sk),
    client_sk            INTEGER      NOT NULL REFERENCES dim_client(client_sk),
    time_id              INTEGER      NOT NULL REFERENCES dim_time(time_id),
    snapshot_month       DATE         NOT NULL,

    -- Balance sheet
    principal_outstanding  DECIMAL(18,4),
    total_overdue_amount   DECIMAL(18,4),
    interest_outstanding   DECIMAL(18,4),
    fees_outstanding       DECIMAL(18,4),

    -- Mora / credit quality
    dpd                  SMALLINT,
    mora_bucket          VARCHAR,   -- 'current','1-30','31-60','61-90','91-180','181-360','360+'
    is_overdue           BOOLEAN        GENERATED ALWAYS AS (dpd > 0),

    -- PAR flags (true if loan DPD >= threshold)
    par_1                BOOLEAN,
    par_30               BOOLEAN,
    par_60               BOOLEAN,
    par_90               BOOLEAN,

    -- Vintage / lifecycle
    months_on_book       SMALLINT,
    monthly_income       DECIMAL(18,4),

    -- Metadata
    source               VARCHAR,   -- 'control_mora', 'pipeline', etc.
    loaded_at            TIMESTAMPTZ    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (loan_sk, time_id)
);
