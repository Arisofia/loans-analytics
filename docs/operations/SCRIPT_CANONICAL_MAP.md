# Script Canonical Map

Single source of truth for script execution paths. Use only these commands.

## Data Pipeline

- Run pipeline: `python3 scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv`
- Analyze real input files: `python3 scripts/data/analyze_real_data.py --data-dir ~/Downloads`
- Local monthly ETL: `python3 scripts/data/local_monthly_etl.py`

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

## Synthetic Data (Test Fixtures)

> These generators live in `tests/fixtures/` — they are for testing/development only and must not be run in production.

- Generate synthetic loan dataset: `python3 tests/fixtures/generate_sample_data.py`
- Generate synthetic KPI series: `python3 tests/fixtures/load_sample_kpis_supabase.py`
- Generate Spanish IDs for tests: `python3 tests/fixtures/seed_spanish_loans.py`

## Maintenance

- Service status report: `python3 scripts/maintenance/generate_service_status_report.py`
- Validate migration index: `python3 scripts/maintenance/validate_migration_index.py`

## ML Training

- Train default risk model: `python3 scripts/ml/train_default_risk_model.py`
- Train WoE/IV scorecard: `python3 scripts/ml/train_scorecard.py`
- Retrain pipeline: `python3 scripts/ml/retrain_pipeline.py`

## Monitoring

- Auto-start monitoring stack: `bash scripts/monitoring/auto_start_monitoring.sh`
- Monitoring health check: `bash scripts/monitoring/health_check_monitoring.sh`
- Harden RLS on sensitive tables: `DATABASE_URL=... bash scripts/monitoring/harden_rls_sensitive_tables.sh`

## Validation

- Validate migration order: `python3 scripts/validation/validate_migration_order.py`
- Validate port consistency: `python3 scripts/validation/validate_port_consistency.py`
- Validate doc links: `python3 tools/validate_doc_links.py`

## Performance

- API load test (Locust): `locust -f tests/load/locustfile.py --headless -u 30 -r 5 -t 5m --host http://localhost:8000`

## Rule

- Avoid root-level wrappers and any duplicate command entrypoints.
- Keep one active implementation path per task under `scripts/{data,maintenance,monitoring,deployment,evaluation}`.

