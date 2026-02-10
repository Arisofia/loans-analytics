# 📋 ACTUALIZACIÓN MENSUAL - GUÍA PASO A PASO

🎯 OBJETIVO
Actualizar los datos de Octubre 2025 con nuevos datos del próximo mes.
📂 PREPARACIÓN (10 minutos)
Paso 1: Obtener los archivos CSV
Necesitas 2 archivos: Base Activa y Desembolsos del mes.
Paso 2: Crear hoja temporal
Tabla con: MES, AUM Total, AUM Anterior, Clientes, Líneas, Performing/Late/Default ($ y %), TPV, Operaciones, Clientes nuevos.
🔢 CALCULAR MÉTRICAS (10 minutos)
Incluye: AUM Growth, Portfolio Quality, Avg Client AUM, Avg Line Size, Avg Ticket, Top 10 Clients, Top 10 Debtors.
Verificaciones:
Performing% + Late% + Default% = 100%
Portfolio Quality% = 100% - Default%
avgTicket × Operaciones ≈ TPV
📝 ACTUALIZAR ARCHIVO (20 minutos)
Sección 1: Portada y KPIs (Slides 1–4)
Línea ~641: portada (subtitle, year).
~699: currentAUM.
~720–735: KPIs (aumGrowth, portfolioQuality, clientConcentration, debtorConcentration).
Sección 2: Portfolio Diagnostics (Slide 5)
~745–767: subtitle, topKPIs, portfolioBreakdown, bottomStats, footer.
Sección 3: Risk Concentration (Slide 6)
~773–820: subtitle, topClients, topDebtors, footer.
Sección 4: Monthly Growth (Slide 13)
~1200: agregar objeto nuevo al final del array monthlyData.
Sección 5: Deck 3 Historical (Slides 28–31)
~1967: historicalData agregar objeto.
~2012: currentSnapshot actualizar.
~2030: monthlyAvgData agregar objeto.
~2052: metricsData agregar objeto.
✅ VERIFICACIÓN (5 minutos)
Checklist de validación y prueba visual en navegador para Slides 1,4,5,6,13 y Deck 3 (28–31).
🚨 ERRORES COMUNES
Comas faltantes en arrays.
Sobrescribir histórico.
Formatos incorrectos.
Inconsistencias entre slides.
📊 RESUMEN VISUAL
PASO 1 CSV → PASO 2 Cálculos → PASO 3 Slides 1–6 → PASO 4 Slide 13 → PASO 5 Slides 28–31 → PASO 6 Verificación.
Total estimado: ~45 minutos.
📝 COMMIT MESSAGE SUGERIDO

```
feat: Update deck data for [MES] 2025
- Update title and all date references to [MES] 2025
- Update AUM from $X.XXM to $Y.YYM
- Update portfolio quality: X% performing, Y% late, Z% default
- Update Top 10 clients and debtors with latest data
- Add [MES] 2025 to monthly growth chart
- Add [MES] 2025 to historical data (Deck 3)
- All calculations verified and consistent
```
