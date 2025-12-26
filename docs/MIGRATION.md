# Migration Guide: Legacy to Unified Pipeline

## Overview
This document outlines the transition from the legacy fragmented scripts to the new Unified Pipeline architecture. This migration ensures build integrity, traceability, and zero-drama operations.

## Key Changes

### Architecture
| Feature | Legacy State | Unified State (New) |
|---------|--------------|---------------------|
| **Orchestration** | Multiple scripts (`scrape_cascade.py`, `ingest_cascade.py`) | Single canonical `UnifiedPipeline` |
| **Validation** | Ad-hoc checks in 0-byte placeholders | Pydantic-driven strict schema enforcement |
| **Traceability** | Fragmented logs | SHA-256 checksums and Run Manifests |
| **Security** | Manual PII handling | Automated SHA-256 masking in Phase 2 |
| **Configuration** | Hard-coded variables | Centralized `config/pipeline.yml` |

## Step-by-Step Transition

### 1. Update Ingestion Triggers
Replace any calls to `scripts/ingest_cascade.py` or `scripts/scrape_cascade.py` with the new entry point:
```bash
# OLD
python scripts/ingest_cascade.py --file input.csv

# NEW
python scripts/run_data_pipeline.py --input input.csv
```

### 2. Verify Output Locations
The legacy system wrote to various directories. The Unified Pipeline defaults to `data/metrics/`. Ensure downstream consumers (dashboards, BI tools) point to the new location.

### 3. Handle Portfolio vs. Loan Data
The new pipeline is resilient to data granularity:
- If `loan_id` is present, it is used for individual records.
- If `loan_id` is missing (aggregate portfolio data), the system generates synthetic IDs (`agg_0`, `agg_1`, etc.) to maintain schema integrity.

## Decommissioned Components
The following files have been removed or archived and should no longer be used:
- `python/ingestion.py` (legacy version)
- `python/transformation.py` (legacy version)
- `scripts/scrape_cascade.py`
- `scripts/ingest_cascade.py`
- `scripts/cascade_ingest.py`
- `src/enterprise_analytics_engine.py`

## Validation of Success
A migration is successful if:
1. `python scripts/run_data_pipeline.py` completes without errors.
2. A `{run_id}_manifest.json` file is present in `data/metrics/`.
3. The manifest contains calculated KPIs for PAR30, PAR90, and CollectionRate.
