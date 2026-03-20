# Análisis de Métricas API (Español)

**Estado del Documento**: Remediación P8 Documentación (stub, 2026-03-20)  
**Propietario**: Equipo de Análisis de Datos  
**Idioma**: Español  
**Guía Completa**: Ver `OBSERVABILITY.md` (en inglés)

## Descripción General

Este documento proporciona análisis de métricas de KPI accesibles a través de la API de Abaco.

## Endpoints de Métricas

### API Base

```
https://api.abaco.local/v1
```

### Métricas Disponibles

#### Calidad de Activos (Asset Quality)
- `GET /metrics/par30` — PAR30 (Portfolio at Risk, 30+ DPD)
- `GET /metrics/par90` — PAR90 (Portfolio at Risk, 90+ DPD)  
- `GET /metrics/npl` — Ratio NPL (Non-Performing Loans, amplio)
- `GET /metrics/npl90` — Ratio NPL-90 (Non-Performing Loans, estricto)

#### Riesgo
- `GET /metrics/default-probability` — Probabilidad de incumplimiento (modelo XGBoost)
- `GET /metrics/ltv-sintetico` — LTV Sintético (factoring)
- `GET /metrics/concentration` — Concentración de obligores (Top-10)

#### Finanzas
- `GET /metrics/apr-portfolio` — APR promedio ponderado
- `GET /metrics/collection-efficiency` — Eficiencia de cobro (6m)
- `GET /metrics/dscr` — Debt Service Coverage Ratio

## Ejemplo de Consulta

```bash
curl -H "Authorization: Bearer $API_KEY" \
  https://api.abaco.local/v1/metrics/par30 \
  -d '{"date": "2026-03-20"}' | jq .

# Respuesta:
{
  "metric": "par30",
  "value": 7.42,
  "unit": "percentage",
  "timestamp": "2026-03-20T10:30:00Z",
  "confidence": 0.98
}
```

## Interpretación de Resultados

| Métrica | Rango Normal | Rango Alerta | Acción |
|---------|--------------|--------------|--------|
| PAR30 | < 8% | > 12% | Escalar a Head of Risk |
| PAR90 | < 4% | > 8% | Escalar a CFO |
| NPL Ratio | < 10% | > 15% | Revisión de portfolio |
| APR Portfolio | 15-35% | > 40% | Revisión de pricing |
| DSCR | > 1.25x | < 1.0x | Sistema de alerta temprana |

## Documentación Completa

Ver los documentos en inglés para especificaciones técnicas completas:
- `OBSERVABILITY.md` — Arquitectura de monitoreo
- `KPI_CATALOG.md` — Catálogo completo de KPIs
- `KPI_SSOT_REGISTRY.md` — Registro de autoridad única (fórmulas)

## Soporte

Para preguntas sobre APIs de métricas, contactar al equipo de Data Engineering.

---

*Última actualización: 2026-03-20 (Remediación Documentación P8)*
