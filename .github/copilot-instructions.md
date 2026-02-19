# Abaco Loans Analytics - Copilot Instructions

## Mission Context

**Business**: B2B Invoice Factoring for Latin American SMEs - providing liquidity against accounts receivable  
**North Star Metric**: Weekly/Monthly Recurrent TPV (Total Processed Volume) from Active Clients  
**Strategic Phase**: Scaling from $7.4M → $16.3M AUM (Assets Under Management) while maintaining <4% default rate

## Architecture Overview

This is a **production-grade fintech lending analytics platform** with dual architecture:

1. **Unified Data Pipeline** (`src/pipeline/`) - 4-phase ETL: Ingestion → Transformation → Calculation → Output
   - **Phase 1**: Ingestion with schema validation and checksums
   - **Phase 2**: Transformation with PII masking (regulatory compliance)
   - **Phase 3**: KPI calculation (19 metrics across 6 categories)
   - **Phase 4**: Multi-format output (Parquet/CSV/JSON)

2. **Multi-Agent AI System** (`python/multi_agent/`) - 8 specialized LLM agents for lending analytics
   - Risk, Growth, Ops, Compliance, Collections, Fraud, Pricing, Retention
   - 20 specialized scenarios for portfolio analysis
   - KPI-aware with real-time anomaly detection

**Primary tech stack**: Python 3.9+, Pydantic, pandas/polars, Azure Functions, Supabase  
**Observability**: OpenTelemetry, Azure Application Insights, Supabase Metrics API (Prometheus-compatible), custom cost tracking

## Project Structure

```
src/pipeline/           # 4-phase ETL orchestrator (entry: orchestrator.py)
  ├── ingestion.py      # CSV/Supabase ingestion with validation
  ├── transformation.py # PII masking + data normalization
  ├── calculation.py    # KPI engine (19 metrics)
  └── output.py         # Multi-format export + compliance reporting

python/multi_agent/     # AI agents: Risk, Growth, Ops, Compliance, Collections, Fraud, Pricing, Retention
  ├── orchestrator.py   # Agent routing and scenario management
  ├── protocol.py       # Pydantic-typed messages and responses
  ├── guardrails.py     # PII redaction (SSN, email, credit cards)
  └── tracing.py        # OpenTelemetry cost/latency tracking

python/validation.py    # Data validation with required column checks
python/config.py        # Pydantic settings (FinancialGuardrails, RiskParameters, SLASettings)
python/kpis/            # KPI calculation modules (PAR30, PAR90, collection_rate)

config/pipeline.yml     # Pipeline configuration (phases, thresholds, outputs)
config/kpis/            # KPI definitions (formulas, thresholds, targets)
config/business_rules.yaml  # Loan status mappings, DPD buckets, risk categories

.github/workflows/      # CI/CD workflows (compliance, security, deployment)
```

## Critical Developer Commands

```bash
# Environment setup (always use .venv)
source .venv/bin/activate
pip install -r requirements.txt

# Run pipeline (main entry point)
python scripts/data/run_data_pipeline.py --input data/raw/sample_loans.csv
python scripts/data/run_data_pipeline.py --mode validate  # Config check only
python scripts/data/run_data_pipeline.py --mode dry-run   # Ingestion only

# Testing (uses pytest with markers)
make test                    # Or: pytest
pytest -m integration        # Integration tests (require SUPABASE_URL, SUPABASE_ANON_KEY)
pytest python/multi_agent/   # Multi-agent tests only

# Code quality
make format  # black + isort
make lint    # ruff, flake8, pylint
make type-check  # mypy
```

## Key Patterns

### Pipeline Phase Pattern

Each phase in `src/pipeline/` follows the same structure:

```python
class PhaseClass:
    def __init__(self, config: PhaseConfig, ...):
        ...
    def execute(self, input_path=None, run_dir=None) -> Dict[str, Any]:
        # Returns {"status": "success|error", "data": ..., "error": ...}
```

### Multi-Agent Protocol

Agents use typed Pydantic models from `python/multi_agent/protocol.py`:

- `AgentRole` enum: RISK_ANALYST, GROWTH_STRATEGIST, OPS_OPTIMIZER, COMPLIANCE, etc.
- `Message`, `AgentRequest`, `AgentResponse` - all typed with Pydantic
- Orchestrator at `python/multi_agent/orchestrator.py` manages agent routing

### Configuration-Driven Design

- Pipeline config: `config/pipeline.yml` (ingestion sources, transformation rules, output formats)
- Business rules: `python/config.py` via `settings` singleton (financial guardrails, SLAs)
- KPI definitions: `config/kpis/kpi_definitions.yaml` (formulas, thresholds, targets)

## Integration Points

- **Supabase**: Primary database - env vars `SUPABASE_URL`, `SUPABASE_ANON_KEY`
  - Connection pooling with health checks (`python/supabase_pool.py`)
  - Prometheus-compatible Metrics API (~200 database performance metrics)
- **Azure Functions**: Deployment target (see `azure.yaml`, `host.json`, `local.settings.json`)
- **LLM Providers**: OpenAI (default), Anthropic, Gemini - env vars `OPENAI_API_KEY`, etc.
- **Observability**:
  - OpenTelemetry tracing in multi-agent system (`python/multi_agent/tracing.py`)
  - Supabase Metrics API for Prometheus/Grafana (see `docs/SUPABASE_METRICS_INTEGRATION.md`)
  - Load testing framework (`scripts/load_test_supabase.py`, `scripts/test_supabase_connection.py`)

## Code Style

- **Formatting**: black (line-length=100), isort (black profile)
- **Type hints**: Required for all new code; mypy for static checking
- **Logging**: Use `python.logging_config.get_logger(__name__)` - NEVER use print() or f-strings in log calls
- **Validation**: `python/validation.py` for data; Pydantic models for configs
- **Currency**: ALWAYS use `Decimal` for money (NEVER float) - enforced by compliance workflows
- **Error Handling**: Specific exceptions with context; avoid bare except or silent failures

## Branch/Commit Conventions

- Branches: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`, `perf/`
- Commits: Conventional Commits format - `feat(pipeline): add batch processing`

## Critical Governance Rules ("Vibe Solutioning")

⚠️ **Zero Tolerance for Fragility**:

- No syntax errors, infinite loops, or incomplete code
- No unhandled edge cases
- Production-ready from day one

⚠️ **Traceability is King**:

- Every financial decision must be traceable to exact code/data source
- Comprehensive audit trails
- Deterministic computations (Decimal for currency, NO floats)
- Immutable event logs

⚠️ **Code is Law**:

- Compliance embedded, not retrofitted
- Governance enforced by CI/CD (CodeRabbit, SonarQube, Bandit)
- Human review as fallback, automation as primary

## Data Governance Policy

📋 **Golden Rules**:

1. `.md` files document **HOW to get data**, not **WHAT the data is**
2. NEVER hard-code metrics in docs ("Current AUM is $7.4M" ❌)
3. Planning docs in `docs/planning/` MUST include "⚠️ STRATEGIC PLANNING - TARGETS ONLY" header
4. Live data from `fact_loans`, `kpi_timeseries_daily` - query, don't copy
5. Archive old extractions to `archives/` with timestamps

## Testing Notes

- Multi-agent tests mock LLM calls (no API keys needed for unit tests)
- Integration tests marked with `@pytest.mark.integration` require Supabase credentials
- Test coverage requirement: >95% (enforced by SonarQube quality gates)
- Run the canonical structure validation command defined in `docs/operations/SCRIPT_CANONICAL_MAP.md` to verify repository completeness

## Security & Compliance

- PII masking is AUTOMATIC in Phase 2 (transformation) - see `src/compliance.py`
- Compliance reports generated in `data/compliance/<run_id>_compliance.json`
- Secret scanning enforced by 48 CI/CD workflows
- Financial data: ISO 4217 currency codes, idempotency keys for payments
- JWT signature validation required in auth flows

## Strategic Context (CTO-Level)

### Current Technical Maturity

- **Status**: Production-ready (151 passing tests, 95.9% coverage)
- **Architecture**: Dual-track (ETL pipeline + AI agents) intentionally separated
- **CI/CD**: 48 workflows covering compliance, security, deployment, quality gates
- **Recent Hardening**: Jan 2026 audit resolved PII compliance gaps, standardized secret checks

### Known Technical Debt

~~⚠️ **Priority 1 (Critical)** - ✅ RESOLVED (2026-01-30):~~

- ~~KPI calculation silent failures~~ → **FIXED**: Implemented structured logging with full context (see `src/pipeline/calculation.py`)
- ~~Missing traceback in phase errors~~ → **FIXED**: All phases now include full traceback in error responses
- ~~No idempotency in orchestrator~~ → **FIXED**: Content-based run_id with result caching
- ~~No Supabase connection pooling~~ → **FIXED**: Async pool with health checks (see `python/supabase_pool.py`)

**📄 Full details**: See `docs/CRITICAL_DEBT_FIXES_2026.md`

⚠️ **Priority 2 (Important)**:

- Script sprawl in `scripts/`: Several one-off maintenance scripts from legacy migrations
- **Fix**: Move to `archives/maintenance/` and consolidate common patterns

### Architectural Decisions (ADRs)

1. **Separation of `src/agents/` vs `python/multi_agent/`**: INTENTIONAL
   - `src/agents/`: Lightweight infrastructure (LLM providers, monitoring)
   - `python/multi_agent/`: Full domain-specific multi-agent system
   - **Do NOT consolidate** - different purposes, clear separation of concerns

2. **Dashboard Strategy**:
   - `streamlit_app/`: Internal and external data exploration (Python, rapid iteration)
   - Serves as the primary interface for both internal analysis and customer-facing insights

3. **Configuration-Over-Code Philosophy**: Core design principle
   - New KPIs added via YAML, not code changes
   - Business rules externalized to `config/business_rules.yaml`
   - Reduces deployment risk and enables non-technical stakeholders to adjust thresholds

### Financial Domain Knowledge

**Critical Metrics** (always use proper terminology):

- **PAR-30/PAR-90**: Portfolio at Risk (30/90 days past due)
- **DPD**: Days Past Due
- **NPL**: Non-Performing Loans (180+ days)
- **Rotation**: Portfolio turnover rate (target: ≥4.5×)
- **Replines**: Recovery projections by cohort
- **CE 6M**: Collection Efficiency over 6 months (target: ≥96%)

**Risk Guardrails** (hardcoded in `python/config.py`):

- Default rate: <4%
- Top-10 concentration: ≤30%
- Single obligor: ≤4%
- Target APR: 34-40%
- DSCR: ≥1.2×

### Scaling Considerations

**Current Phase**: Growth from $7.4M → $16.3M AUM

- **Bottleneck 1**: KPI calculation latency at scale → Consider Polars adoption for larger datasets
- **Bottleneck 2**: Multi-agent LLM costs → Tracing system tracks this; optimize prompt engineering
- **Bottleneck 3**: Supabase read throughput → Connection pooling already in place; monitor query performance

**Next Technical Milestones**:

1. Real-time KPI streaming (current: batch daily/weekly)
2. Event-driven architecture for agent triggers (current: manual invocation)
3. ML model integration for fraud/pricing agents (current: rule-based + LLM)

### Innovation Opportunities

🚀 **High Impact, Low Effort**:

- Replace silent error handling in KPI processor with structured logging
- Consolidate common patterns in `scripts/` into reusable modules
- Add OpenTelemetry tracing to pipeline phases (currently only in multi-agent)

🚀 **High Impact, Medium Effort**:

- Implement streaming KPI calculation using Polars + Arrow for real-time dashboard updates
- Add agent performance benchmarks to CI/CD (latency, cost per query, accuracy)
- Build agent-to-agent communication protocol for complex scenarios (e.g., Risk → Compliance → Pricing workflow)

🚀 **Transformational (Requires Planning)**:

- Event-driven agent orchestration (Kafka/EventBridge triggers)
- MLOps pipeline for fraud detection model lifecycle
- Multi-tenant architecture for white-label deployment
