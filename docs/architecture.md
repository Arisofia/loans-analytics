# Abaco Loans Analytics - Unified Pipeline Architecture

## Executive Summary
The Abaco unified pipeline is the canonical, production-grade workflow for ingestion, transformation, calculation, and distribution of Cascade loan analytics. It replaces fragmented scripts with a single, configuration-driven system that is traceable, auditable, and idempotent.

## System Diagram

```
                 +------------------------------+
                 |      Unified Pipeline        |
                 | python/pipeline/orchestrator |
                 +---------------+--------------+
                                 |
                                 v
+-------------------+    +------------------+    +-------------------+    +------------------+
| Phase 1 Ingestion | -> | Phase 2 Transform| -> | Phase 3 Calculation| -> | Phase 4 Output   |
| python/pipeline/  |    | python/pipeline/ |    | python/pipeline/   |    | python/pipeline/ |
| ingestion.py      |    | transformation.py|    | calculation_v2.py  |    | output.py        |
+-------------------+    +------------------+    +-------------------+    +------------------+
           |                        |                       |                        |
           v                        v                       v                        v
      Raw archive             PII masking             KPI metrics              Manifests + exports
      checksums               quality checks          audit trail              logs/runs/<run_id>
```

## Data Flow
1. **Ingestion**: Load Cascade loan tape (CSV/JSON/Parquet or HTTP), validate schema, compute checksum, and archive raw inputs.
2. **Transformation**: Normalize columns, handle nulls, detect outliers, and mask PII using compliance utilities.
3. **Calculation**: Compute KPIs from config, produce audit trails, timeseries rollups, and anomaly flags.
4. **Output**: Persist analytics-ready data, emit manifests, and store run artifacts in `logs/runs/`.

## Component Responsibilities

### Orchestrator (python/pipeline/orchestrator.py)
- Owns run lifecycle, run_id strategy, and sequencing.
- Writes run summary to `logs/runs/<run_id>/<run_id>_summary.json`.
- Emits compliance report via `python/compliance`.

### Ingestion (python/pipeline/ingestion.py)
- Supports file and HTTP ingestion with retry, rate limiting, and circuit breaker.
- Validates against `config/data_schemas/loan_tape.json` and required columns.
- Captures checksums and archives raw inputs to `data/raw/cascade`.

### Transformation (python/pipeline/transformation.py)
- Normalizes column names and trims strings.
- Handles nulls and outliers.
- Applies PII masking and produces access logs.

### Calculation (python/pipeline/calculation_v2.py)
- Computes KPIs from `config/pipeline.yml` function mappings.
- Produces KPI audit trail and optional timeseries rollups.
- Flags anomalies via baseline comparison in `logs/runs/`.

### Output (python/pipeline/output.py)
- Persists data in Parquet/CSV/JSON.
- Generates manifest with hashes, lineage, and compliance links.
- Optional Azure upload when enabled.

## Configuration System

### Pipeline Configuration
- **File**: `config/pipeline.yml`
- **Purpose**: Single source of truth for ingestion, transformation, calculation, outputs, and observability.

### KPI Definitions
- **File**: `config/kpi_definitions_unified.yml`
- **Purpose**: KPI ownership, formula, thresholds, and data sources.

### Schema Definitions
- **File**: `config/data_schemas/loan_tape.json`
- **Purpose**: Required fields and type validation for Cascade loan tape.

## Run Artifacts (logs/runs/<run_id>)
- `<run_id>_summary.json`: Pipeline status and phase results.
- `<run_id>_manifest.json`: Full output manifest with hashes and outputs.
- `<run_id>_compliance.json`: PII masking and access logs.

## Deployment Architecture
- **Local / CI**: `python scripts/run_data_pipeline.py --input <file>`
- **Container**: `Dockerfile.pipeline` (batch execution)
- **Cloud**: Azure Blob Storage upload via output phase when enabled

## Security and Compliance
- PII masking enforced in Phase 2 (configurable keywords).
- Compliance reports written to `logs/runs/` for auditability.
- Secrets read from environment variables only.

## Observability
- Structured log events by phase.
- Manifest includes input/output hashes and audit logs.
- Anomaly detection compares against previous runs.

## Compatibility Layer
Legacy wrappers are retained for test stability and existing scripts:
- `python/ingestion.py` (`CascadeIngestion`)
- `python/transformation.py` (`DataTransformation`)
- `scripts/run_data_pipeline.py` (`run_pipeline`)
