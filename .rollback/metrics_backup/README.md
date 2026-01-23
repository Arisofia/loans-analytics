# Metrics Backup Retention Policy

This directory contains point-in-time metric and ingest backups for audit, disaster recovery, and compliance.

## Retention Policy

- Only the most recent backup for each ingest period is retained.
- Duplicates or near-identical backups are pruned automatically.
- Backups are kept for 90 days (raw) and 2 years (processed), unless required for audit.

## Data Lineage & Manifest

- Each backup should have a manifest (JSON) with origin, transform run, and input/output hashes.
- All backups must have `_validation_passed: True` in every row.
- Schema or column changes must be versioned and flagged.

## Restore & Validation

- Restoration is tested regularly from a single backup.
- Slack/alerting is automated if any backup is created with `_validation_passed != True`.

## Compliance

- No static, dummy, or test data is kept here.
- All files are production artifacts, not examples.

## Contact

- For questions or incidents, see SECURITY.md or contact the data engineering team.
