# Abaco Loans Analytics - Operations Runbook

## 1. System Overview

The Abaco Loans Analytics system is a production-grade fintech intelligence
pipeline built with elite engineering standards. It orchestrates data ingestion
from multiple sources (CSV, Parquet, Excel, HTTP APIs), applies advanced
financial transformations, calculates key performance indicators (KPIs), and
generates executive reports.

**Phase 5 Status**: ✅ **Operational Deliverables Complete**
- Pylint: **9.98/10** (Excellence)
- Mypy: **0 type errors** across 112 source files
- Tests: **316 passing**, 10 skipped
- Architecture: Refactored for maintainability and type safety

## 2. Environment Setup

- **Python**: 3.9+ (3.11 recommended)
- **Virtual Environment**: `.venv`
- **Dependencies**: `pip install -r requirements.txt -r dev-requirements.txt`

### Essential Environment Variables

- `PIPELINE_ENV`: `dev`, `staging`, or `production` (default: `dev`)
- `AZURE_STORAGE_CONNECTION_STRING`: Required for Azure Blob storage outputs.
- `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE`: Required for database sync.
- `NOTION_TOKEN` / `NOTION_REPORTS_PAGE_ID`: Required for Notion reporting.
- `FIGMA_TOKEN` / `FIGMA_FILE_KEY`: Required for Figma dashboard updates.

## 3. Quality & Code Standards

### Phase 5 Improvements

The codebase has undergone comprehensive refactoring for production readiness:

- **Code Formatting**: Automated via Black, isort, and Ruff across all modules
- **Type Safety**: All 112 source files achieve mypy success (0 type errors)
- **Linting Excellence**: Pylint score improved from 9.96 to 9.98/10
- **Architectural Refactoring**:
  - `KPIMetadata`: Converted to frozen dataclass for immutable metadata handling
  - `PersistContext`: New dataclass encapsulates output persistence parameters
  - Reduced method argument counts for better readability and maintainability

### Pre-Commit Quality Checks

Before deploying any changes, run the comprehensive quality suite:

```bash
# Quick lint check (non-blocking)
make lint

# Auto-format code
make format

# Type checking
make type-check

# Full quality audit
make audit-code

# Complete quality check with tests
make quality
```

## 4. Core Operational Commands

### Running the Full Pipeline

The primary entry point for production runs is `run_complete_analytics.py`, which loads and processes real ABACO loan data:

```bash
# Execute complete analytics pipeline with all KPI calculations
python run_complete_analytics.py
```

For executive report generation:

```bash
# Generate executive report
python generate_executive_report.py
```

### Manual Pipeline Execution (Internal)

```bash
python scripts/run_data_pipeline.py --input data/raw/abaco_portfolio.csv
```

### Health & Parity Checks

```bash
# Verify KPI parity (Python vs SQL)
make test-kpi-parity

# Full system bootstrap and health check
python tools/zencoder_bootstrap.py
```

## 5. Monitoring & Artifacts

### Log Location

- **Pipeline Runs**: `logs/runs/<run_id>/`
- **Daily Logs**: `logs/abaco.analytics.log`

### Success Criteria

1. `summary.json` contains `"status": "success"`.
2. `manifest.json` is generated with valid file hashes.
3. No critical anomalies flagged in `compliance.json`.

## 6. Incident Response & Triage

### Common Failure Modes

- **Schema Drift**: If ingestion fails due to missing columns, verify the input
  file against `config/data_schemas/`.
- **Circuit Breaker**: If the pipeline stops with a circuit breaker error, check
  recent data quality trends or downstream service availability.
- **KPI Anomalies**: If reports show unexpected KPI values, run
  `tests/test_kpi_parity.py` to rule out engine inconsistencies.

### Rollback Procedure

1. Identify the last successful `run_id`.
2. Re-run reporting scripts using the cached parquet files in
   `data/metrics/<run_id>.parquet`.

## 7. Maintenance

### Quality Gates

- **Weekly**: Run `make audit-code` to ensure engineering standards (Pylint 9.98+/10, zero type errors, test coverage)
- **Before Deployment**: Execute `make quality` for full validation (format, lint, type-check, test)
- **Monthly**: Review KPI definitions in `config/kpis/kpi_definitions.yaml`

### Codebase Hygiene

Phase 5 introduced architectural best practices:
- All new features must maintain Pylint score ≥ 9.95/10
- Type hints required for all public APIs (mypy compliance)
- New methods should follow dataclass patterns for parameter management
- No positional arguments beyond 3; use dataclasses or dict unpacking for optional parameters

### Deprecation Schedule

- **v2.0 Cutover** (Q1 2026): Delete `config/LEGACY/` and archived modules as per MIGRATION.md

---

*Confidential - Abaco Loans Operations*  
**Last Updated**: Phase 5 - January 2026*
