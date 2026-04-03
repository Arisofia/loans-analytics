# Loans Analytics - Copilot Instructions

## Repository Scope

Production-focused lending analytics repository with:

- Unified data pipeline in `backend/src/pipeline/` and `scripts/data/run_data_pipeline.py`
- Multi-agent analytics system in `backend/loans_analytics/multi_agent/`
- Operations and observability automation under `scripts/monitoring/` and `docs/OBSERVABILITY.md`

## Canonical Project Paths

- Pipeline orchestration: `backend/src/pipeline/orchestrator.py`
- Pipeline phases: `backend/src/pipeline/ingestion.py`, `backend/src/pipeline/transformation.py`, `backend/src/pipeline/calculation.py`, `backend/src/pipeline/output.py`
- Multi-agent orchestrator: `backend/loans_analytics/multi_agent/orchestrator.py`
- Multi-agent protocol: `backend/loans_analytics/multi_agent/protocol.py`
- Guardrails/PII redaction: `backend/loans_analytics/multi_agent/guardrails.py`
- Pipeline entrypoint: `scripts/data/run_data_pipeline.py`
- Supabase setup helper: `scripts/data/setup_supabase_tables.py`

## Canonical Commands

**All execution commands are defined in `docs/operations/SCRIPT_CANONICAL_MAP.md` — this is the single source of truth.**

### Quick Start

```bash
# Environment
source .venv/bin/activate
pip install -r requirements.txt

# Quality & Testing
make format
make lint
make type-check
make test

# Monitoring
make monitoring-start
make monitoring-health
```

### Using Operations Map

For data pipeline, ML, monitoring, validation, and all other commands:

- **Data Pipeline**: `docs/operations/SCRIPT_CANONICAL_MAP.md#data-pipeline`
- **ML Training**: `docs/operations/SCRIPT_CANONICAL_MAP.md#ml-training`
- **Monitoring**: `docs/operations/SCRIPT_CANONICAL_MAP.md#monitoring`
- **Validation**: `docs/operations/SCRIPT_CANONICAL_MAP.md#validation`

## Engineering Rules

- Use `Decimal` for financial calculations; do not use `float` for currency.
- Keep processing deterministic and auditable (clear manifests/logging per run).
- Do not log secrets or raw PII.
- For LLM-facing workflows, sanitize/redact inputs with `backend/loans_analytics/multi_agent/guardrails.py`.
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

