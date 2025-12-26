# Operational Runbook: Abaco Data Pipeline

## Deployment Procedures

### Environment Setup
Ensure the Python virtual environment is active and all dependencies are installed.
```bash
# Activate virtual environment
source .venv/bin/activate

# Install required dependencies
pip install pydantic pyarrow pandas pyyaml azure-storage-blob
```

### Configuration
The pipeline is driven by `config/pipeline.yml`. Ensure this file is updated with correct endpoints and target settings.
```yaml
# config/pipeline.yml
cascade:
  portfolio_id: abaco
outputs:
  azure:
    enabled: true
    container: pipeline-runs
```

## Execution Procedures

### Manual Pipeline Run
Run the end-to-end pipeline using the unified CLI script.
```bash
python scripts/run_data_pipeline.py --input data/abaco_portfolio_calculations_fixed.csv
```

### Options
- `--input`: Path to the raw CSV file from Cascade.
- `--user`: Identifier for the operator (e.g., your name).
- `--action`: Context for the run (e.g., `manual-adhoc`).
- `--config`: Path to a custom YAML config if needed.

## Monitoring & Observability

### Logs
The pipeline outputs structured logs to `stdout`. Monitor for:
- `[Ingestion:raw_read] success`: File successfully loaded and checksummed.
- `[Transformation:pii_masking] completed`: Sensitive data has been secured.
- `[Calculation:metric_computed] success`: KPIs have been computed with formula traceability.
- `[Output:complete] success`: Manifest generated and cloud export finished.

### Run Artifacts
Every run generates a unique set of artifacts in `data/metrics/` (or your configured output dir):
- `{run_id}.parquet`: High-performance data file.
- `{run_id}.csv`: Compatibility data file.
- `{run_id}_manifest.json`: Comprehensive execution summary (metadata, metrics, lineage).

## Troubleshooting

### Schema Validation Failures
**Symptom**: `ValueError: Schema validation failed for X rows.`
- **Action**: Inspect the raw input CSV. Ensure columns match the expected fields in `python/pipeline/ingestion.py` (e.g., `total_receivable_usd`, `total_eligible_usd`).

### Missing Dependencies
**Symptom**: `ImportError: Unable to find a usable engine; tried using: 'pyarrow'`.
- **Action**: Run `pip install pyarrow`.

### Azure Export Failures
**Symptom**: `[Output:azure_upload] skipped | {'reason': 'No connection string found'}`
- **Action**: Ensure `AZURE_STORAGE_CONNECTION_STRING` is set in your environment.
