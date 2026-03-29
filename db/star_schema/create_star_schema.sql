-- =============================================================================
-- Pure Star Schema — Loans Analytics (PostgreSQL/Supabase)
-- Enforces:
--   * Fact_Desembolsos
--   * Fact_Transacciones_Pago
--   * Bridge_Prestatario_Prestamo
--   * Dim_Calendario as central role-playing time dimension
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS star;

-- ---------------------------------------------------------------------------
-- 1) Central calendar dimension (Dim_Calendario)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS star.dim_calendario (
    date_key               INTEGER PRIMARY KEY, -- YYYYMMDD
    calendar_date          DATE NOT NULL UNIQUE,
    year_number            SMALLINT NOT NULL,
    quarter_number         SMALLINT NOT NULL,
    month_number           SMALLINT NOT NULL,
    month_name             VARCHAR(12) NOT NULL,
    week_of_year           SMALLINT NOT NULL,
    day_of_month           SMALLINT NOT NULL,
    day_of_week_iso        SMALLINT NOT NULL,
    is_month_end           BOOLEAN NOT NULL DEFAULT FALSE
);

-- ---------------------------------------------------------------------------
-- 2) Dimensions
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS star.dim_prestatario (
    prestatario_sk         BIGSERIAL PRIMARY KEY,
    prestatario_id         VARCHAR(64) NOT NULL UNIQUE,
    tipo_documento         VARCHAR(16),
    numero_documento       VARCHAR(64),
    nombre_completo        VARCHAR(255),
    segmento               VARCHAR(64),
    ciudad                 VARCHAR(128),
    pais                   VARCHAR(64),
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS star.dim_prestamo (
    prestamo_sk            BIGSERIAL PRIMARY KEY,
    prestamo_id            VARCHAR(64) NOT NULL UNIQUE,
    producto               VARCHAR(64),
    moneda                 CHAR(3) NOT NULL DEFAULT 'USD',
    sucursal               VARCHAR(64),
    tasa_nominal_anual     NUMERIC(12,8),
    plazo_meses            SMALLINT,

    -- Role-playing dimension keys to Dim_Calendario
    fecha_solicitud_key    INTEGER REFERENCES star.dim_calendario(date_key),
    fecha_aprobacion_key   INTEGER REFERENCES star.dim_calendario(date_key),
    fecha_desembolso_key   INTEGER REFERENCES star.dim_calendario(date_key),
    fecha_vencimiento_key  INTEGER REFERENCES star.dim_calendario(date_key),
    fecha_castigo_key      INTEGER REFERENCES star.dim_calendario(date_key),

    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 3) Bridge (Bridge_Prestatario_Prestamo)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS star.bridge_prestatario_prestamo (
    bridge_sk              BIGSERIAL PRIMARY KEY,
    prestatario_sk         BIGINT NOT NULL REFERENCES star.dim_prestatario(prestatario_sk),
    prestamo_sk            BIGINT NOT NULL REFERENCES star.dim_prestamo(prestamo_sk),
    relacion_tipo          VARCHAR(32) NOT NULL DEFAULT 'TITULAR', -- TITULAR, CODEUDOR, GARANTE
    relacion_inicio_key    INTEGER REFERENCES star.dim_calendario(date_key),
    relacion_fin_key       INTEGER REFERENCES star.dim_calendario(date_key),
    is_primary             BOOLEAN NOT NULL DEFAULT TRUE,
    participation_pct      NUMERIC(9,6) NOT NULL DEFAULT 1.0,
    UNIQUE (prestatario_sk, prestamo_sk, relacion_tipo)
);

-- ---------------------------------------------------------------------------
-- 4) Facts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS star.fact_desembolsos (
    desembolso_sk          BIGSERIAL PRIMARY KEY,
    prestamo_sk            BIGINT NOT NULL REFERENCES star.dim_prestamo(prestamo_sk),
    prestatario_sk         BIGINT NOT NULL REFERENCES star.dim_prestatario(prestatario_sk),
    fecha_desembolso_key   INTEGER NOT NULL REFERENCES star.dim_calendario(date_key),
    monto_desembolsado     NUMERIC(18,4) NOT NULL CHECK (monto_desembolsado >= 0),
    cargo_originacion      NUMERIC(18,4) NOT NULL DEFAULT 0,
    canal                  VARCHAR(64),
    loaded_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS star.fact_transacciones_pago (
    pago_sk                BIGSERIAL PRIMARY KEY,
    prestamo_sk            BIGINT NOT NULL REFERENCES star.dim_prestamo(prestamo_sk),
    prestatario_sk         BIGINT NOT NULL REFERENCES star.dim_prestatario(prestatario_sk),
    fecha_pago_key         INTEGER NOT NULL REFERENCES star.dim_calendario(date_key),
    principal_pagado       NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (principal_pagado >= 0),
    interes_pagado         NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (interes_pagado >= 0),
    mora_pagada            NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (mora_pagada >= 0),
    fee_pagado             NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (fee_pagado >= 0),
    monto_total_pagado     NUMERIC(18,4) GENERATED ALWAYS AS
                           (principal_pagado + interes_pagado + mora_pagada + fee_pagado) STORED,
    metodo_pago            VARCHAR(64),
    loaded_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- 5) Performance indexes (single-direction 1:N joins)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_dim_prestamo_fecha_desembolso_key
    ON star.dim_prestamo (fecha_desembolso_key);
CREATE INDEX IF NOT EXISTS idx_bridge_prestamo
    ON star.bridge_prestatario_prestamo (prestamo_sk);
CREATE INDEX IF NOT EXISTS idx_bridge_prestatario
    ON star.bridge_prestatario_prestamo (prestatario_sk);
CREATE INDEX IF NOT EXISTS idx_fact_desembolsos_prestamo
    ON star.fact_desembolsos (prestamo_sk, fecha_desembolso_key);
CREATE INDEX IF NOT EXISTS idx_fact_pagos_prestamo
    ON star.fact_transacciones_pago (prestamo_sk, fecha_pago_key);

-- ---------------------------------------------------------------------------
-- 6) Compatibility views for existing downstream SQL
-- ---------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS compat;

CREATE OR REPLACE VIEW compat.fact_disbursement AS
SELECT
    desembolso_sk AS disbursement_sk,
    prestamo_sk AS loan_sk,
    prestatario_sk AS client_sk,
    fecha_desembolso_key AS time_id,
    dc.calendar_date AS disbursement_date,
    monto_desembolsado AS principal_amount,
    canal AS channel,
    loaded_at
FROM star.fact_desembolsos fd
JOIN star.dim_calendario dc ON dc.date_key = fd.fecha_desembolso_key;

CREATE OR REPLACE VIEW compat.fact_payment AS
SELECT
    pago_sk AS payment_sk,
    prestamo_sk AS loan_sk,
    prestatario_sk AS client_sk,
    fecha_pago_key AS time_id,
    dc.calendar_date AS payment_date,
    principal_pagado AS principal_paid,
    interes_pagado AS interest_paid,
    fee_pagado AS fees_paid,
    monto_total_pagado AS total_paid,
    metodo_pago AS payment_method,
    loaded_at
FROM star.fact_transacciones_pago fp
JOIN star.dim_calendario dc ON dc.date_key = fp.fecha_pago_key;
