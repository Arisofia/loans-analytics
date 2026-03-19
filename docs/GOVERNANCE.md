# Engineering Governance

## Purpose

This document defines the active governance rules for `abaco-loans-analytics`.
It intentionally excludes deprecated tooling and non-existent workflows.

## Core Principles

- Reliability first: no broken paths, no stale automation references.
- Traceability: KPI and pipeline changes must be linked to source code and docs.
- Security by default: secrets in CI/secret managers only, never in repo.
- Determinism: financial calculations must be reproducible and auditable.

## Active CI/CD Controls

The following workflows are the source of truth for repository governance:

- `.github/workflows/pr-checks.yml`
- `.github/workflows/tests.yml`
- `.github/workflows/security-scan.yml`

## Required Review and Merge Conditions

- Pull requests must pass required CI checks before merge.
- Security scan results and dependency checks must be green.
- Changes to data pipeline, KPI logic, or security-sensitive code require reviewer sign-off.
- Command and script changes must follow `docs/operations/SCRIPT_CANONICAL_MAP.md`.

## Command and Script Policy

- Use canonical commands only (no duplicate wrappers).
- Keep one active script path per task under `scripts/`.
- Remove obsolete scripts when their process is retired.
- Do not keep deprecated executable scripts in archive folders.

## Documentation Policy

- Do not reference workflows/scripts that do not exist.
- Keep operational commands centralized in `docs/operations/SCRIPT_CANONICAL_MAP.md`.
- Update docs in the same PR that changes automation paths.

## Security and Data Handling

- No hardcoded credentials, tokens, or private keys.
- Avoid PII in logs and shared artifacts.
- Use parameterized database access and validated inputs.

## Financial Precision & Monetary Calculations

**CRITICAL**: All monetary calculations must guarantee zero floating-point drift. This is non-negotiable for fintech operations.

**Complete enforcement policy**: [`docs/FINANCIAL_PRECISION_GOVERNANCE.md`](FINANCIAL_PRECISION_GOVERNANCE.md)

**Key Requirements** (summary):
1. **Storage**: All monetary amounts are stored as `Int64` (cents) in schemas and DataFrames
2. **Interest Rates**: All rates stored as `Int64` (basis points, 0.01% units)
3. **Calculations**: All financial math uses Python `Decimal` with `ROUND_HALF_UP` rounding
4. **Ingestion**: Monetary CSV/API data converted via `dollars_to_cents()` with validation
5. **Schema Enforcement**: `Float64` in monetary columns causes immediate CI/CD failure
6. **Testing**: All changes to monetary code must pass `tests/unit/test_financial_precision.py` (blocks merge)

**Code Review Requirement**: Every PR touching monetary code must verify:
- [ ] No `Float64` in monetary schema columns
- [ ] No `float()` arithmetic in calculations
- [ ] All conversions use `dollars_to_cents()` / `cents_to_dollars()`
- [ ] All aggregations use `safe_decimal_sum()`
- [ ] All divisions use `safe_decimal_divide()`
- [ ] Financial precision regression tests pass

**Violation Response**: PRs introducing float arithmetic in monetary code fail CI/CD and are blocked from merge.

## KPI Single Source of Truth

**CRITICAL**: KPIs must have single canonical implementations. Multiple implementations of the same KPI cause data integrity failures and operational confusion.

**Complete governance framework**: [`docs/KPI_SSOT_REGISTRY.md`](KPI_SSOT_REGISTRY.md)

**Inventory of fragmentation**: [`docs/KPI_IMPLEMENTATION_INVENTORY.md`](KPI_IMPLEMENTATION_INVENTORY.md)

**Change control procedures**: [`docs/KPI_CHANGE_CONTROL_CHECKLIST.md`](KPI_CHANGE_CONTROL_CHECKLIST.md)

**Key Requirements** (summary):
1. **Registry**: All KPIs defined in `config/kpis/kpi_definitions.yaml` with versioning and audit trail
2. **Formula Engine**: All KPI calculations execute through engine (Phase 2 in progress)
3. **No Duplicates**: Each KPI implemented once; consolidation roadmap in inventory
4. **Version Tracking**: Every calculation returns formula_version, execution_time, actor, timestamp
5. **Testing**: All changes require regression tests (historical data match >= 3 months)
6. **Audit Trail**: Every calculation logged with formula version, timestamp, actor, run_id

**Code Review Requirement**: Every PR touching KPI logic must verify:
- [ ] KPI defined in registry (`config/kpis/kpi_definitions.yaml`)
- [ ] Formula version incremented if formula changed
- [ ] Regression test added/updated (>= 3 months historical data)
- [ ] Impact analysis documented (% change from previous)
- [ ] Change control checklist completed

**Violation Response**: PRs with duplicate KPI implementations rejected unless consolidated or waived by data eng + finance.

## References

- `docs/FINANCIAL_PRECISION_GOVERNANCE.md` (Enforcement policy for monetary calculations)
- `docs/FINANCIAL_PRECISION_IMPLEMENTATION_GUIDE.md` (Developer quick-reference with code patterns)
- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/KPI_SSOT_REGISTRY.md` (KPI consolidation framework and architecture)
- `docs/KPI_IMPLEMENTATION_INVENTORY.md` (Current fragmentation audit and consolidation roadmap)
- `docs/KPI_CHANGE_CONTROL_CHECKLIST.md` (Change control procedures with examples)
- `docs/REPOSITORY_MAINTENANCE.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
