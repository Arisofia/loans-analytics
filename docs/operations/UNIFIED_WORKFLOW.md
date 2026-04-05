# Unified Production Workflow

Status: active production reference for the current repository layout.

## Process Overview

The platform has one canonical analytics flow driven by `scripts/data/run_data_pipeline.py`.
Execution can route either through the standard pipeline or the zero-cost DuckDB/Parquet path depending on the input type.

```
INPUT                         ROUTING                    PROCESSING                            OUTPUTS
CSV / Google Sheets /   ->   pipeline_router      ->   Phases 1-4 pipeline            ->   Parquet / JSON / audit
loan tape / control           (when applicable)        + optional Phase 5                    metadata / Supabase sync
de mora CSV                                                decision intelligence                + API / Streamlit views
```

## Canonical Entry Points

- CLI entry: `scripts/data/run_data_pipeline.py`
- Standard orchestrator: `backend/src/pipeline/orchestrator.py`
- Standard phases:
  - `backend/src/pipeline/ingestion.py`
  - `backend/src/pipeline/transformation.py`
  - `backend/src/pipeline/calculation.py`
  - `backend/src/pipeline/output.py`
- Decision intelligence: `backend/src/pipeline/decision_phase.py`
- Zero-cost router: `backend/src/zero_cost/pipeline_router.py`
- API entry: `backend/loans_analytics/apps/analytics/api/main.py`
- Streamlit entry: `frontend/streamlit_app/app.py`

Use `docs/operations/SCRIPT_CANONICAL_MAP.md` for all supported commands. This file documents architecture and operational flow, not command duplication.

## Runtime Flow

### 1. Ingestion

`backend/src/pipeline/ingestion.py` validates incoming data, normalizes raw inputs, and prepares Arrow-safe structures for downstream phases.

Supported live input modes include:

- local CSV inputs
- Google Sheets-backed ingestion paths
- standard pipeline datasets
- loan tape / control-de-mora files routed through `backend/src/zero_cost/pipeline_router.py`

### 2. Transformation

`backend/src/pipeline/transformation.py` applies semantic mapping, null-handling policy, type normalization, and deterministic cleaning rules.

Primary supporting configuration:

- `config/business_rules.yaml`
- `config/business_parameters.yml`
- `config/pipeline.yml`

### 3. Calculation

`backend/src/pipeline/calculation.py` computes KPIs and related analytics.

Canonical KPI authority:

- engine runner: `backend/src/kpi_engine/engine.py`
- risk formulas: `backend/src/kpi_engine/risk.py`
- revenue formulas: `backend/src/kpi_engine/revenue.py`
- KPI registry: `config/kpis/kpi_definitions.yaml`

Independent financial KPI math outside `backend/src/kpi_engine/` is not part of the target architecture.

### 4. Output

`backend/src/pipeline/output.py` exports run artifacts and audit metadata and can persist outputs for downstream consumers.

Typical outputs include:

- parquet exports
- JSON payloads
- audit metadata
- optional Supabase synchronization

### 5. Decision Intelligence

`backend/src/pipeline/decision_phase.py` is a non-blocking Phase 5 step that builds marts and features, runs decision agents, and produces decision-center artifacts when enabled.

### 6. Consumption Layers

- FastAPI routes under `backend/loans_analytics/apps/analytics/api/routes/`
- Streamlit dashboards under `frontend/streamlit_app/pages/`
- Multi-agent analysis under `backend/loans_analytics/multi_agent/`

## Triggering The Workflow

For exact commands, use `docs/operations/SCRIPT_CANONICAL_MAP.md`.

Common trigger families:

- pipeline execution
- zero-cost ETL execution
- monitoring start / health checks
- validation and migration checks
- ML training workflows

## Viewing Results

- Streamlit application: `frontend/streamlit_app/app.py`
- FastAPI application: `backend/loans_analytics/apps/analytics/api/main.py`
- generated run artifacts under the configured output locations
- Supabase tables when database sync is enabled

## Testing And Validation

Use the canonical commands documented in `docs/operations/SCRIPT_CANONICAL_MAP.md` for:

- formatting and linting
- type checking
- unit and integration-safe tests
- monitoring validation
- migration validation

Multi-agent tests require `HISTORICAL_CONTEXT_MODE=MOCK` and are not part of the default safe CI path.

## Related Documentation

- `docs/OPERATIONS.md` for the operational runbook
- `docs/OBSERVABILITY.md` for monitoring and telemetry
- `docs/FINANCIAL_PRECISION_GOVERNANCE.md` for monetary precision requirements
- `docs/DATA_GOVERNANCE.md` for deterministic data handling policy
- `REPO_MAP.md` for the current repository structure

## Summary

| Component | Canonical Path | Role |
| --- | --- | --- |
| Entry point | `scripts/data/run_data_pipeline.py` | Starts pipeline execution |
| Routing | `backend/src/zero_cost/pipeline_router.py` | Selects standard vs zero-cost path |
| Orchestration | `backend/src/pipeline/orchestrator.py` | Coordinates pipeline phases |
| KPI engine | `backend/src/kpi_engine/engine.py` | Canonical metric execution |
| Output | `backend/src/pipeline/output.py` | Exports artifacts and audit metadata |
| API | `backend/loans_analytics/apps/analytics/api/main.py` | Programmatic access |
| Streamlit | `frontend/streamlit_app/app.py` | Dashboard UI |

---

**🎯 MISSION**: Keep pipeline clean, simple, and production-ready.  
**✅ STATUS**: All projects organized by process flow.  
**🚀 READY**: Execute, monitor, update config, repeat.
