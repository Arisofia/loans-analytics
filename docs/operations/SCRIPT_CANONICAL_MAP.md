# Script Canonical Map

Single source of truth for script execution paths. Use only these commands.

## Data Pipeline

- Run pipeline: `python3 scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv`
- Validate structure: `python3 scripts/maintenance/validate_structure.py`
- Analyze real input files: `python3 scripts/data/analyze_real_data.py --data-dir ~/Downloads`

## Zero-Cost ETL (DuckDB + Parquet — replaces Azure)

> These are the canonical entry points for the zero-cost stack. Use `make` targets when available.

- Full pipeline (ingest + schema + snapshot): `make run`
- Tests only: `make test`
- Ingest only (loan tape or Control de Mora): `make etl-local INPUT=data/raw/<file>.csv`
- Initialise DuckDB star schema: `make zero-cost-schema`
  _(Equivalent: `python3 scripts/data/init_duckdb_schema.py`)_
- Build monthly snapshot: `make snapshot-build MONTH=2026-02-28`
  _(Equivalent: `python3 scripts/data/build_snapshot.py --month 2026-02-28`)_
- Local stack (API + dashboard via Docker): `make zero-cost-up`
- Stop local stack: `make zero-cost-down`

## Synthetic Data

- Generate synthetic loan dataset: `python3 scripts/data/generate_sample_data.py`
- Generate synthetic KPI series: `python3 scripts/data/load_sample_kpis_supabase.py`
- Generate Spanish IDs for tests: `python3 scripts/data/seed_spanish_loans.py`

## Maintenance

- Repo maintenance: `./scripts/maintenance/repo_maintenance.sh --mode=standard`
- Comprehensive cleanup (integrations/caches/orphans): `./scripts/maintenance/comprehensive_cleanup.sh --dry-run`
- Repo doctor: `./scripts/maintenance/repo-doctor.sh`
- Cleanup old workflow runs: `./scripts/maintenance/comprehensive_cleanup.sh --cleanup-workflow-runs --keep 25`
- Service status report: `python3 scripts/maintenance/generate_service_status_report.py`
- Infra validator (Task 1-5): `python3 scripts/maintenance/abaco_infra_validator.py --apply -v`

## Monitoring

- Auto-start monitoring stack: `bash scripts/monitoring/auto_start_monitoring.sh`
- Monitoring health check: `bash scripts/monitoring/health_check_monitoring.sh`

## Performance

- KPI profiler (cProfile, real/synthetic): `python3 scripts/performance/profile_kpi_engine.py --rows 1000000`
- KPI scale benchmark (pandas/polars): `python3 scripts/performance/benchmark_kpi_engine_scale.py --rows 100000,500000,1000000 --mode both`
- API load test (Locust): `locust -f tests/load/locustfile.py --headless -u 30 -r 5 -t 5m --host http://localhost:8000`

## Rule

- Avoid root-level wrappers and any duplicate command entrypoints.
- Keep one active implementation path per task under `scripts/{data,maintenance,monitoring,deployment,evaluation}`.

