# Unified KPI Core

## Overview
The `python/analytics_core` package provides a unified KPI model, catalog, and computation engine for portfolio, growth, and operational metrics. It standardizes KPI metadata and output serialization so Streamlit and the Next.js dashboard can consume the same JSON payloads.

## Package layout
- `kpi_models.py`: Typed KPI primitives (Pydantic models) and KPI set container.
- `kpi_catalog.py`: Standard fintech KPI catalog definitions (loan book, growth, operations).
- `kpi_engine.py`: KPI computation functions for portfolio and growth KPIs.
- `kpi_store.py`: JSON persistence helpers for KPI sets.

## Streamlit exports
When KPI exports are generated in the Streamlit app, KPI sets are written to:

```
exports/kpi_sets/
  portfolio_core_latest.json
  growth_core_latest.json
```

These files are refreshed on each export run and include a timestamped history.

## Next.js API consumption
The web app exposes the latest KPI sets via:

```
GET /api/kpis
```

The route reads from `exports/kpi_sets` by default. Override the location with `KPI_REPORTS_DIR` if the KPI exports live elsewhere.

## Extending KPIs
Add or update KPI definitions in `kpi_catalog.py`, then extend the corresponding computation logic in `kpi_engine.py`.
