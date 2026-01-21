# Operational Runbook: Abaco Unified Pipeline

## Purpose

This runbook covers deployment, execution, monitoring, incident response, and recovery for the unified data pipeline.

## Prerequisites

- Python 3.10+
- `pip install -r requirements.lock.txt` (or the project-standard install)
- Environment variables:
  - `AZURE_STORAGE_CONNECTION_STRING` (optional)

## Execution

### Manual Run (Canonical)

```bash
```

### Configuration Override

```bash
python scripts/run_data_pipeline.py \
  --config config/pipeline.yml
```


Set in `config/pipeline.yml`:

```yaml
pipeline:
  phases:
    ingestion:
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

- Manifests and compliance reports are stored under `logs/runs/`.
- To restore a prior run, rehydrate outputs from `data/metrics/<run_id>` and manifest.

## Ready-to-Execute Commands

1. Run pipeline with file input:

   ```bash
   ```

2. Run tests:

   ```bash
   pytest tests/ -v
   ```

3. Validate config:

   ```bash
   python -c "from src.pipeline.orchestrator import PipelineConfig; PipelineConfig()"
   ```
