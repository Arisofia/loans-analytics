# FI-ANALYTICS: Analytics Pipeline Test Plan

## Objectives
- Validate the accuracy of KPI calculations against verified baselines.
- Ensure the pipeline handles unbounded datasets in memory-constrained environments.
- Verify compliance with output schemas (JSON/CSV) for downstream consumption by Portfolio Managers.
- Confirm robust execution as a scheduled GitHub Actions CI/CD task.

## Scope
- **`src/analytics/run_pipeline.py`**: Core calculation logic and CLI interface.
- **KPI Calculations**: Portfolio-wide and segment-level (Consumer/SME) metrics.
- **Artifact Generation**: `kpi_results.json` and `metrics.csv`.
- **Error Handling**: Graceful failure for missing columns or malformed CSV data.

## Out of Scope
- Frontend visualization in dashboards (covered by web tests).
- Real-time streaming data ingestion.
- Multi-currency conversion (USD assumed).

## Test Approach
- **Automated Smoke Tests**: Verify pipeline execution and artifact existence.
- **Data Correctness Tests**: Compare computed KPIs against `baseline_kpis.json` with a 5% tolerance.
- **Performance/Stress Tests**: Simulate large datasets to monitor memory usage and execution time.
- **Edge Case Tests**: Validate behavior with empty datasets, missing columns, and partial data.

## Test Environment Requirements
- **Python 3.9+** with `pandas` and `pytest`.
- **Memory**: Max 2GB (simulating memory-constrained CI environments).
- **Test Data**: Canonical `sample_small.csv` and generated synthetic large datasets.

## Risk Assessment
- **Memory Exhaustion**: Large CSV files may cause OOM (Out of Memory) errors in CI runners. *Mitigation: Monitor memory during stress tests.*
- **Calculation Drift**: Changes in segment logic may lead to inaccurate KPIs for Portfolio Managers. *Mitigation: Maintain strict baseline matching.*
- **Schema Breaking Changes**: Modifications to JSON structure may break downstream dashboard APIs. *Mitigation: Schema validation in every test run.*

## Key Checklist Items
- [ ] Pipeline exits with code 0 on valid data.
- [ ] `kpi_results.json` matches the required JSON schema.
- [ ] Portfolio-level KPIs are within 5% of baselines.
- [ ] Consumer and SME segments are calculated correctly.
- [ ] Pipeline logs "Pipeline start" and "success" clearly.

## Test Exit Criteria
- 100% of automated tests (Smoke, Correctness, Schema) passing.
- No memory leaks detected during 100k row processing.
- All artifact fields populated (no unexpected nulls).
