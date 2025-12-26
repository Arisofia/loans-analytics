# Operational Runbook: Abaco Unified Pipeline

## Purpose
This runbook covers deployment, execution, monitoring, incident response, and recovery for the unified data pipeline.

## Prerequisites
- Python 3.10+
- `pip install -r requirements.lock.txt` (or the project-standard install)
- Environment variables:
  - `META_SYSTEM_USER_TOKEN` (Cascade token)
  - `AZURE_STORAGE_CONNECTION_STRING` (optional)

## Execution

### Manual Run (Canonical)
```bash
python scripts/run_data_pipeline.py --input data/raw/cascade/loan_tape.csv
```

### Configuration Override
```bash
python scripts/run_data_pipeline.py \
  --input data/raw/cascade/loan_tape.csv \
  --config config/pipeline.yml
```

### HTTP Ingestion (Cascade)
Set in `config/pipeline.yml`:
```yaml
pipeline:
  phases:
    ingestion:
      source: cascade_http
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
- Raw inputs are archived under `data/raw/cascade`.
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
   python -c "from python.pipeline.orchestrator import PipelineConfig; PipelineConfig()"
   ```
