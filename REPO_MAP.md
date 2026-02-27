# REPO_MAP

Single index for where each concern lives and which command to run.

## Canonical Commands

- `make api` -> start FastAPI (`python/apps/analytics/api`)
- `make agents` -> multi-agent scenarios (`python/multi_agent`)
- `make kpis` -> unified data pipeline (`src/pipeline` via `scripts/data/run_data_pipeline.py`)
- `make test` -> default test suite
- `make e2e` -> end-to-end tests (`tests/e2e`, opt-in with `RUN_E2E=1`)
- `make clean` -> repository maintenance cleanup

## Directory Map

- `python/apps/analytics/api/` -> API models, services, endpoints
- `python/multi_agent/` -> multi-agent protocol, orchestrator, tracing, guardrails
- `python/kpis/` -> KPI engines, catalog processing, strategic reporting
- `src/pipeline/` -> ingestion, transformation, KPI calculation, output
- `streamlit_app/` -> dashboard pages and components
- `tests/` -> project-wide tests (unit/integration/e2e)
- `python/tests/` -> additional Python package tests
- `.github/workflows/` -> CI/CD pipelines and security checks
- `infra/` -> Azure Bicep, AWS Terraform, Kubernetes manifests
- `scripts/data/` -> data and pipeline execution scripts
- `scripts/maintenance/` -> cleanup, validators, status checks
- `scripts/monitoring/` -> Grafana/Prometheus setup and health scripts
- `docs/` -> operational, architecture, governance documentation
- `config/` -> KPI, pipeline and monitoring configuration
- `db/migrations/` -> SQL migration history

## Active Naming Convention

- Service modules: `*_service.py`
- Pydantic models: `*_models.py` or `models.py` inside API module
- Tests: `test_*.py`
- CLI scripts: verb-based under `scripts/<domain>/` (`run_`, `validate_`, `generate_`, `setup_`)

## Cleanup Policy

- Generated artifacts are not kept in tracked source paths.
- Deprecated files are removed when not referenced by code, workflows, docs, or Make targets.
- Canonical script list: `docs/operations/SCRIPT_CANONICAL_MAP.md`
- Folder ownership map: `docs/OWNER_MAP.md`
