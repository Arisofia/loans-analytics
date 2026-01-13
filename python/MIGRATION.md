# MIGRATION GUIDE: KPI Engine v1 to v2

**Status**: 🔵 DRAFT  
**Target Version**: 2.0  
**Last Updated**: 2026-01-03

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
from src.kpi_engine_v2 import KPIEngineV2

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
```bash
audit_df = engine.get_audit_trail()
audit_df.to_csv("kpi_audit_log.csv")
```

---

## 4. Deprecation Schedule

- **v1 Functions**: Marked as deprecated in v1.8.
- **v1 Removal**: Planned for v2.0 (Q1 2026).

Please update all dashboard widgets and scheduled reports to use `KPIEngineV2` by the end of Q1 2026.

---
**AI-driven improvements based on Vibe Solutioning standards**
