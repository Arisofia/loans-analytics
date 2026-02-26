# Repository Maintenance Guide

## Canonical Flow

Use one maintenance entrypoint, documented centrally in:

- `docs/operations/SCRIPT_CANONICAL_MAP.md`

Do not duplicate cleanup command blocks in other documents.

## Options Policy

- Keep one command path: `scripts/maintenance/repo_maintenance.sh`.
- Change behavior only with flags on the same command (`--dry-run`, `--mode=aggressive`, `--mode=nuclear`, `--format-only`, `--ci`).
- Do not introduce wrapper scripts or duplicated maintenance docs.

## Current References

- Command map: `docs/operations/SCRIPT_CANONICAL_MAP.md`
- Script source: `scripts/maintenance/repo_maintenance.sh`

## Quick Validation

Run after major cleanup refactors using the commands defined in:

- `docs/operations/SCRIPT_CANONICAL_MAP.md`
