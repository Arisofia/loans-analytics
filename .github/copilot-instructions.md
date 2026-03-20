# Abaco Loans Analytics - Copilot Instructions

## Repository Scope

Production-focused lending analytics repository with:

- Unified data pipeline in `backend/src/pipeline/` and `scripts/data/run_data_pipeline.py`
- Multi-agent analytics system in `backend/python/multi_agent/`
- Operations and observability automation under `scripts/monitoring/` and `docs/OBSERVABILITY.md`

## Canonical Project Paths

- Pipeline orchestration: `backend/src/pipeline/orchestrator.py`
- Pipeline phases: `backend/src/pipeline/ingestion.py`, `backend/src/pipeline/transformation.py`, `backend/src/pipeline/calculation.py`, `backend/src/pipeline/output.py`
- Multi-agent orchestrator: `backend/python/multi_agent/orchestrator.py`
- Multi-agent protocol: `backend/python/multi_agent/protocol.py`
- Guardrails/PII redaction: `backend/python/multi_agent/guardrails.py`
- Pipeline entrypoint: `scripts/data/run_data_pipeline.py`
- Supabase setup helper: `scripts/data/setup_supabase_tables.py`

## Canonical Commands

```bash
# Environment
source .venv/bin/activate
pip install -r requirements.txt

# Pipeline
python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv
python scripts/data/run_data_pipeline.py --mode validate
python scripts/data/run_data_pipeline.py --mode dry-run

# Quality
make format
make lint
make type-check
make test

# Monitoring
make monitoring-start
make monitoring-health
```

## Engineering Rules

- Use `Decimal` for financial calculations; do not use `float` for currency.
- Keep processing deterministic and auditable (clear manifests/logging per run).
- Do not log secrets or raw PII.
- For LLM-facing workflows, sanitize/redact inputs with `python/multi_agent/guardrails.py`.
- Prefer existing canonical scripts from `docs/operations/SCRIPT_CANONICAL_MAP.md`; avoid introducing duplicate scripts for the same task.

## CI/CD Workflows in Active Use

- `.github/workflows/tests.yml`
- `.github/workflows/pr-checks.yml`
- `.github/workflows/security-scan.yml`

## Documentation Sources of Truth

- `README.md`
- `docs/SETUP_GUIDE_CONSOLIDATED.md`
- `docs/OPERATIONS.md`
- `docs/GOVERNANCE.md`
- `docs/OBSERVABILITY.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`

