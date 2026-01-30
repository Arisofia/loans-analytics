# Operational Runbook: Abaco Unified Pipeline

> **⚠️ Deprecated Integrations (Retired 2026-01)**
>
> The following integrations have been fully retired: **Slack, HubSpot, Notion, Cascade, Looker**.
> References to `META_SYSTEM_USER_TOKEN` (Cascade) are no longer required.
> **Current data ingestion:** CSV files or Supabase direct queries.

## Purpose

This runbook covers deployment, execution, monitoring, incident response, and recovery for the unified data pipeline.

## Prerequisites

- Python 3.10+
- `pip install -r requirements.lock.txt` (or the project-standard install)
- Environment variables:
  - `AZURE_STORAGE_CONNECTION_STRING` (optional)
  - `SUPABASE_URL` and `SUPABASE_KEY` (for database connectivity)

## Execution

### Manual Run (Canonical)

```bash
python scripts/run_data_pipeline.py --input data/raw/cascade/loan_tape.csv
```

### Configuration Override

```bash
python scripts/run_data_pipeline.py \
  --input data/archives/loan_tape.csv \
  --config config/pipeline.yml
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

- Raw inputs are archived under `data/archives/cascade`.
- Manifests and compliance reports are stored under `logs/runs/`.
- To restore a prior run, rehydrate outputs from `data/metrics/<run_id>` and manifest.

## Ready-to-Execute Commands

1. Run pipeline with file input:
   ```bash
   python scripts/run_data_pipeline.py --input data/raw/cascade/loan_tape.csv
   ```
2. Run tests:
   ```bash
   pytest tests/ -v
   ```
3. Validate config:
   ```bash
   python -c "from src.pipeline.orchestrator import PipelineConfig; PipelineConfig()"
   ```
