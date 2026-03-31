-- =============================================================================
-- Pure Star Schema — DuckDB
-- Mirrors PostgreSQL star schema naming for deterministic local analytics.
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS star;

CREATE TABLE IF NOT EXISTS star.dim_calendario (
    date_key               INTEGER PRIMARY KEY,
    calendar_date          DATE NOT NULL UNIQUE,
    year_number            SMALLINT NOT NULL,
    quarter_number         SMALLINT NOT NULL,
    month_number           SMALLINT NOT NULL,
    month_name             VARCHAR NOT NULL,
    week_of_year           SMALLINT NOT NULL,
    day_of_month           SMALLINT NOT NULL,
    day_of_week_iso        SMALLINT NOT NULL,
    is_month_end           BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS star.dim_prestatario (
    prestatario_sk         BIGINT PRIMARY KEY,
    prestatario_id         VARCHAR NOT NULL UNIQUE,
    tipo_documento         VARCHAR,
    numero_documento       VARCHAR,
    nombre_completo        VARCHAR,
    segmento               VARCHAR,
    ciudad                 VARCHAR,
    pais                   VARCHAR,
    created_at             TIMESTAMP DEFAULT NOW()
);

CREATE SEQUENCE IF NOT EXISTS star.seq_dim_prestatario START 1;
INSERT INTO star.dim_prestatario (prestatario_sk, prestatario_id)
SELECT nextval('star.seq_dim_prestatario'), '__seed__'
WHERE NOT EXISTS (SELECT 1 FROM star.dim_prestatario WHERE prestatario_id='__seed__');
DELETE FROM star.dim_prestatario WHERE prestatario_id='__seed__';

CREATE TABLE IF NOT EXISTS star.dim_prestamo (
    prestamo_sk            BIGINT PRIMARY KEY,
    prestamo_id            VARCHAR NOT NULL UNIQUE,
    producto               VARCHAR,
    moneda                 VARCHAR NOT NULL DEFAULT 'USD',
    sucursal               VARCHAR,
    tasa_nominal_anual     DECIMAL(12,8),
    plazo_meses            SMALLINT,
    fecha_solicitud_key    INTEGER,
    fecha_aprobacion_key   INTEGER,
    fecha_desembolso_key   INTEGER,
    fecha_vencimiento_key  INTEGER,
    fecha_castigo_key      INTEGER,
    created_at             TIMESTAMP DEFAULT NOW(),
    updated_at             TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS star.bridge_prestatario_prestamo (
    bridge_sk              BIGINT PRIMARY KEY,
    prestatario_sk         BIGINT NOT NULL,
    prestamo_sk            BIGINT NOT NULL,
    relacion_tipo          VARCHAR NOT NULL DEFAULT 'TITULAR',
    relacion_inicio_key    INTEGER,
    relacion_fin_key       INTEGER,
    is_primary             BOOLEAN NOT NULL DEFAULT TRUE,
    participation_pct      DECIMAL(9,6) NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS star.fact_desembolsos (
    desembolso_sk          BIGINT PRIMARY KEY,
    prestamo_sk            BIGINT NOT NULL,
    prestatario_sk         BIGINT NOT NULL,
    fecha_desembolso_key   INTEGER NOT NULL,
    monto_desembolsado     DECIMAL(18,4) NOT NULL,
    cargo_originacion      DECIMAL(18,4) NOT NULL DEFAULT 0,
    canal                  VARCHAR,
    loaded_at              TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS star.fact_transacciones_pago (
    pago_sk                BIGINT PRIMARY KEY,
    prestamo_sk            BIGINT NOT NULL,
    prestatario_sk         BIGINT NOT NULL,
    fecha_pago_key         INTEGER NOT NULL,
    principal_pagado       DECIMAL(18,4) NOT NULL DEFAULT 0,
    interes_pagado         DECIMAL(18,4) NOT NULL DEFAULT 0,
    mora_pagada            DECIMAL(18,4) NOT NULL DEFAULT 0,
    fee_pagado             DECIMAL(18,4) NOT NULL DEFAULT 0,
    monto_total_pagado     DECIMAL(18,4),
    metodo_pago            VARCHAR,
    loaded_at              TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bridge_prestamo ON star.bridge_prestatario_prestamo (prestamo_sk);
CREATE INDEX IF NOT EXISTS idx_bridge_prestatario ON star.bridge_prestatario_prestamo (prestatario_sk);
CREATE INDEX IF NOT EXISTS idx_fact_desembolsos_prestamo ON star.fact_desembolsos (prestamo_sk, fecha_desembolso_key);
CREATE INDEX IF NOT EXISTS idx_fact_pagos_prestamo ON star.fact_transacciones_pago (prestamo_sk, fecha_pago_key);
