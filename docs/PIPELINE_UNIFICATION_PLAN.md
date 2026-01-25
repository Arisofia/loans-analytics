# Unified Pipeline Audit and Execution Plan

## Purpose and scope
This document consolidates the end-to-end audit scope and defines the execution plan to deliver a single, deterministic, production-grade pipeline for Cascade → analytics distribution. It emphasizes automation, observability, and configuration-driven design to eliminate manual steps and fragmentation.

## Current-state review checklist
- **Architecture walk-through**: map every ingestion, transformation, calculation, and output path across `scripts/`, `python/ingest/`, `agents/`, `workflows/`, and app integrations. Capture dependencies, entrypoints, and shared utilities.
- **Data flow tracing**: follow Cascade exports from HTTP request through storage, transformation, KPI computation, and distribution. Identify duplicate logic, circular imports, and brittle assumptions (hard-coded values, manual triggers, ad-hoc notebooks).
- **Documentation audit**: review all Markdown files (92+ noted) for redundancy, stale content, or conflicting guidance. Resolve merge conflicts, collapse duplicates (e.g., Vercel docs), and archive historical material under `/archives/` with clear "DO NOT USE IN PRODUCTION" labels.
- **Configuration and secrets**: enumerate all YAML/TOML/JSON configs, environment variables, and workflow secrets. Validate rotation policies and ensure no credentials are embedded in code or logs.
- **Testing and quality gates**: catalogue existing tests, coverage levels, lint/mypy/pylint configurations, and CI workflows. Identify gaps in data validation coverage (Pandera/Great Expectations) and missing observability hooks.

## Target architecture (single sequential pipeline)
1. **Phase 1 – Ingestion (Cascade → Raw)**
   - HTTP client with retries, rate limiting, and token refresh before expiry threshold.
   - Schema validation using Pydantic for request/response contracts and Pandera for DataFrame typing.
   - Checksum verification and duplicate detection before persistence; raw archives stored with timestamps and immutable hashes.
   - Structured JSON logging (trace_id, run_id) plus dead-letter queue handling for unrecoverable responses.
2. **Phase 2 – Transformation (Raw → Clean)**
   - Null/outlier handling, type normalization, and referential integrity checks across entities (loans, cash flows, customers).
   - Business rules and KPI derivations expressed as declarative formulas (see `config/pipelines/unified_pipeline.yml`).
   - Transformation audit log: capture input hash, output hash, validation results, and timing per step.
3. **Phase 3 – Calculation & Enrichment (Clean → Analytics-ready)**
   - KPI computation with formula traceability linking source tables and columns; enforce precision and validation ranges.
   - Time-series rollups (daily/weekly/monthly) with anomaly detection versus historical baselines.
   - Calculation manifest generated per run with lineage, owners, and thresholds for alerting.
4. **Phase 4 – Output & Distribution (Analytics-ready → Consumption)**
   - Multi-format exports (Parquet/CSV/JSON) with embedded schemas and freshness metadata.
   - Supabase/database writes within transactions; retry on transient errors with idempotent upserts.
   - Dashboard/Streamlit refresh triggers and event hooks to propagate status to downstream consumers.
   - Audit trail including data quality scores, run metadata, and SLA timers.

## Execution roadmap
- **Week 1 – Full audit**
  - Inventory modules, entrypoints, and data paths; produce dependency graph and flow diagrams.
  - Validate all config surfaces and secrets handling; flag manual interventions and environment assumptions.
  - Document findings and prioritize risk items (data quality, security, operational gaps).
- **Week 2 – Pipeline unification**
  - Implement canonical ingestion client, transformation scaffolding, and validation layers driven by `config/pipelines/unified_pipeline.yml`.
  - Remove duplicate pipelines and collapse documentation into single authoritative sources.
  - Stand up structured logging, observability hooks, and compliance logging to `logs/runs`.
- **Week 3 – Hardening and tests**
  - Achieve 80%+ coverage across ingestion, transformation, and KPI computation with unit/integration tests.
  - Add Pandera/Great Expectations suites, mypy/pylint cleanliness, and CI enforcement.
  - Finalize operational playbooks, migration steps, and rollback procedures.

## Deliverables
- **Architecture**: updated `docs/ARCHITECTURE.md` diagrams and component responsibilities covering the unified pipeline.
- **Configuration**: `config/pipeline.yml` as the single source of truth for endpoints, auth, validation thresholds, KPI formulas, and outputs.
- **Pipeline code**: canonical modules under `python/pipeline/` for ingestion, transformation, KPI computation, validation, and outputs wired to the configuration file.
- **Operational readiness**: `docs/OPERATIONS.md` with deployment, monitoring, alerting, incident response, and backup/restore steps.
- **Migration guide**: `docs/MIGRATION.md` describing cutover, validation, and rollback plans.
- **Data quality report**: validation outcomes against Cascade exports with remediation logs.

## Guardrails and standards
- **Type and validation**: Pydantic models for API I/O, Pandera schemas for DataFrames, Great Expectations for data quality checks.
- **Observability**: structured logs (JSON), Prometheus metrics, OpenTelemetry traces; run metadata must include run_id, trace_id, data version, and SLA timers.
- **Security**: environment-provided secrets only; enforce credential rotation; scrub PII in logs via compliance utilities.
- **Safety and idempotency**: deterministic re-runs, transactional writes, and dead-letter queue for unrecoverable payloads.

## Immediate actions (ready-to-execute)
- Adopt `config/pipeline.yml` as the configuration entrypoint; wire ingestion and transformation modules to read from it.
- Establish run-scoped directories under `logs/runs/<timestamp>` capturing structured logs, validation reports, manifests, and compliance outputs.
- Replace hard-coded endpoints and tokens with environment lookups defined in the unified pipeline config; implement token refresh based on `refresh_threshold_hours`.
- Introduce checksum-based duplicate detection prior to raw persistence; log hash mismatches and short-circuit downstream processing.
- Standardize exports to Parquet/CSV/JSON with schemas and freshness metadata; ensure Supabase writes are wrapped in transactions with retries.

## Success criteria and metrics
- **Automation**: zero manual steps from trigger to completion; deterministic outputs on rerun.
- **Quality**: 0 critical data quality issues, <5 minor per month; validation gates enforced in CI.
- **Performance**: end-to-end pipeline under 10 minutes with consistent timings and alerting for SLA breaches.
- **Coverage**: >80% test coverage, 100% of public APIs documented, lint/mypy/pylint with zero warnings.
- **Reliability**: <1% deployment failure rate; MTTR <15 minutes with documented rollback paths.
