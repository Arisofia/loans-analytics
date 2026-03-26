# Engineering Governance

## Purpose

This document defines the active governance rules for `loans-loans-analytics`.
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

## Secret Scanning Governance

**CRITICAL**: Repository history and incoming pull requests must be scanned for secrets before merge.

**Enforcement configuration**: [`SECURITY.md`](../SECURITY.md) and [`.gitleaks.toml`](../.gitleaks.toml)

**Key Requirements** (summary):
1. **CI/CD enforcement**: `.github/workflows/security-scan.yml` must run Gitleaks on push and pull request events.
2. **History scanning**: Secret scanning must use full git history for authoritative detection.
3. **No exceptions by default**: False positives may be allowlisted only after manual review and documented rationale.
4. **Incident response**: Any committed secret must be revoked, removed from history, and logged as a security incident.
5. **Artifact retention**: Secret scan reports must be retained for audit review.

**Code Review Requirement**: Every PR touching credentials, deployment, config, or CI files must verify:
- [ ] No hardcoded secrets introduced
- [ ] `.gitleaks.toml` allowlist changes are justified and minimal
- [ ] Security scan workflow remains active and failing on real detections
- [ ] Any example credentials are clearly placeholders only

**Violation Response**: Merges are blocked when Gitleaks detects unapproved secrets or when scan enforcement is weakened.

## Migration Governance

**CRITICAL**: Database migrations must execute deterministically and use one canonical naming convention.

**Implementation plan**: [`docs/OPERATIONS.md`](OPERATIONS.md)

**Key Requirements** (summary):
1. **Naming standard**: All migrations must use `YYYYMMDDHHMMSS_description.sql`.
2. **Deterministic order**: Alphabetic sort must equal execution order.
3. **No duplicate intent**: Superseded migrations must be removed or explicitly deprecated, not left active in parallel.
4. **Change safety**: Migration renames/deletions require backup, dependency review, and dev-environment validation.
5. **Operational traceability**: Any migration policy change must update setup and operations documentation in the same change.

**Code Review Requirement**: Every PR touching `db/migrations/` must verify:
- [ ] Migration filename follows ISO 8601 timestamp format
- [ ] Execution order remains deterministic after sort
- [ ] No duplicate or conflicting schema intent remains active
- [ ] Downstream references and setup docs are updated if needed
- [ ] Development validation evidence exists before merge

**Violation Response**: Non-deterministic or duplicate migrations are blocked from merge until resolved.

## Manual Overrides Governance

**CRITICAL**: Manual overrides are controlled exceptions and must never bypass approval, audit, or expiry review.

**Detailed framework**: [`docs/GOVERNANCE.md#manual-overrides-governance`](#manual-overrides-governance)

**Key Requirements** (summary):
1. **Approval tiers**: Overrides must follow Operational, Material, or Strategic approval thresholds based on impact.
2. **Documented rationale**: Every override must include business justification, approver, effective date, and review/expiry date.
3. **Immutable traceability**: Override changes must be reflected in version control and linked to approval evidence.
4. **Review cadence**: Active overrides require periodic review and removal or renewal at expiry.
5. **No silent overrides**: Direct edits without documented approval are treated as data integrity incidents.

**Code Review Requirement**: Every PR introducing or modifying override behavior must verify:
- [ ] Override reason and approval authority are documented
- [ ] Expiry/review date is defined unless explicitly permanent and approved
- [ ] Affected config/data files remain auditable in git history
- [ ] Monitoring or reconciliation steps are defined when material impact exists

**Violation Response**: Unauthorized or undocumented overrides must be reverted and escalated for incident review.

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

**Inventory of fragmentation**: [`docs/KPI_SSOT_REGISTRY.md`](KPI_SSOT_REGISTRY.md)

**Change control procedures**: [`docs/KPI-Operating-Model.md`](KPI-Operating-Model.md)

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
- `docs/MIGRATION_STANDARDIZATION_PLAN.md` (Migration naming standardization and execution plan)
- `docs/MANUAL_OVERRIDES_GOVERNANCE.md` (Approval, audit, and review framework for manual overrides)
- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/KPI_SSOT_REGISTRY.md` (KPI consolidation framework and architecture)
- `docs/KPI_IMPLEMENTATION_INVENTORY.md` (Current fragmentation audit and consolidation roadmap)
- `docs/KPI_CHANGE_CONTROL_CHECKLIST.md` (Change control procedures with examples)
- `docs/REPOSITORY_MAINTENANCE.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
