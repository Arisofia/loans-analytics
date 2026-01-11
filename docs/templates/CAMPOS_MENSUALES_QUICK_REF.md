# ⚡ REFERENCIA RÁPIDA - CAMPOS MENSUALES

🎯 UBICACIONES EN /utils/deckData.ts
Slide Ubicación Campo Dato Requerido Fuente
1 deck1.title.subtitle subtitle "Reporte Ejecutivo [MES] 2025" Manual
1 deck1.title.year year "[MES] 2025" Manual
3 deck1.marketOpportunity.currentAUM.amount amount "$___M" Base Activa: Total Pendiente
3 deck1.marketOpportunity.currentAUM.label label "AUM Actual ([MES-YY])" Manual
4 deck1.kpis.mainKPIs.aumGrowth.metric metric "___%" Calculado: MoM %
4 deck1.kpis.mainKPIs.aumGrowth.subtext subtext "$***M actual vs $***M anterior" Base Activa
4 deck1.kpis.mainKPIs.portfolioQuality.metric metric "**_%" 100% - Default%
4 deck1.kpis.mainKPIs.portfolioQuality.subtext subtext "Default rate _**%, Late **%" Base Activa
4 deck1.kpis.mainKPIs.clientConcentration.metric metric "\_**%" Suma Top 10
4 deck1.kpis.mainKPIs.clientConcentration.subtext subtext "**_% de AUM en top 10" Base Activa
4 deck1.kpis.mainKPIs.debtorConcentration.metric metric "_**%" Suma Top 10
4 deck1.kpis.mainKPIs.debtorConcentration.subtext subtext "***% en top 10 pagadores" Base Activa
5 deck1.portfolioDiagnostics.subtitle subtitle "...operativa - [MES] 2025" Manual
5 deck1.portfolioDiagnostics.topKPIs.totalAUM.value value "$***M" Base Activa
5 deck1.portfolioDiagnostics.topKPIs.activeClients.value value **_ Base Activa
5 deck1.portfolioDiagnostics.topKPIs.creditLines.value value _** Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.performing % + $ "***%" + "$***M" Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.latePayment % + $ "***%" + "$***M" Base Activa
5 deck1.portfolioDiagnostics.portfolioBreakdown.default % + $ "***%" + "$***M" Base Activa
5 deck1.portfolioDiagnostics.bottomStats.aprAverage.value value "**\_%" Manual
5 deck1.portfolioDiagnostics.bottomStats.avgClientAUM.value value "$\_\_\_**" AUM / Clientes
5 deck1.portfolioDiagnostics.bottomStats.avgLineSize.value value "$**\_**" AUM / Líneas
5 deck1.portfolioDiagnostics.bottomStats.defaultRate.value value "**_%" Base Activa
5 deck1.portfolioDiagnostics.footer footer "...al _** de **\_\_\_** 2025..." Manual
6 deck1.riskConcentration.subtitle subtitle "...pagadores - [MES] 2025" Manual
6 deck1.riskConcentration.topClients.total total "**_% of AUM" Calculado
6 deck1.riskConcentration.topClients.list[0-9] items 10 objetos {name, amount, percent} Base Activa
6 deck1.riskConcentration.topDebtors.total total "_**% of receivables" Calculado
6 deck1.riskConcentration.topDebtors.list[0-9] items 10 objetos {name, amount, percent} Base Activa
13 deck1.monthlyGrowth.monthlyData[NEW] object month + aum + netChange + % + newClients Base + Desembolsos
28 deck3.portfolioHistorical.historicalData[NEW] object month + aum + clients + ticket + tpv + default Base + Desembolsos
29 deck3.aumLivePortfolio.currentSnapshot.\* 4 campos date + totalAUM + activeClients + avgClientAUM Base
30 deck3.avgOperationAmount.monthlyAvgData[NEW] object month + avgAmount + count + volume Desembolsos
31 deck3.monthlyOperationsMetrics.metricsData[NEW] object month + ops + volume + ticket + conv + time Desembolsos

Tiempo estimado: 30–40 minutos · Última actualización: Oct 2025
