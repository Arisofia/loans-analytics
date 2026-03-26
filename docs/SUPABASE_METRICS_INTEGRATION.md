# Supabase Metrics Integration Guide

**Document Status**: P8 Documentation Remediation (stub, 2026-03-20)  
**Owner**: Data Engineering Team  
**Full Implementation**: Planned for Q2 2026

## Overview

Integration of real-time KPI metrics with Supabase for analytics dashboarding.

## Quick Reference

### Database Tables

- `kpi_values` — Historical KPI snapshots per calculation run
- `kpi_definitions` — KPI metadata and ownership
- `calculation_audit` — Audit trail of all KPI computations

### Setup

```bash
python scripts/data/setup_supabase_tables.py --apply
```

### Metrics Export

All pipeline outputs automatically sync to Supabase:

```bash
# See: docs/operations/SCRIPT_CANONICAL_MAP.md#data-pipeline
python scripts/data/run_data_pipeline.py --input data/samples/loans_sample_data_20260202.csv
# → kpi_values table updated
# → calculation_audit logged
```

## See Also

- `OBSERVABILITY.md` — Monitoring & alerting setup
- `OPERATIONS.md` — Day-to-day operational runbooks
- `SETUP_GUIDE_CONSOLIDATED.md` — Full environment configuration

---

*For detailed integration specifications, contact Data Engineering Team.*
