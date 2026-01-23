# Abaco Loans Analytics v2.0 Architecture & Transformation Plan

## Executive Summary

Abaco's analytics estate needs to move from ad-hoc scripts and stubbed orchestration to a production-grade, auditable platform. This proposal delivers a deterministic pipeline with contract-based ingestion, automated validation, lineage capture, and department-ready semantic outputs that map directly to the provided KPI catalog.

## Current State Assessment

- **Placeholder orchestration**: The Airflow DAG defines the control flow but leaves ingestion, validation, KPI computation, and lineage as no-op placeholders, meaning no reproducibility, auditability, or alerts are currently enforced in production tasks.
- **Documentation-only architecture**: The existing architecture overview describes intended stacks and agents without binding them to executable workflows or data contracts, creating a gap between plans and operational reality.
- **Static metric expectations**: KPIs and departmental needs are documented, but there is no enforced mapping between source schemas, calculations, and published dashboards, leading to manual reconciliation and risk of drift.

## Target Architecture (Production-Grade)

### Orchestration & Scheduling

- **Engine**: Prefer **Prefect 3** for Python-native orchestration with first-class observability and retries; keep Airflow compatibility by emitting Prefect deployments to the existing scheduler during transition.
- **Execution**: Use Kubernetes agents with work queues per domain (ingestion, transform, compliance) to isolate failures and control concurrency.

### Data Contracts & Schemas

- **Contract registry**: Define pydantic-based schemas for each upstream payload (Cascade exports, collections, delinquency feeds) and store them in `src/contracts/` with versioning.
- **Schema enforcement**: Validate every ingest against the contract before writing to raw storage; fail closed with actionable error messages.

### Data Validation & Quality Gates

- **Library**: Adopt **Great Expectations** suites per contract to enforce nullability, ranges, referential integrity, and freshness for every daily run.
- **Rules of engagement**: Block promotion from raw → staging unless suites pass; emit validation artifacts to `logs/runs/{date}/` with hashes of input files and expectation results.

### Transformation & Semantic Layer

- **Engine**: Use **dbt** for SQL-first, testable transformations with sources, staging, and mart layers; integrate with existing warehouse tables referenced by the KPI catalog.
- **Python metrics**: Encapsulate non-SQL business logic (e.g., cashflow simulations) in `src/metrics/` modules with unit tests and typed signatures; expose results as dbt seeds or external tables.
- **Semantic contracts**: Maintain a YAML metric store aligning KPIs to dbt models or Python outputs, including grain, dimensions, and freshness SLAs.

### Lineage & Observability

- **Metadata**: Push run metadata (flow run ID, code revision, input hashes, contract versions) to **OpenLineage**/**OpenMetadata** for end-to-end traceability.
- **Logging**: Standardize structured logging (JSON) with request IDs and dataset hashes; ship to a centralized sink (e.g., Loki) with Grafana dashboards for pipeline SLOs.
- **Alerting**: Integrate Prefect alerts with Slack/email for failed tasks, SLA breaches, or expectation suite failures; include remediation runbook links.

### Storage & Environments

- **Raw layer**: Immutable object storage (e.g., S3/GCS) organized by source/date/hash; enforce write-once with retention policies.
- **Staging/warehouse**: BigQuery or Snowflake models managed by dbt; partitioned by load date with idempotent upserts.
- **Secrets**: Centralize credentials in Vault/Secrets Manager with short-lived tokens; mount via workload identity rather than env files.

### Security, Compliance, and Auditability

- **PII handling**: Automatic PII detection/masking in ingestion flows; store masked samples for debugging and full payloads only in secure zones.
- **Access logging**: Every dataset read/write emits an audit record with principal, purpose, and ticket reference.
- **Regulatory readiness**: Retain validation artifacts and lineage for evidencing board/investor reporting and regulator audits.

## Delivery Roadmap (Aligned to Mandate)

- **Week 1**: Complete contract definitions, expectation suites, and Prefect deployment design; publish migration guide from Airflow DAG to Prefect deployments.
- **Week 2**: Implement ingestion + validation + staging flows with automated promotion gates; deliver unit tests for contracts and Python metrics.
- **Week 3**: Build dbt models for departmental KPIs and wire semantic store; run integration tests against mock and sampled data; finalize alerting dashboards.
- **Week 4**: Production validation with shadow runs, SLO monitoring, and handoff runbooks; cutover from Airflow stubs to Prefect deployments with rollback plan.

## Technical Decisions & Trade-offs

- **Prefect vs. Airflow**: Prefect offers richer Python ergonomics and observability; retain Airflow compatibility during migration via scheduled Prefect deployments to avoid operational disruption.
- **dbt for transformations**: Provides tested, versioned SQL lineage and slim CI; paired with Python for complex simulations to balance performance and readability.
- **Great Expectations**: Chosen for declarative validations and artifacted outputs; lightweight overhead relative to building custom validators and essential for auditability.
- **Pandas vs. Polars**: Start with Pandas for wide library support in finance-specific functions; introduce Polars selectively where performance profiling shows benefits without compromising team familiarity.

## Immediate Next Actions

1. Stand up `src/contracts/` and `src/validation/` modules with initial schemas and expectation suites for Cascade exports and collections feeds.
2. Replace the placeholder Airflow tasks with Prefect flow triggers and begin emitting lineage + validation artifacts per run.
3. Define the dbt project skeleton (sources, staging, marts) aligned to the KPI mapping, ensuring every metric has a tested, version-controlled definition.
4. Publish runbooks for incident response, schema drift handling, and data quality remediation linked from alert payloads.

## Risk Register

- **Operational gap**: Current no-op DAG tasks mean silent failures; migration must prioritize instrumentation first to surface issues early.
- **Schema drift**: Upstream contract changes can silently corrupt metrics; contract versioning and expectation suites mitigate this by failing closed.
- **Security/PII**: Without deterministic masking and access logging, compliance exposure remains; enforce masking and audit hooks at ingestion.
