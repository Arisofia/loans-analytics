# FI-ANALYTICS: Analytics Pipeline Test Cases

## Test Case ID: FI-ANALYTICS-001
**Test Case Title**: Pipeline smoke execution and exit status
**Priority**: Critical
**Type**: Functional
**Preconditions**: `sample_small.csv` exists in `tests/data/archives/`
**Tags**: #smoke #cli
**Test Data Requirements**: Standard test dataset
**Parameters**: N/A
**Test Steps - Data - Expected Result**
1. Run pipeline via CLI with `--dataset` and `--output` flags - `sample_small.csv` - Exit code 0
2. Check stdout/stderr for "Pipeline start" message - N/A - Log message present
3. Verify directory contains `kpi_results.json` and `metrics.csv` - N/A - Files created

---

## Test Case ID: FI-ANALYTICS-002
**Test Case Title**: Artifact Schema and Required Fields Validation
**Priority**: Critical
**Type**: Functional
**Preconditions**: Pipeline executed successfully
**Tags**: #schema #artifacts
**Test Data Requirements**: `kpi_results.json` artifact
**Parameters**: N/A
**Test Steps - Data - Expected Result**
1. Load `kpi_results.json` and validate against `kpi_results_schema.json` - `kpi_results.json` - Schema validation passes
2. Verify `run_id` is a valid UUID4 - `run_id` - UUID format correct
3. Verify `timestamp` is in ISO 8601 format - `timestamp` - Date format correct
4. Confirm `total_receivable_usd` is present and numeric - `total_receivable_usd` - Value > 0

---

## Test Case ID: FI-ANALYTICS-003
**Test Case Title**: KPI Numerical Accuracy vs Baseline
**Priority**: High
**Type**: Functional
**Preconditions**: `baseline_kpis.json` available
**Tags**: #correctness #kpi
**Test Data Requirements**: `sample_small.csv`
**Parameters**: `tolerance = 0.05`
**Test Steps - Data - Expected Result**
1. Compare calculated `total_receivable_usd` vs baseline - computed: $4,160,000 - Within ±5%
2. Compare calculated `collection_rate_pct` vs baseline - computed: ~96.9% - Within ±5%
3. Compare `par_90_pct` vs baseline - computed: ~0.39% - Within ±5%
4. Verify no values are `NaN` or `null` - N/A - No nulls in numeric fields

---

## Test Case ID: FI-ANALYTICS-004
**Test Case Title**: Memory-Constrained Performance (Large Dataset)
**Priority**: Medium
**Type**: Performance
**Preconditions**: Synthetic 100k row dataset generated
**Tags**: #performance #scalability
**Test Data Requirements**: 100,000 records
**Parameters**: `max_memory = 2GB`, `timeout = 60s`
**Test Steps - Data - Expected Result**
1. Execute pipeline on 100k row CSV - synthetic_large.csv - Completes within 60s
2. Monitor RSS memory usage during run - N/A - Peak memory < 2GB
3. Verify output files are correctly aggregated - N/A - Artifacts produced

---

## Test Case ID: FI-ANALYTICS-005
**Test Case Title**: Missing Column Resilience (Optional Fields)
**Priority**: Medium
**Type**: Functional
**Preconditions**: Dataset missing `dpd_0_7_usd` column
**Tags**: #edge-case #robustness
**Test Data Requirements**: CSV with missing optional columns
**Parameters**: N/A
**Test Steps - Data - Expected Result**
1. Run pipeline on CSV missing DPD columns - partial_dataset.csv - Exit code 0
2. Verify `par_0_7_pct` defaults to 0.0 in JSON output - N/A - Value is 0.0
3. Check logs for warnings about missing columns - N/A - Warnings logged
