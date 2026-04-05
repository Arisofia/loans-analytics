# Operational Runbook: Loans Unified Pipeline

> **⚠️ Deprecated Integrations (Retired 2026-01)**
> References to `META_SYSTEM_USER_TOKEN` (Cascade) are no longer required.
> **Current data ingestion:** CSV files or Supabase direct queries.

## Purpose

This runbook covers deployment, execution, monitoring, incident response, and recovery for the unified data pipeline.

## Prerequisites

- Python 3.10+
- `make setup` or `pip install -r requirements.txt && pip install -r requirements-dev.txt`
- Environment variables:
  - `AZURE_STORAGE_CONNECTION_STRING` (optional)
  - `SUPABASE_URL` and `SUPABASE_ANON_KEY` or `SUPABASE_SERVICE_ROLE_KEY` (for database connectivity)

## Execution

### Canonical Commands

For all data pipeline execution commands, see **[docs/operations/SCRIPT_CANONICAL_MAP.md](./operations/SCRIPT_CANONICAL_MAP.md#data-pipeline)**.

**Quick reference:**

```bash
# Run pipeline (CSV)
python scripts/data/run_data_pipeline.py --input data/raw/loan_data.csv

# Run pipeline (Google Sheets)
python scripts/data/run_data_pipeline.py --input gsheets://DESEMBOLSOS

# Via make
make run                # Full pipeline with samples
make etl-local INPUT=<path>  # Local ETL with custom input
```

## Run Artifacts

- `logs/runs/<run_id>/<run_id>_summary.json`
- `logs/runs/<run_id>/<run_id>_manifest.json`
- `logs/runs/<run_id>/<run_id>_compliance.json`
- `data/metrics/<run_id>.parquet`
- `data/metrics/<run_id>.csv`

## Monitoring

- Validate `summary.json` status is `success`.
- Check `manifest.json` for `file_hashes` and `quality_checks`.
- Review anomaly flags in `manifest.json`.

## Incident Response

1. **Triage**: Check `logs/runs/<run_id>_summary.json` for phase failure.
2. **Validate Input**: Confirm schema and column availability.
3. **Rollback**: Re-run previous manifest outputs if latest run failed validation.
4. **Escalate**: Notify data engineering if schema drift or data contract issues detected.

## Backup and Recovery

- Raw inputs live under `data/raw/`.
- Manifests and compliance reports are stored under `logs/runs/`.
- To restore a prior run, rehydrate outputs from `data/metrics/<run_id>` and manifest.

## Additional Resources

**See [docs/operations/SCRIPT_CANONICAL_MAP.md](./operations/SCRIPT_CANONICAL_MAP.md) for:**
- All data pipeline commands
- ML training workflows
- Monitoring stack commands
- Validation and maintenance commands
- Performance testing

**For testing and validation:**
- See `docs/GOVERNANCE.md` for test strategy
- See `Makefile` targets: `make test`, `make test-baseline`, `make lint`

