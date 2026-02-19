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
- `.github/workflows/unified-tests.yml`
- `.github/workflows/security-scan.yml`
- `.github/workflows/dependencies.yml`

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

## References

- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/REPOSITORY_MAINTENANCE.md`
- `docs/SECURITY.md`
- `docs/OPERATIONS.md`
