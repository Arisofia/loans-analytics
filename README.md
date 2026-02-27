# Abaco Loans Analytics - Unified Pipeline Platform

[![Pipeline](https://img.shields.io/badge/Pipeline-Operational-brightgreen)]()
[![Structure](https://img.shields.io/badge/Structure-Validated-success)]()
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

This repository contains the Abaco financial analytics platform:

- Unified 4-phase pipeline: Ingestion -> Transformation -> Calculation -> Output
- Multi-agent analysis modules under `python/multi_agent/`
- Streamlit dashboard and monitoring automation

## Current status

- Canonical command map: `docs/operations/SCRIPT_CANONICAL_MAP.md`
- Repository architecture index: `REPO_MAP.md`
- Folder ownership map: `docs/OWNER_MAP.md`
- Master no-stop delivery checklist: `docs/operations/MASTER_DELIVERY_TODO.md`
- Pipeline ingestion requires explicit real input (`--input`). Dummy/sample fallback is disabled.
- KPI engine profiling and scale benchmarks available under `scripts/performance/`.
- Multi-agent providers include OpenAI, Anthropic, Gemini, and Grok (xAI-compatible API).
- Multi-cloud deployment baseline includes Azure Bicep + AWS Terraform starter + Kubernetes manifests.

Last reviewed: 2026-02-20

## Prerequisites

- Python 3.10+
- Git
- Optional: Docker (monitoring stack), Azure CLI (infra/deployment)

## Quick start

1. Clone and enter repository

```bash
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics
```

2. Create environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Short entry points:

```bash
make api
make agents
make kpis
make test
make e2e
```

3. Validate repository structure

```bash
python3 scripts/maintenance/validate_structure.py
```

4. Run pipeline with real input

```bash
# Full execution
python3 scripts/data/run_data_pipeline.py \
  --input data/raw/abaco_real_data_20260202.csv \
  --mode full

# Ingestion-only check
python3 scripts/data/run_data_pipeline.py \
  --input data/raw/abaco_real_data_20260202.csv \
  --mode dry-run

# Stop after transformation
python3 scripts/data/run_data_pipeline.py \
  --input data/raw/abaco_real_data_20260202.csv \
  --mode validate
```

5. Launch dashboard

```bash
streamlit run streamlit_app.py
```

6. Start monitoring stack (optional)

```bash
bash scripts/monitoring/auto_start_monitoring.sh
```

## Repository map

### Core pipeline

`src/pipeline/`

- `orchestrator.py`
- `ingestion.py`
- `transformation.py`
- `calculation.py`
- `output.py`
- `config.py`

### Configuration

`config/`

- `pipeline.yml`
- `business_rules.yaml`
- `kpis/kpi_definitions.yaml`

### Scripts (canonical paths)

- `scripts/data/run_data_pipeline.py`
- `scripts/maintenance/validate_structure.py`
- `scripts/maintenance/abaco_infra_validator.py`
- `scripts/maintenance/repo_maintenance.sh`
- `scripts/monitoring/auto_start_monitoring.sh`
- `scripts/performance/profile_kpi_engine.py`
- `scripts/performance/benchmark_kpi_engine_scale.py`

### Apps and analytics

- `streamlit_app.py` and `streamlit_app/`
- `python/apps/analytics/api/`
- `python/multi_agent/`

### Infra

- Azure Bicep: `infra/*.bicep`
- AWS Terraform starter: `infra/aws/`
- Kubernetes baseline manifests: `infra/kubernetes/`

## Output artifacts

Pipeline runs are written under `logs/runs/<run_id>/`, including:

- `raw_data.parquet`
- `clean_data.parquet`
- `kpi_results.parquet`
- `calculation_manifest.json`
- `kpis_output.parquet`
- `kpis_output.csv`
- `kpis_output.json`
- `pipeline_results.json`

## Validation and testing

Repository and pipeline checks:

```bash
python3 scripts/maintenance/validate_structure.py
python3 scripts/maintenance/abaco_infra_validator.py -v
```

Quality checks:

```bash
ruff check .
black --check .
```

Tests:

```bash
# Main test suite (CI-aligned)
pytest tests/ -v --tb=short -m "not integration"

# Multi-agent suite
pytest python/multi_agent/ -v -k "test_" --tb=short

# Integration tests (requires Supabase secrets)
pytest tests/ -v -m "integration" --tb=short
```

## Security and CI

- Security workflow: `.github/workflows/security-scan.yml`
- Dependency scan uses Snyk with fail-on High/Critical when token is configured.
- Tests workflow: `.github/workflows/tests.yml`

## Documentation

Start here:

- `docs/README.md`
- `docs/SETUP_GUIDE_CONSOLIDATED.md`
- `docs/OPERATIONS.md`
- `docs/GOVERNANCE.md`
- `docs/OBSERVABILITY.md`
- `docs/API_SECURITY_GUIDE.md`
- `docs/ML_CONTINUOUS_LEARNING_ROADMAP.md`
- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/operations/MASTER_DELIVERY_TODO.md`

## Contributing

1. Validate structure with canonical command.
2. Implement changes with tests and lint.
3. Run real-data pipeline checks for affected flow.
4. Open PR to `main`.

## License

Proprietary - Abaco Financial Services.
