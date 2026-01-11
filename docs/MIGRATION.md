# Migration Guide: Legacy Pipeline -> Unified Pipeline

## Goal

Move all ingestion, transformation, and KPI computation to the unified pipeline without data loss or downtime.

## Scope

- Replace ad-hoc ingestion scripts with `src/pipeline/orchestrator.py`.
- Consolidate KPI calculations under `config/pipeline.yml` and `config/kpi_definitions_unified.yml`.
- Centralize run artifacts under `logs/runs/`.

## Step-by-Step Migration

### 1. KPI Engine v1 to v2

Replace direct function calls with the `KPIEngineV2` orchestrator for consistent interfaces and audit trails.

**Old (v1):**

```python
from src.kpis.par_30 import calculate_par_30
par30_val = calculate_par_30(df)
```

**New (v2):**

```python
from src.kpis import KPIEngineV2
engine = KPIEngineV2(df, actor="reporting_service")
metrics = engine.calculate_all()
par30_val = metrics["PAR30"]["value"]
```

### 2. Update Entry Points

**Old**

```bash
python scripts/ingest_cascade.py --file input.csv
```

**New**

```bash
python scripts/run_data_pipeline.py --input data/archives/cascade/loan_tape.csv
```

### 2. Validate Schemas

- Ensure `config/data_schemas/loan_tape.json` matches Cascade export columns.
- Confirm required numeric columns exist before moving to strict mode.

### 3. Run Dual Mode (1-2 weeks)

- Run unified pipeline in parallel with legacy processes.
- Compare KPI outputs with existing dashboards.
- Record discrepancies in `logs/runs/<run_id>_summary.json` and data quality report.

### 4. Cutover

- Switch scheduling/orchestration to unified pipeline entry point.
- Deprecate legacy scripts and update runbooks.

## Validation Checklist

- Manifest exists under `logs/runs/<run_id>/<run_id>_manifest.json`.
- Compliance report generated under `logs/runs/<run_id>/<run_id>_compliance.json`.
- KPI values match expected ranges and prior baselines.

## Rollback Plan

- Re-run last known good manifest outputs from `data/metrics/<run_id>`.
- If schema drift is detected, revert `config/pipeline.yml` and re-run in strict=false mode.

## Timeline and Risks

- **Week 1**: Dual runs and schema alignment.
- **Week 2**: Update dashboards to new outputs.
- **Week 3**: Cutover and retire legacy scripts.

**Risks**

- Schema drift from Cascade exports.
- Hidden dependencies on legacy output locations.
- KPI deltas caused by normalization changes.

**Mitigations**

- Run dual-mode reconciliation for at least 2 weeks.
- Maintain output backward-compatible CSV/Parquet.
- Keep legacy wrappers for test stability during migration.
