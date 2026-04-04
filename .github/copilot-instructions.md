# Loans Analytics - Copilot Instructions

## Repository Scope

Production-focused lending analytics repository with:

- Unified data pipeline in `backend/src/pipeline/` and `scripts/data/run_data_pipeline.py`
- Zero-cost ETL path (DuckDB + Parquet) in `backend/src/zero_cost/`, routed by `backend/src/zero_cost/pipeline_router.py`
- Multi-agent analytics system in `backend/loans_analytics/multi_agent/`
- Decision Intelligence phase (Phase 5) in `backend/src/pipeline/decision_phase.py`
- Streamlit frontend in `frontend/streamlit_app/` (11 pages)
- Operations and observability automation under `scripts/monitoring/` and `docs/OBSERVABILITY.md`

## Canonical Project Paths

### Pipeline

- Pipeline orchestration: `backend/src/pipeline/orchestrator.py`
- Pipeline phases: `backend/src/pipeline/ingestion.py`, `backend/src/pipeline/transformation.py`, `backend/src/pipeline/calculation.py`, `backend/src/pipeline/output.py`
- Decision Intelligence (Phase 5, non-blocking): `backend/src/pipeline/decision_phase.py`
- Pipeline router (standard vs. zero-cost): `backend/src/zero_cost/pipeline_router.py`
- Pipeline entrypoint: `scripts/data/run_data_pipeline.py`

### KPI & Risk

- KPI engine (SSoT): `backend/loans_analytics/kpis/engine.py`
- Asset quality formulas (PAR/NPL): `backend/loans_analytics/kpis/ssot_asset_quality.py`
- KPI definitions config: `config/kpis/kpi_definitions.yaml`
- Default risk model (XGBoost): `backend/loans_analytics/models/default_risk_model.py`

### Multi-Agent System

- Multi-agent orchestrator: `backend/loans_analytics/multi_agent/orchestrator.py`
- Multi-agent protocol: `backend/loans_analytics/multi_agent/protocol.py`
- Guardrails/PII redaction: `backend/loans_analytics/multi_agent/guardrails.py`
- Feature store builders: `backend/loans_analytics/multi_agent/feature_store/`

### API & Frontend

- FastAPI app: `backend/loans_analytics/apps/analytics/api/main.py`
- API routes (feature-based): `backend/loans_analytics/apps/analytics/api/routes/`
- Streamlit app: `frontend/streamlit_app/`

### Infrastructure

- Supabase setup helper: `scripts/data/setup_supabase_tables.py`
- Business rules config: `config/business_rules.yaml`
- Business parameters: `config/business_parameters.yml`
- DB migrations: `db/migrations/` (14-digit timestamp naming, lexicographic order)

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
- **Zero-Cost ETL**: `docs/operations/SCRIPT_CANONICAL_MAP.md#zero-cost-etl-duckdb--parquet--replaces-azure`
- **ML Training**: `docs/operations/SCRIPT_CANONICAL_MAP.md#ml-training`
- **Monitoring**: `docs/operations/SCRIPT_CANONICAL_MAP.md#monitoring`
- **Validation**: `docs/operations/SCRIPT_CANONICAL_MAP.md#validation`

## Engineering Rules

### Financial Precision

- Use `Decimal` (never `float`) for all monetary calculations.
- Store monetary amounts as `Int64` scaled integers (cents); rates as basis points.
- Apply `ROUND_HALF_UP` rounding; set `decimal.getcontext().rounding = ROUND_HALF_UP` at entry points.
- See `docs/FINANCIAL_PRECISION_GOVERNANCE.md` for the full policy.

### Data Processing

- Keep processing deterministic and auditable (clear manifests/logging per run).
- Pipeline run ID is derived from SHA256(data_hash|config_hash|code_version|mode) — never wall-clock time.
- Do not log secrets or raw PII.
- Use pipeline `--mode [validate|dry-run|execute]` stages before writing to production targets.

### LLM & Agents

- For LLM-facing workflows, sanitize/redact inputs with `backend/loans_analytics/multi_agent/guardrails.py`.
- Import agents from `backend.loans_analytics.multi_agent` — not the deprecated shim at `backend.src.agents.multi_agent`.
- Multi-agent tests require `HISTORICAL_CONTEXT_MODE=MOCK`; they are excluded from standard CI runs by default.

### Database

- All DB migrations use 14-digit timestamp prefixes (`YYYYMMDDHHmmSS_description.sql`) in lexicographic order.
- Validate migration order with `python3 scripts/maintenance/validate_migration_index.py` before applying.

### Scripts & Tooling

- Prefer existing canonical scripts from `docs/operations/SCRIPT_CANONICAL_MAP.md`; avoid introducing duplicate scripts for the same task.
- Use `make` targets for common workflows; add new commands to `SCRIPT_CANONICAL_MAP.md` first.

## Pipeline Architecture

### Standard Pipeline (Phases 1–4 + 5)

The standard pipeline processes loan data through five sequential phases:

1. **Ingestion** (`ingestion.py`) — Load and validate raw data; coerce object columns to Arrow-safe types.
2. **Transformation** (`transformation.py`) — Normalize columns, apply semantic layer mapping, smart null handling (numeric 3-tier, categorical strict opacity).
3. **Calculation** (`calculation.py`) — Compute KPIs, run segmentation model, run advanced clustering.
4. **Output** (`output.py`) — Export parquet/JSON artifacts, build `audit_metadata.json`, sync to Supabase.
5. **Decision Intelligence** (`decision_phase.py`) — Non-blocking phase; builds marts → features → runs decision agents → produces `DecisionCenterState`.

### Zero-Cost Path (Loan Tape / Control-de-Mora)

Use `backend/src/zero_cost/` when the input is a loan tape or Control-de-Mora CSV (not a standard pipeline input).
Routing is automatic via `backend/src/zero_cost/pipeline_router.py`.
Storage backend: DuckDB + Parquet (no external database required).
Key modules: `loan_tape_loader.py`, `control_mora_adapter.py`, `local_migration_etl.py`, `monthly_snapshot.py`, `storage.py`.

## Multi-Agent Feature Store

The feature store (`backend/loans_analytics/multi_agent/feature_store/`) provides five builder categories:

- `loan_features.py` — Loan-level behavioral features (DPD, payment ratios, mora metrics)
- `customer_features.py` — Customer-level aggregates
- `segment_features.py` — Segment-level metrics (used by segmentation model)
- `campaign_features.py` — Marketing/campaign attribution features
- `treasury_features.py` — Liquidity and treasury features

Features are scenario-aware; the scenario engine (`backend/src/scenario_engine/`) drives base/downside/stress variants.

## Frontend Architecture

The Streamlit app (`frontend/streamlit_app/`) consists of 11 pages:

| Page | Purpose |
|------|---------|
| `01_Executive_Command_Center.py` | C-suite KPI dashboard |
| `02_Risk_Intelligence.py` | PAR/NPL/default risk monitoring |
| `03_Collections_Operations.py` | Collections & recovery tracking |
| `04_Treasury_Liquidity.py` | Liquidity ratios and cash flow |
| `05_Sales_Growth.py` | Disbursement and growth metrics |
| `06_Agent_Insights.py` | Multi-agent analysis results |
| `07_Scenario_Engine.py` | Base/downside/stress scenarios |
| `08_Reports_Center.py` | Exportable reports |
| `09_Data_Quality.py` | Pipeline data quality scores |
| `10_AI_Decision_Center.py` | Phase 5 decision intelligence output |
| `11_Investor_Room.py` | Investor-facing KPI summary |

Data loaders live under `frontend/streamlit_app/` and connect to the KPI engine and Phase 5 outputs.

## API Routes

The FastAPI app at `backend/loans_analytics/apps/analytics/api/main.py` organizes routes by feature domain:

- `routes/agents.py` — Multi-agent analysis endpoints
- `routes/decisions.py` — Decision intelligence endpoints (Phase 5)
- `routes/metrics.py` — KPI / metrics endpoints
- `routes/quality.py` — Data quality check endpoints
- `routes/reports.py` — Reporting and export endpoints
- `routes/scenarios.py` — Scenario engine endpoints

`ROUND_HALF_UP` is set globally via `getcontext().rounding` at app startup.

## Test Organization

```
tests/
├── unit/           # Unit tests (default CI target)
├── integration/    # Integration tests (opt-in; require external services)
├── e2e/            # End-to-end tests (opt-in; require live backend)
├── agents/         # Multi-agent tests (require HISTORICAL_CONTEXT_MODE=MOCK)
├── zero_cost/      # Zero-cost path tests
└── phase{1,2,4,5}/ # Phase-specific regression tests
```

Pytest markers (from `pyproject.toml`):

- `@pytest.mark.integration` — tests requiring external services (Supabase, etc.)
- `@pytest.mark.e2e` — tests requiring a live backend/frontend
- `@pytest.mark.integration_supabase` — Supabase-backed KPI integration tests

Default `make test` runs only unit and integration-safe tests. To run multi-agent tests, invoke the agent test suite directly: `HISTORICAL_CONTEXT_MODE=MOCK pytest tests/agents/`.

Note: default marker filtering (`pytest tests/ -m "not integration and not e2e"`) does not exclude `tests/agents/` by path; agent tests are excluded from default CI runs only if they are explicitly marked or excluded by CI configuration.

Test paths configured in `pyproject.toml`: `backend/loans_analytics/tests` and `tests/`.

## Deprecated Components

| Component | Deprecated Path | Correct Path | Removal Target |
|-----------|----------------|--------------|----------------|
| Multi-agent shim | `backend.src.agents.multi_agent` | `backend.loans_analytics.multi_agent` | Q2 2026 |

The deprecated shim issues a `DeprecationWarning` on import. PR checks (`pr-checks.yml`) actively block new `backend.loans_analytics.multi_agent._llm_agents` imports and module-level `orchestrator` imports.

## CI/CD Workflows in Active Use

- `.github/workflows/tests.yml` — 6 jobs: unit, integration, integration-skipped, multi-agent, e2e (optional), smoke
- `.github/workflows/pr-checks.yml` — python-qa job with 3 blocking rules:
  1. **Block generated artifacts** in PR diff (pycache, pytest cache, JSONL metrics)
  2. **Block legacy backend edits** (freeze `backend/loans_analytics/` except tests & `__init__.py`)
  3. **Block legacy orchestrator imports** (forbid `backend.loans_analytics.multi_agent._llm_agents` imports and module-level `orchestrator` imports)
- `.github/workflows/security-scan.yml` — 5 jobs: CodeQL, Snyk dependency scan, pip-audit/Bandit/Safety, Gitleaks secret scanning, Trivy container scan

## Documentation Sources of Truth

- `README.md`
- `REPO_MAP.md` — Full directory structure and architecture overview
- `docs/SETUP_GUIDE_CONSOLIDATED.md`
- `docs/OPERATIONS.md`
- `docs/GOVERNANCE.md` / `docs/DATA_GOVERNANCE.md`
- `docs/OBSERVABILITY.md`
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md`
- `docs/FINANCIAL_PRECISION_GOVERNANCE.md` — Mandatory financial precision policy
- `docs/security/SECRETS_MANAGEMENT.md` / `docs/API_SECURITY_GUIDE.md`
- `docs/operations/SCRIPT_CANONICAL_MAP.md` — Single source of truth for all CLI commands
- `docs/operations/UNIFIED_WORKFLOW.md` — End-to-end workflow reference

