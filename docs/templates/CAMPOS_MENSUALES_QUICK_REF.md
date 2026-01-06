# ⚡ REFERENCIA RÁPIDA - CAMPOS MENSUALES

🎯 UBICACIONES EN /utils/deckData.ts
Slide Ubicación Campo Dato Requerido Fuente
1 deck1.title.subtitle subtitle "Reporte Ejecutivo [MES] 2025" Manual
1 deck1.title.year year "[MES] 2025" Manual
3 deck1.marketOpportunity.currentAUM.amount amount "$___M" Base Activa: Total Pendiente
3 deck1.marketOpportunity.currentAUM.label label "AUM Actual ([MES-YY])" Manual
4 deck1.kpis.mainKPIs.aumGrowth.metric metric "___%" Calculado: MoM %
4 deck1.kpis.mainKPIs.aumGrowth.subtext subtext "$___M actual vs $___M anterior" Base Activa
4 deck1.kpis.mainKPIs.portfolioQuality.metric metric "___%" 100% - Default%
4 deck1.kpis.mainKPIs.portfolioQuality.subtext subtext "Default rate ___%, Late __%" Base Activa
4 deck1.kpis.mainKPIs.clientConcentration.metric metric "___%" Suma Top 10
4 deck1.kpis.mainKPIs.clientConcentration.subtext subtext "___% de AUM en top 10" Base Activa
4 deck1.kpis.mainKPIs.debtorConcentration.metric metric "___%" Suma Top 10
4 deck1.kpis.mainKPIs.debtorConcentration.subtext subtext "___% en top 10 pagadores" Base Activa
5 deck1.portfolioDiagnostics.subtitle subtitle "...operativa - [MES] 2025" Manual
5 deck1.portfolioDiagnostics.topKPIs.totalAUM.value value "$___M" Base Activa
5 deck1.portfolioDiagnostics.topKPIs.activeClients.value value ___ Base Activa
5 deck1.portfolioDiagnostics.topKPIs.creditLines.value value ___ Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.performing % + $ "___%" + "$___M" Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.latePayment % + $ "___%" + "$___M" Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.default % + $ "___%" + "$___M" Base Activa
5 deck1.portfolioDiagnostics.bottomStats.aprAverage.value value "___%" Manual
5 deck1.portfolioDiagnostics.bottomStats.avgClientAUM.value value "$_____" AUM / Clientes
5 deck1.portfolioDiagnostics.bottomStats.avgLineSize.value value "$_____" AUM / Líneas
5 deck1.portfolioDiagnostics.bottomStats.defaultRate.value value "___%" Base Activa
5 deck1.portfolioDiagnostics.footer footer "...al ___ de _______ 2025..." Manual
6 deck1.riskConcentration.subtitle subtitle "...pagadores - [MES] 2025" Manual
6 deck1.riskConcentration.topClients.total total "___% of AUM" Calculado
6 deck1.riskConcentration.topClients.list[0-9] items 10 objetos {name, amount, percent} Base Activa
6 deck1.riskConcentration.topDebtors.total total "___% of receivables" Calculado
6 deck1.riskConcentration.topDebtors.list[0-9] items 10 objetos {name, amount, percent} Base Activa
13 deck1.monthlyGrowth.monthlyData[NEW] object month + aum + netChange + % + newClients Base + Desembolsos
28 deck3.portfolioHistorical.historicalData[NEW] object month + aum + clients + ticket + tpv + default Base + Desembolsos
29 deck3.aumLivePortfolio.currentSnapshot.* 4 campos date + totalAUM + activeClients + avgClientAUM Base
30 deck3.avgOperationAmount.monthlyAvgData[NEW] object month + avgAmount + count + volume Desembolsos
31 deck3.monthlyOperationsMetrics.metricsData[NEW] object month + ops + volume + ticket + conv + time Desembolsos

Tiempo estimado: 30–40 minutos · Última actualización: Oct 2025
