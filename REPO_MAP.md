# Abaco Loans Analytics - Repository Map

**Last Updated**: 2026-03-21  
**Audit Status**: Production Readiness Remediation Complete

## Directory Structure

### Root Configuration
- `.github/workflows/` — CI/CD pipelines (tests, security, deployment)
- `docker-compose.yml` — Local dev stack definition
- `Dockerfile`, `Dockerfile.dashboard`, `Dockerfile.pipeline` — Container images
- `Makefile` — Development task automation (format, lint, test, deploy)
- `pyproject.toml` — Python project configuration (build, tests, dependencies)
- `.env.example` — Template for environment variables

### Core Application

#### `backend/` — Main application backend
- `src/pipeline/` — **Canonical pipeline** (ingestion, transformation, calculation, output)
  - `orchestrator.py` — Pipeline execution coordinator
  - `ingestion.py` — Data loading phase
  - `transformation.py` — Data cleaning & null handling
  - `calculation.py` — KPI & risk model computation
  - `output.py` — Results export & Supabase sync
- `src/zero_cost/` — **Canonical legacy loan-tape / Control-de-Mora path**
  - Used by zero-cost migration and historical loan-tape workflows.
  - Kept intentionally in parallel with `src/pipeline/` for route-specific compatibility.
  - Covered by `tests/zero_cost/` and routed by `pipeline_router.py`.
- `src/analytics/__init__.py` — Compatibility analytics helpers
  - Utility-only module retained for legacy/test support; not the KPI SSoT owner.

#### `python/` — Python application layer (backend/python/)
- `kpis/` — **KPI engine (SSoT)** — all KPI computation routes through here
  - `engine.py` — KPIEngineV2 (standard & derived KPIs)
  - `ssot_asset_quality.py` — PAR/NPL canonical formulas
  - `formula_engine.py` — SQL-like KPI formula parser
  - `lending_kpis.py` — Lending-specific ratio computations
- `apps/` — Service layer
  - `analytics/api/service.py` — KPI health scoring (SSoT health check paths)
- `models/` — ML/Risk models
  - `default_risk_model.py` — XGBoost default probability (with fail-fast validation)
- `multi_agent/` — LLM-based analysis agents
  - `orchestrator.py` — Multi-agent coordinator
  - `protocol.py` — Agent communication protocol
  - `guardrails.py` — PII redaction & input sanitization

#### `scripts/` — Canonical execution scripts
- `data/run_data_pipeline.py` — **Primary pipeline entrypoint**
  - `--input <csv>` — explicit real data input (no dummy fallback)
  - `--mode [validate|dry-run|execute]` — execution mode
- `data/setup_supabase_tables.py` — DB schema initialization
- `monitoring/` — Operations automation (health checks, alerts)

### Configuration & Governance

#### `config/` — Business rules & parameters
- `pipeline.yml` — Pipeline phase configuration
- `business_rules.yaml` — Lending domain rules
- `business_parameters.yml` — Financial thresholds & targets
- `kpis/` — KPI definitions (per version)
- `rules/` — Alert & validation rules

#### `db/` — Database & data
- `migrations/` — Supabase migration scripts (14-digit timestamps, lexicographic order)
- `sql/` — Raw SQL utilities
- `star_schema/` — Dimensional schema definitions
- `samples/` — (planned) Sample loan data for development

### Documentation

#### `docs/` — **Authority on operations, governance, security**
- `README.md` — Overview of all docs
- `SETUP_GUIDE_CONSOLIDATED.md` — Full setup from zero
- `OPERATIONS.md` — Day-to-day operations & runbooks
- `GOVERNANCE.md` — Data governance, audit trail, SSoT policies
- `SECURITY.md` — Security hardening, secrets management
- `OBSERVABILITY.md` — Monitoring, logging, distributed tracing
- `PRODUCTION_DEPLOYMENT_GUIDE.md` — Production rollout checklist
- `FINANCIAL_PRECISION_GOVERNANCE.md` — Decimal/rounding rules for currency
- `DATA_GOVERNANCE.md` — Data quality, lineage, PII handling
- `KPI_CATALOG.md` — Complete list of all KPIs with definitions
- `KPI_SSOT_REGISTRY.md` — Single Source of Truth for KPI formulas
- `KPI-Operating-Model.md` — *(DocumentationP8)* KPI ownership & update procedures
- `kpi_lineage.md` — *(DocumentationP8)* KPI dependency graph & upstream sources
- `API_SECURITY_GUIDE.md` — API endpoint hardening
- `operations/` — Operational procedures
  - `SCRIPT_CANONICAL_MAP.md` — All production-ready scripts & their purpose
  - `MASTER_DELIVERY_TODO.md` — *(DocumentationP8)* Pre-production checklist

### Testing

#### `tests/` — Comprehensive test suite
- `test_transformation.py` — Null handling, outlier detection
- `test_pipeline_calculation_risk.py` — NPL/PAR calculations
- `test_default_risk_model.py` — Risk model validation
- `test_pipeline_*.py` — Phase-specific integration tests
- `agents/` — Multi-agent testing
- `security/` — Security regression tests
- `zero_cost/` — Zero-cost path tests (validates `backend/src/zero_cost/` canonical legacy flow)

#### `backend/python/tests/` — Unit tests for Python libraries
- `test_kpi_engine.py` — KPIEngineV2 unit tests
- `test_strategic_modules.py` — Strategic reporting tests
- `test_ssot_asset_quality.py` — Asset quality formula tests

### Frontend & Dashboards

#### `frontend/` — User-facing applications
- `streamlit_app/app.py` — Main analytics dashboard
- `components/` — Reusable UI components

### Utilities & Tools

- `tools/` — Miscellaneous scripts (testing, validation)

---

## Key Architectural Patterns

### Single Source of Truth (SSoT)

| Component | Owner File | Purpose |
|-----------|-----------|---------|
| **KPI Formulas** | `backend/python/kpis/ssot_asset_quality.py` | All PAR, NPL, asset quality metrics |
| **Risk Model** | `backend/python/models/default_risk_model.py` | Canonical default probability |
| **Pipeline Phases** | `src/pipeline/` — 4-phase coordinator | All data flows must route through here |
| **Business Rules** | `config/business_rules.yaml` | Audit trail for rule changes |

### Versioning & Governance

- **Code**: Semantic versioning (tags on main branch post-release)
- **Database**: Migrations use 14-digit timestamps, enforced lexicographic order
- **Documentation**: Quarterly audit (GOVERNANCE.md Section 2)
- **KPI Definitions**: Version tracked in config/kpis/ with change log

---

## Critical Files for Production Access

**Read These First:**
1. `SETUP_GUIDE_CONSOLIDATED.md` — Environment setup
2. `OPERATIONS.md` — Daily operations
3. `PRODUCTION_DEPLOYMENT_GUIDE.md` — Release process
4. `docs/operations/MASTER_DELIVERY_TODO.md` — Pre-prod checklist

**Governance & Compliance:**
1. `GOVERNANCE.md` — Data handling, audit trail, SSoT enforcement
2. `SECURITY.md` — Security requirements & hardening
3. `FINANCIAL_PRECISION_GOVERNANCE.md` — Decimal/money calculation rules

**KPI Development:**
1. `KPI_CATALOG.md` — All KPI definitions
2. `KPI_SSOT_REGISTRY.md` — Formula registry
3. `KPI-Operating-Model.md` — Ownership & update procedures

---

## Deprecated Components (Retired 2026-01)

- `backend/src/agents/multi_agent/__init__.py` — Legacy shim (use `backend.python.multi_agent` directly)
  - Deprecation target: Q2 2026
  - Status: Explicit imports with DeprecationWarning added

---

## Contact & Ownership

For ownership questions, see `OWNER_MAP.md` in docs/.
