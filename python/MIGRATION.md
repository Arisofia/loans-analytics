# MIGRATION GUIDE: KPI Engine v1 to v2
**Status**: ✅ IMPLEMENTED  
**Target Version**: 2.0  
**Last Updated**: 2026-01-29
---
## 1. Overview
This document describes the migration path from the legacy KPI calculation logic (v1) to the new `KPIEngineV2`. The v2 engine provides a standardized interface, built-in audit trails, and better error handling.
## 2. Key Changes
### Interface Standardization
- **v1**: Various functions with different return types (floats, tuples, or dicts).
- **v2**: All KPI calculators return a consistent `(value, context)` tuple.
### Audit & Traceability
- **v2**: Every calculation is logged in an `audit_trail` with timestamps, actor information, and run IDs.
### Error Handling
- **v2**: Individual KPI failures do not crash the entire pipeline; errors are captured in the result dictionary.
---
## 3. How to Migrate
### Step 1: Initialize the Engine
Replace direct function calls with the `KPIEngineV2` orchestrator.
**Old (v1):**
```python
from src.kpis.par_30 import calculate_par_30
par30_val = calculate_par_30(df)
```
**New (v2):**
```python
from python.kpis.engine import KPIEngineV2
engine = KPIEngineV2(df, actor="reporting_service")
metrics = engine.calculate_all()
par30_val = metrics["PAR30"]["value"]
```
### Step 2: Accessing On-Demand KPIs
Some KPIs are not calculated by default in `calculate_all()` but are available on-demand.
```python
ltv_val, ltv_context = engine.calculate_ltv()
```
### Step 3: Accessing the Audit Trail
To export the calculation lineage for compliance:
```python
audit_df = engine.get_audit_trail()
audit_df.to_csv("exports/kpi_audit_trail.csv", index=False)
```

The audit trail DataFrame includes:
- `timestamp`: ISO format timestamp of calculation
- `run_id`: Unique identifier for the calculation run
- `actor`: Identity of the entity requesting calculations
- `kpi_name`: Name of the KPI (e.g., "PAR30", "COLLECTION_RATE")
- `value`: Calculated value (None if calculation failed)
- `context`: Additional calculation details (formula, rows processed)
- `error`: Error message if calculation failed
- `status`: "success" or "failed"

### Step 4: Integration with Pipeline
The pipeline's `OutputPhase` can automatically export the audit trail:
```python
from src.pipeline.output import OutputPhase
from python.kpis.engine import KPIEngineV2

# Create engine and calculate KPIs
engine = KPIEngineV2(df, actor="pipeline", run_id="2026-01-29-001")
kpi_results = engine.calculate_all()

# Output phase will export audit trail to exports/kpi_audit_trail.csv
output_phase = OutputPhase(config)
output_results = output_phase.execute(
    kpi_results=kpi_results,
    run_dir=run_directory,
    kpi_engine=engine  # Pass engine for audit trail export
)
```
---
## 4. Implementation Status
### ✅ Completed
- **KPIEngineV2 Class** (`python/kpis/engine.py`):
  - Standardized `(value, context)` tuple interface
  - Built-in audit trail with full traceability
  - Error isolation (individual KPI failures don't crash pipeline)
  - Methods: `calculate_par_30()`, `calculate_collection_rate()`, `calculate_ltv()`, `calculate_all()`, `get_audit_trail()`

- **Pipeline Integration** (`src/pipeline/output.py`):
  - `OutputPhase` accepts optional `kpi_engine` parameter
  - Automatic export to `exports/kpi_audit_trail.csv`
  - Quality score calculation based on audit records
  - SLA checking based on calculation success rate

- **Testing** (`python/tests/test_kpi_engine.py`):
  - 13 comprehensive test cases
  - Error handling validation
  - Audit trail structure verification

- **Documentation**:
  - Demo script: `tools/demo_kpi_audit.py`
  - Updated migration guide with implementation details

### 🔄 In Progress
- Full dependency resolution for automated testing
- Integration with existing pipeline orchestrator

## 5. Deprecation Schedule
- **v1 Functions**: Marked as deprecated in v1.8.
- **v1 Removal**: Planned for v2.0 (Q2 2026).
Please update all dashboard widgets and scheduled reports to use `KPIEngineV2` by the end of Q1 2026.
---
**AI-driven improvements based on Vibe Solutioning standards**
