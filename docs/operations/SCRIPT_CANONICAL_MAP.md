# Script Canonical Map

Single source of truth for script execution paths. Use only these commands.

## Data Pipeline

- Run pipeline: `python scripts/data/run_data_pipeline.py --input data/raw/sample_loans.csv`
- Validate structure: `python scripts/maintenance/validate_structure.py`
- Analyze real input files: `python scripts/data/analyze_real_data.py --data-dir ~/Downloads`

## Synthetic Data

- Generate synthetic loan dataset: `python scripts/data/generate_sample_data.py`
- Generate synthetic KPI series: `python scripts/data/load_sample_kpis_supabase.py`
- Generate Spanish IDs for tests: `python scripts/data/seed_spanish_loans.py`

## Maintenance

- Repo maintenance: `./scripts/maintenance/repo_maintenance.sh --mode=standard`
- Repo doctor: `./scripts/maintenance/repo-doctor.sh`
- Cleanup old workflow runs: `./scripts/maintenance/cleanup_workflow_runs_by_count.sh --keep 25`
- Service status report: `python scripts/maintenance/generate_service_status_report.py`
- Infra validator (Task 1-5): `python scripts/maintenance/abaco_infra_validator.py --apply -v`

## Monitoring

- Auto-start monitoring stack: `bash scripts/monitoring/auto_start_monitoring.sh`
- Monitoring health check: `bash scripts/monitoring/health_check_monitoring.sh`
- Backup dashboards: `bash scripts/monitoring/backup_dashboards.sh`
- Restore dashboards: `bash scripts/monitoring/restore_dashboards.sh`

## Rule

- Avoid root-level wrappers (for example `scripts/run_data_pipeline.py` or `scripts/validate_structure.py`).
- Keep one active implementation path per task under `scripts/{data,maintenance,monitoring,deployment,evaluation}`.
