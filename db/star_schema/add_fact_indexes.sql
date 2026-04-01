-- Performance indexes for star schema fact table foreign keys
-- Run once after star schema creation to improve analytical query speed.

CREATE INDEX IF NOT EXISTS idx_fact_desembolsos_prestamo
    ON star.fact_desembolsos(prestamo_sk);

CREATE INDEX IF NOT EXISTS idx_fact_desembolsos_prestatario
    ON star.fact_desembolsos(prestatario_sk);

CREATE INDEX IF NOT EXISTS idx_fact_desembolsos_fecha
    ON star.fact_desembolsos(fecha_desembolso_key);

CREATE INDEX IF NOT EXISTS idx_fact_pagos_prestamo
    ON star.fact_transacciones_pago(prestamo_sk);

CREATE INDEX IF NOT EXISTS idx_fact_pagos_fecha
    ON star.fact_transacciones_pago(fecha_pago_key);

CREATE INDEX IF NOT EXISTS idx_bridge_prestatario
    ON star.bridge_prestatario_prestamo(prestatario_sk);

CREATE INDEX IF NOT EXISTS idx_bridge_prestamo
    ON star.bridge_prestatario_prestamo(prestamo_sk);
