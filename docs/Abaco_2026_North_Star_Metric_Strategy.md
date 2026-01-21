# 🧭 Abaco 2026 — North Star Metric Strategy (NSM)

## 1. Executive summary

**Goal:**

Align the organization around a single metric that captures value creation and sustainable growth for the B2B factoring business.

**Recommended NSM:**

> **Weekly/Monthly Recurrent TPV from Active Clients**

This measures the total processed volume from clients who repeat, reflecting retention, expansion, and portfolio health. It is actionable every week and directly connected to revenue, risk, and governance.

**How it connects to execution:**

- Anchors the origination → cashflow funnel (pancake/replines) by measuring only clients who repeat and generate collections.
- Uses existing guardrails (rotation ≥4.5×, default/NPL <4%, Top-10 concentration ≤30%, single-obligor ≤4%).
- Feeds weekly/monthly board-pack and operational dashboard monitoring (alerts for concentration, DPD/NPL, TPV drops by bucket or channel).

## 2. Context and strategic theses

1. **Target market:** Formal SMEs using accounts receivable for liquidity; e-invoicing adoption eases origination and monitoring.
2. **Competitive edge:** Debtor-centric risk engine and pricing segmented by CreditLineCategory (A–H).
3. **Strategic shift:** Move from measuring only origination to measuring recurrent platform usage and portfolio quality.
4. **Prior gap:** Tracking focused on invoices originated per month; it missed recurrence, expansion, and real cashflow.

## 3. Value engine and key indicators

| Stage | SME action | Value to Abaco | Related metrics |
| --- | --- | --- | --- |
| Acquisition | Onboarding and first operation | New clients | Monthly new logos by segment (Micro/Small/Medium) |
| Engagement | Recurrent factoring usage | Recurrent TPV | **NSM:** Weekly/Monthly Recurrent TPV |
| Conversion | Invoice financing | Revenue and margin | % invoices financed, weighted APR |
| Retention/Expansion | Credit-line upsell | Higher LTV | TPV per recurrent client, bucket upgrades |
| Portfolio health | Collections and cures | Controlled risk | Default rate, DPD/NPL, debtor concentration |

## 4. Definition and calculation

**Metric:** Recurrent TPV from active clients (weekly/monthly).

- **Active clients:** Clients with ≥1 operation in the measurement window.
- **Recurrent:** Clients with ≥2 consecutive periods with TPV > 0 or those returning after ≥90 days (recovered).
- **Calculation:** Sum of Disbursement Amount of financed invoices from recurrent clients in the window.

**Supporting indicators:**

- Financing rate over submitted invoices
- Repeat rate (clients with operations in ≥2 consecutive periods)
- 12m cash-weighted rotation and replines vs plan
- Debtor and client concentration (single-obligor ≤4%, Top-10 ≤30%)
- Default rate 180+ and DPD>15
- Mix-weighted APR by CreditLineCategory

## 5. Alignment with 2025-2026 OKRs

| Objective | NSM-aligned key results | Owner |
| --- | --- | --- |
| Grow with risk control | AUM $7.4M→$16.3M; rotation ≥4.5×; NPL180+ <4%; real default <4%; Top-10 concentration ≤30% | CEO/CRO/CFO |
| Profitability and liquidity | Weighted APR 34–40%; cost of debt ≤13%; DSCR ≥1.2×; utilization 75–90% | CFO |
| Bucketed go-to-market | ≥1 close/KAM/month in $50–150k; upgrades $10–50k→$50–150k; MQL→SQL ≥35–50%; ≤$10k close rate ≥30% | Head of Sales/Head of Growth |
| Production-grade platform | Decision SLA ≤24h, funding SLA ≤48h in ≥90%; live rotation/replines/DPD/NPL panels; SLO ≥99.5% | CTO |
| Portfolio health & collections | CE 6M ≥96%; replines deviation by bucket ±2 p.p.; losses within band (<4%) | Head of Risk |

## 6. Governance and cadence

- **Monitoring:** Weekly (operational) and monthly (board pack) for the NSM and supporting KPIs.
- **Ownership:** NSM DRI: Head of Growth + CEO; Data maintains dashboards; Risk/Finance validate covenants.
- **Alerts:** Concentration breaches, DPD/NPL spikes, replines deviation, TPV drops by segment or channel.

## 7. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Recurrence drop in smaller buckets (G–H) | Adjust pricing/score, reinforce onboarding and reminders; prioritize prime debtors |
| Concentration in a few debtors | Debtor limits, automated alerts, and origination rebalance |
| Misalignment between origination and cashflow | Replines and cash-weighted rotation as guardrails; compare plan vs actual weekly |
| Data quality on invoices/collateral | DTE integration, automated validations, 100% assignment audit |

## 8. Why not use other metrics as the central NSM

- **Invoices originated per month:** Measures acquisition and gross volume only; misses recurrence, expansion, and real cashflow. Fintechs such as Fundbox, BlueVine, and Kredito24 moved from this to recurrent TPV as they scaled.
- **LTV/CAC:** Critical for unit economics and investor reporting, but slow and aggregated; it does not govern weekly pulse or portfolio quality. SaaS/fintech leaders use it as a complementary metric, not as the NSM.

## 9. NSM benchmarks in the industry

- **Recurrent TPV/GMV:** Stripe, Square, PayPal, Shopify, MercadoPago, Konfio.

## 10. Next steps

1. Publish the recurrent TPV panel with cuts by client (new/recurrent/recovered), bucket, and debtor.
2. Activate alerts for concentration and rotation/replines drops vs plan.
3. Link funnels by channel (Digital ≤$10k, Mixed $10–50k, KAM $50–150k) to the NSM to optimize CAC and churn.
4. Report the NSM and supporting KPIs in the weekly/monthly/QBR cadence.

---

# 🧭 Abaco 2026 — Estrategia de la Métrica Estrella del Norte (NSM)

## 1. Resumen ejecutivo

**Objetivo:**

Alinear a toda la organización en torno a una métrica única que capture la creación de valor y el crecimiento sostenible del negocio de factoring B2B.

**NSM recomendada:**

> **TPV recurrente semanal/mensual de clientes activos**

Esta métrica mide el volumen total procesado por clientes que repiten, reflejando retención, expansión y salud de cartera. Es accionable semanalmente y está directamente conectada con ingresos, riesgo y gobernanza.

**Cómo se conecta con la ejecución:**

- Ancla el funnel de originación → cashflow (pancake/replines) al medir solo clientes que repiten y generan recuperaciones.
- Usa los guardrails ya definidos (rotación ≥4.5×, default/NPL <4%, concentración Top-10 ≤30%, single-obligor ≤4%).
- Alimenta el seguimiento semanal/mensual del board pack y el dashboard operativo (alertas de concentración, DPD/NPL, caída de TPV por bucket o canal).

## 2. Contexto y tesis estratégicas

1. **Mercado objetivo:** PYME formales que utilizan sus cuentas por cobrar para liquidez. La adopción de facturación electrónica facilita originación y monitoreo.
2. **Ventaja competitiva:** Motor de riesgo centrado en pagador y pricing segmentado por categoría de la línea de crédito (A–H).
3. **Cambio estratégico:** Pasar de medir solo originación a medir uso recurrente de la plataforma y calidad de cartera.
4. **Brecha previa:** El seguimiento se centraba en facturas originadas/mes; no capturaba recurrencia, expansión ni cashflow real.

## 3. Motor de valor e indicadores principales

| Etapa | Acción PYME | Valor para Abaco | Métricas asociadas |
| --- | --- | --- | --- |
| Adquisición | Alta y primera operación | Nuevos clientes | Altas mensuales por segmento (Micro/Pequeña/Mediana) |
| Compromiso | Uso recurrente de factoring | TPV recurrente | **NSM:** TPV recurrente semanal/mensual |
| Conversión | Financiación de facturas | Ingresos y margen | % facturas financiadas, APR ponderado |
| Retención/Expansión | Upsell por línea de crédito | Mayor LTV | TPV por cliente recurrente, upgrades de bucket |
| Salud de cartera | Cobro y curas | Riesgo controlado | Default rate, DPD/NPL, concentración pagador |

## 4. Definición y cálculo

**Métrica:** TPV recurrente de clientes activos (semana/mes).

- **Clientes activos:** Clientes con ≥1 operación en la ventana de medición.
- **Recurrentes:** Clientes con ≥2 periodos consecutivos con TPV>0 o que regresan tras ≥90 días (recuperados).
- **Cálculo:** Suma del Disbursement Amount de facturas financiadas por clientes recurrentes en la ventana.

**Indicadores de apoyo:**

- Tasa de financiación sobre facturas sometidas
- Tasa de repetición (clientes con operaciones en ≥2 periodos consecutivos)
- Rotación 12m cash-weighted y replines vs. plan
- Concentración por pagador y cliente (single-obligor ≤4%, Top-10 ≤30%)
- Default rate 180+ y DPD>15
- APR ponderado por mix de CategoríaLíneaCredito

## 5. Alineación con OKRs 2025-2026

| Objetivo | Resultados clave alineados con NSM | Owner |
| --- | --- | --- |
| Crecer con control de riesgo | AUM $7.4M→$16.3M; rotación ≥4.5×; NPL180+ <4%; default real <4%; concentración Top-10 ≤30% | CEO/CRO/CFO |
| Rentabilidad y liquidez | APR ponderada 34–40%; costo deuda ≤13%; DSCR ≥1.2×; utilización 75–90% | CFO |
| Go-to-market por bucket | ≥1 cierre/KAM/mes en $50–150k; upgrades $10–50k→$50–150k; MQL→SQL ≥35–50%; close ≤$10k ≥30% | Head of Sales/Head of Growth |
| Plataforma production-grade | SLA decisión ≤24h, fondeo ≤48h en ≥90%; paneles de rotación, replines, DPD/NPL en vivo; SLO ≥99.5% | CTO |
| Salud de portafolio & cobranzas | CE 6M ≥96%; desvío de replines por bucket ±2 p.p.; pérdidas dentro de banda (<4%) | Head of Risk |

## 6. Gobernanza y cadencia

- **Seguimiento:** Semanal (operativo) y mensual (board pack) del NSM y KPIs de apoyo.
- **Propiedad:** DRI de NSM: Head of Growth + CEO; Data habilita paneles; Riesgo/Finanzas validan covenants.
- **Alertas:** Brechas de concentración, DPD/NPL, desviación de replines, caída de TPV recurrente por segmento o canal.

## 7. Riesgos y mitigaciones

| Riesgo | Mitigación |
| --- | --- |
| Caída de recurrencia en buckets pequeños (G–H) | Ajustar pricing/score, reforzar onboarding y recordatorios; priorizar Pagadores prime |
| Concentración en pocos pagadores | Límites por deudor, alertas automáticas y rebalanceo de originación |
| Desalineación entre originación y cashflow | Replines y rotación cash-weighted como guardrails; comparar plan vs. real semanal |
| Data quality en facturas/colaterales | Integración DTE, validaciones automáticas, auditoría de cesiones 100% |

## 8. Por qué no usar otras métricas como NSM central

- **Facturas originadas/mes:** Mide solo adquisición y volumen bruto; no captura recurrencia, calidad ni cashflow. Fintechs como Fundbox, BlueVine y Kredito24 migraron de este enfoque a TPV recurrente al escalar.
- **LTV/CAC:** Crítico para unit economics y reporting, pero es un ratio lento y agregado; no gobierna el pulso semanal ni la calidad de cartera. SaaS/fintech líderes lo usan como métrica complementaria, no como NSM.

## 9. Benchmarks de NSM en la industria

- **TPV/GMV recurrente:** Stripe, Square, PayPal, Shopify, MercadoPago, Konfio.

## 10. Próximos pasos

1. Publicar panel de TPV recurrente con cortes por cliente (nuevo/recurrente/recuperado), bucket y pagador.
2. Activar alertas de concentración y caídas de rotación/replines vs. plan.
3. Vincular embudos por canal (Digital ≤$10k, Mixto $10–50k, KAM $50–150k) al NSM para optimizar CAC y churn.
4. Reportar NSM y KPIs de apoyo en la cadencia semanal/mensual/QBR.
