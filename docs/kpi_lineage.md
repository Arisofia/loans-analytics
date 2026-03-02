# KPI Lineage From Control de Mora

## Objetivo
Garantizar que los KPIs del pipeline se puedan calcular desde **Control de Mora** aun cuando ya no exista `loan_data` actualizado.

## Lógica de cruce entre fuentes
El merge multiarchivo se ejecuta como:
1. Normalización por archivo (`_prepare_dataframe`).
2. Unión vertical (`concat`) de todas las fuentes.
3. Colapso por `loan_id` con prioridad temporal (`_collapse_to_loan_level`), conservando el valor no nulo más reciente por columna.

Esto permite cruzar `loan_data` y `control de mora` en periodos históricos (hasta inicios de enero) y usar solo Control de Mora para periodos recientes.

## Fórmulas derivadas implementadas (Control de Mora)

### 1) Fecha de vencimiento
- `due_date`:
  - Primero usa `due_date`/`fechapagoprogramado`/`fecha_vencimiento`.
  - Si falta, deriva como:
    - `origination_date + term_days` (donde `term_days` viene de `days_to_pay`, `dias_en_pagar`, `term_max`, etc.).
    - Fallback: `origination_date + term_months`.

### 2) Mora en días / DPD
- `dpd` y `days_past_due`:
  - Si ya vienen informados, se conservan.
  - Si faltan: `max(as_of_date - due_date, 0)`.
  - `as_of_date` se toma de `as_of_date/snapshot_date/measurement_date/fecha_actual`.

### 3) Procede a cobro
- `collections_eligible`:
  - Si viene en fuente (`procede_a_cobrar`), se normaliza a `Y/N`.
  - Si falta: `Y` cuando `dpd > 0` y `exposure > 0` y `status != closed`; de lo contrario `N`.

### 4) Utilización de línea
- `utilization_pct`:
  - Si existe, se normaliza (acepta `%`, `$`, comas).
  - Si falta: `exposure / credit_line * 100`.
  - `exposure` usa `outstanding_balance/current_balance/amount/principal_amount`.

### 5) Gobierno / Público
- `government_sector`:
  - Usa `government_sector`/`goes` si existen.
  - Si falta, infiere `GOES` por:
    - `gov/ministry/ministerio` poblado, o
    - keywords en pagador (`issuer_name`/`emisor`): `MINISTERIO`, `GOBIERNO`, `ALCALDIA`, `PUBLIC`, etc.
  - Caso contrario: `PRIVATE`.

### 6) Historial de pago (fecha y monto)
- `last_payment_date`:
  - Se deriva de `last_payment_date/payment_date/fecha_de_pago/fechacobro`.
- `last_payment_amount`:
  - Fallbacks: `payment_amount`, `_pagado`, `total_payment_received`, `capital_collected`.
- `total_scheduled`:
  - Primero usa campos directos (`total_due`, `monto_programado`).
  - Si falta: aproximación mensual desde `principal_amount` y `term_days`.

### 7) Campos auxiliares para KPI
- `term_months`: derivado y acotado (0 < term <= 240).
- `tpv`: fallback desde `total_payment_received` / `capital_collected`.
- `payment_frequency`: derivado (`bullet`/`installment`) para KPI de automatización.

## KPIs que quedan habilitados con estas derivaciones
Además de los KPIs de riesgo ya activos (`PAR30/60/90`, `NPL`, `default_rate`), se habilitan con datos no nulos:
- `collections_rate`
- `recovery_rate`
- `processing_time_avg`
- `customer_lifetime_value`
- `automation_rate`
- Enriched KPIs (`collections_eligible_rate`, `government_sector_exposure_rate`, `avg_credit_line_utilization`, `capital_collection_rate`, `mdsc_posted_rate`)

## Cartera actual (validación)
Run validado: `20260302_115047_control_formula`
- `as_of_date` máximo: **2026-02-28**
- **Cartera actual (total_outstanding_balance)**: **USD 6,009,689.22**
- Préstamos activos/no cerrados: **5,218**

Definición de cartera usada (igual a KPI):
- `SUM(outstanding_balance WHERE status != 'closed')`
