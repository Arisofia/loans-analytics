# 📋 PLANTILLA DE ACTUALIZACIÓN MENSUAL - DECKDATA.TS

## 🎯 INSTRUCCIONES DE USO

**Propósito**: Este documento lista TODOS los campos que debes actualizar cada mes en `/utils/deckData.ts` cuando recibas nuevos datos del CSV.

**Cómo usar**:

1. Copia esta plantilla.
2. Llena los campos con los nuevos datos del mes.
3. Actualiza el archivo `/utils/deckData.ts` siguiendo la ubicación exacta indicada.
4. Verifica que todos los cálculos matemáticos sean correctos.

---

## 📅 MES A ACTUALIZAR: [_______]

**Fecha de corte de datos**: [_**/**_/2025]  
**Archivo fuente CSV**: [nombre_archivo.csv]

---

## 🔴 DECK 1: Portfolio Analysis & Strategy

### 📌 SLIDE 1: Title (Portada)

**Ubicación**: `deck1.title`

```typescript
title: {
  mainTitle: "Abaco",
  subtitle: "Reporte Ejecutivo [MES] 2025", // ← ACTUALIZAR MES
  year: "[MES] 2025" // ← ACTUALIZAR MES
}
```

Campos a llenar:

 subtitle: "Reporte Ejecutivo _________ 2025"

 year: "_________ 2025"

📌 SLIDE 2: TAM Funnel (No requiere actualización mensual)

Ubicación: deck1.tamFunnel

❌ SKIP - Datos estáticos de mercado

📌 SLIDE 3: Market Opportunity

Ubicación: deck1.marketOpportunity.currentAUM

Always show details
currentAUM: {
  amount: "$___M", // ← AUM actual del mes
  label: "AUM Actual ([MES-YY])" // ← ACTUALIZAR MES
}

Campos a llenar:

 amount: "$_____M"

 label: "AUM Actual (_-)"

Fuente de datos: Total Pendiente en Base Activa

📌 SLIDE 4: KPIs - Top 4 Metrics

Ubicación: deck1.kpis.mainKPIs

KPI 1: AUM Growth
Always show details
aumGrowth: {
  metric: "_____%", // ← % de crecimiento MoM (puede ser negativo)
  description: "MoM Growth Rate",
  subtext: "$___M actual vs $___M mes anterior" // ← ACTUALIZAR ambos valores
}

Cálculo

Always show details
% Growth = ((AUM_actual - AUM_mes_anterior) / AUM_mes_anterior) × 100

Campos a llenar

 metric: "______%"

 subtext: "$____M actual vs $____M mes anterior"

KPI 2: Portfolio Quality
Always show details
portfolioQuality: {
  metric: "_____%", // ← 100% - Default Rate
  description: "Performing Portfolio",
  subtext: "Default rate ___%, Late___%" // ← ACTUALIZAR ambos %
}

Cálculo

Always show details
Portfolio Quality % = 100% - Default Rate (90+ DPD)

Campos a llenar

 metric: "______%"

 subtext: "Default rate ___%, Late___%"

KPI 3: Client Concentration
Always show details
clientConcentration: {
  metric: "___**%", // ← % suma del Top 10 Clientes
  description: "Top 10 Clients",
  subtext: "**_% de AUM en top 10 clientes" // ← ACTUALIZAR
}

Cálculo

Always show details
Concentración = Suma de % de los 10 clientes más grandes

Campos a llenar

 metric: "______%"

 subtext: "___% de AUM en top 10 clientes"

KPI 4: Debtor Concentration
Always show details
debtorConcentration: {
  metric: "___**%", // ← % suma del Top 10 Pagadores
  description: "Top 10 Debtors",
  subtext: "**_% de receivables en top 10 pagadores" // ← ACTUALIZAR
}

Cálculo

Always show details
Concentración = Suma de % de los 10 pagadores más grandes

Campos a llenar

 metric: "______%"

 subtext: "___% de receivables en top 10 pagadores"

📌 SLIDE 5: Portfolio Diagnostics

Ubicación: deck1.portfolioDiagnostics

Subtitle (Fecha de corte)
Always show details
subtitle: "Análisis detallado de AUM, calidad y estructura operativa - [MES] 2025"

Campos a llenar

 subtitle: "Análisis detallado de AUM, calidad y estructura operativa - _____ 2025"

Top KPIs
Always show details
topKPIs: {
  totalAUM: { value: "$___M", label: "Assets Under Management" },
  activeClients: { value:___, label: "Clientes activos con líneas abiertas" },
  creditLines: { value: ___, label: "Líneas de crédito totales activas" }
}

Campos a llenar

 totalAUM.value: "$______M"

 activeClients.value: _____

 creditLines.value: _____

Fuente: CSV Base Activa

Portfolio Breakdown
Always show details
portfolioBreakdown: {
  performing: { percent: "___**%", amount: "$___M" },
  latePayment: { percent: "_____%", amount: "$_**M" },
  default: { percent: "**_**%", amount: "$___M" }
}

Verificación: performing% + late% + default% = 100%

Bottom Stats
Always show details
bottomStats: {
  aprAverage: { value: "_****%", label: "Tasa promedio anual" },
  avgClientAUM: { value: "$_____," label: "Promedio por cliente" },
  avgLineSize: { value: "$****_," label: "Promedio por línea" },
  defaultRate: { value: "_____%", label: "Tasa de mora > 90 días" }
}

Cálculos

Always show details
avgClientAUM = AUM Total / Clientes Activos
avgLineSize = AUM Total / Líneas de Crédito
defaultRate = Default % (de portfolioBreakdown)

Footer
Always show details
footer: "Datos actualizados al ___ de _______ 2025. Default calculado como % del AUM total con mora > 90 días."

📌 SLIDE 6: Risk Concentration

Ubicación: deck1.riskConcentration

Subtitle
Always show details
subtitle: "Concentración en top clientes y pagadores - [MES] 2025"

Top 10 Clientes
Always show details
topClients: {
  total: "__**% of AUM",
  list: [
    { name: "**_", amount: "$_**k", percent: "**_%" },
    ...
  ]
}

Top 10 Pagadores
Always show details
topDebtors: {
  total: "__**% of receivables",
  list: [
    { name: "**_", amount: "$_**k", percent: "**_%" },
    ...
  ]
}

Footer
Always show details
footer: "Datos de concentración al ___ de _______ 2025. Ordenados por exposure de AUM."

📌 SLIDE 13: Monthly Growth

Ubicación: deck1.monthlyGrowth.monthlyData
⚠️ AGREGAR nuevo objeto al FINAL del array

Always show details
{
  month: "[MES] 2025",
  aum: "$___M",
  netChange: "$_**M",
  percentGrowth: "**___%",
  newClients: ___
}

Cálculos

Always show details
netChange = AUM_actual - AUM_mes_anterior
percentGrowth = (netChange / AUM_mes_anterior) × 100

🔴 DECK 3: Historical Data & Analytics
📌 SLIDE 28: Portfolio Historical

Ubicación: deck3.portfolioHistorical.historicalData
⚠️ AGREGAR al final

Always show details
{
  month: "[MES]-25",
  aum: "$___M",
  activeClients: ___,
  avgTicket: "$_**k",
  tpv: "$_**M",
  defaultRate: "**_**%"
}

📌 SLIDE 29: AUM Live Portfolio
Always show details
currentSnapshot: {
  date: "___ de ________ 2025",
  totalAUM: "$___M",
  activeClients: ___,
  avgClientAUM: "$_____"
}

Cálculo: avgClientAUM = totalAUM / activeClients

📌 SLIDE 30: Avg Operation Amount

Ubicación: deck3.avgOperationAmount.monthlyAvgData
⚠️ AGREGAR al final

Always show details
{
  month: "[MES]-25",
  avgAmount: "$___k",
  operationsCount: ___,
  totalVolume: "$___M"
}

📌 SLIDE 31: Monthly Operations Metrics

Ubicación: deck3.monthlyOperationsMetrics.metricsData
⚠️ AGREGAR al final

Always show details
{
  month: "[MES]-25",
  operations: ___,
  volume: "$___M",
  avgTicket: "$___k",
  conversionRate: "N/D",
  timeToFund: "N/D"
}

✅ CHECKLIST FINAL DE ACTUALIZACIÓN

Slide 1, 3, 4, 5, 6 actualizados

Slides 13, 28, 30, 31 con nuevo objeto agregado al final

Verificaciones matemáticas y de formato completadas

Consistencias cruzadas verificadas

Tiempo estimado: 30–45 minutos por mes
Versión: 1.0 — Última actualización: Oct 2025
