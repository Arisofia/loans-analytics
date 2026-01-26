# TECH_SPEC_V2.md - Abaco Loans Analytics Pipeline v2.0

## 1. Objective

Transform the fragmented, multi-version pipeline into a unified,
contract-driven, and testable system with full data lineage and observability.

## 2. Unified Directory Structure

We will move from a scattered root to a clean, modular structure:

- `/src`: Unified source code (formerly in `src/`, `abaco_pipeline/`, `abaco_runtime/`).
- `/config`: Master configuration (`pipeline.yml`) and environment overrides.
- `/tests`: Comprehensive test suite (unit, integration, parity).
- `/docs`: Process and architecture documentation (no static data).
- `/data`: Production data (git-ignored).
- `/data_fixtures`: Versioned sample data for testing and development.

## 3. Data Flow Contract

The pipeline will follow a strict, layered approach:

1. **Ingest**: Pull raw data from Cascade, HubSpot, or CSV.
2. **Validate**: Enforce schemas using **Great Expectations** or **Pandera**.
3. **Transform**: Clean and enrich data into a canonical format.
4. **Calculate**: Compute KPIs using the unified **KPI Engine v2**.
5. **Output**: Publish artifacts (Parquet/JSON) with unique hashes and audit metadata.

## 4. KPI Governance

- **Source of Truth**: All KPI definitions live in `config/pipeline.yml`.
- **Schema Enforcement**: `config/kpi_schema_v2.json` validates all definitions.
- **Traceability**: Every metric is stamped with `run_id`, `input_hash`, and `timestamp`.

## 5. Elimination of Technical Debt

- Delete all `v1` legacy code once `v2` parity is confirmed.
- Remove all `.bak`, `demo_`, and orphaned experiment files.
- Consolidate duplicated utility functions into a single `src.utils` package.

## 6. Observability & Self-Healing

- **Logging**: Structured JSON logging for all pipeline phases.
- **Alerting**: Failure alerts via Slack/Email with actionable error contexts.
- **Idempotency**: All jobs must be idempotent and restartable from any phase.

## 7. Immediate Action Plan

1. **Inventory & Sweep**: Finalize deletion of orphaned files identified
   in Phase 1 audit.
2. **Module Consolidation**: Move `src/` contents to `src/` and resolve
   import paths.
3. **Contract Implementation**: Implement Great Expectations validation
   for the Ingest phase.
4. **Dashboard Linkage**: Update Streamlit/Next.js dashboards to pull
   from versioned artifacts.
