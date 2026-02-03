# Abaco Loans Analytics

## Overview

**Abaco Loans Analytics** is a production-grade fintech lending analytics platform designed for B2B invoice factoring targeting Latin American SMEs. The platform provides liquidity against accounts receivable while maintaining sophisticated risk management and portfolio analytics.

### Business Context

- **Mission**: Provide fast, data-driven lending decisions for SME invoice factoring
- **North Star Metric**: Weekly/Monthly Recurrent TPV (Total Processed Volume) from Active Clients
- **Current Scale**: Active growth phase scaling Assets Under Management (AUM)
- **Risk Target**: Maintain <4% default rate across portfolio

---

## Platform Architecture

The platform features a dual-architecture design optimized for both data processing and AI-powered analytics:

### 1. Unified Data Pipeline (`src/pipeline/`)

A 4-phase ETL orchestration system for loan portfolio analytics:

```
Phase 1: Ingestion     → CSV/Supabase data intake with schema validation
Phase 2: Transformation → PII masking + data normalization (regulatory compliance)
Phase 3: Calculation    → 19 KPIs across 6 categories (risk, growth, collections, etc.)
Phase 4: Output         → Multi-format export (Parquet/CSV/JSON) + compliance reports
```

**Entry Point**: `scripts/run_data_pipeline.py`

### 2. Multi-Agent AI System (`python/multi_agent/`)

8 specialized LLM-powered agents for lending intelligence:

- **Risk Analyst**: Portfolio risk assessment and early warning signals
- **Growth Strategist**: Expansion opportunities and market insights
- **Ops Optimizer**: Process efficiency and operational improvements
- **Compliance Officer**: Regulatory adherence and audit trails
- **Collections Manager**: Recovery strategies and payment tracking
- **Fraud Detector**: Anomaly detection and suspicious pattern identification
- **Pricing Analyst**: APR optimization and competitive positioning
- **Retention Specialist**: Client lifetime value and churn prevention

**Key Features**:

- 20+ pre-built lending scenarios
- KPI-aware with real-time anomaly detection
- Guardrails for PII redaction and regulatory compliance
- OpenTelemetry tracing for cost and latency monitoring

---

## Tech Stack

### Core Technologies

- **Language**: Python 3.9+ (with modern type hints support for 3.10+)
- **Data Processing**: pandas/polars for ETL, Decimal for currency calculations
- **Validation**: Pydantic for data models and configuration
- **Database**: Supabase (PostgreSQL) with connection pooling
- **Deployment**: Azure Functions (serverless)

### Observability

- **Logging**: Centralized via `python.logging_config`
- **Tracing**: OpenTelemetry for multi-agent system
- **Metrics**: Azure Application Insights + Supabase Metrics API (Prometheus-compatible)
- **Dashboards**: Streamlit for data exploration, Grafana for monitoring

### AI/LLM Integration

- Primary: OpenAI GPT-4
- Alternatives: Anthropic Claude, Google Gemini
- Cost tracking and prompt optimization built-in

---

## Key Performance Indicators (KPIs)

### Risk Metrics

- **PAR-30/PAR-90**: Portfolio at Risk (30/90 days past due)
- **NPL Rate**: Non-Performing Loans (180+ days overdue)
- **Default Rate**: Target <4%
- **DSCR**: Debt Service Coverage Ratio (target ≥1.2×)

### Growth Metrics

- **AUM**: Assets Under Management
- **TPV**: Total Processed Volume
- **Portfolio Rotation**: Target ≥4.5× annual turnover
- **Client Retention**: Active client recurrence rate

### Collections Metrics

- **DPD**: Days Past Due distribution
- **CE 6M**: Collection Efficiency over 6 months (target ≥96%)
- **Recovery Rate**: Successful recovery on delinquent loans
- **Replines**: Recovery projections by cohort

### Operational Metrics

- **Origination Velocity**: Time from application to disbursement
- **Process Efficiency**: Automation rate and manual intervention frequency
- **Data Quality**: Completeness and accuracy scores

---

## Repository Structure

```
abaco-loans-analytics/
├── src/pipeline/           # 4-phase ETL orchestrator
│   ├── orchestrator.py     # Main pipeline coordinator
│   ├── ingestion.py        # Data intake and validation
│   ├── transformation.py   # PII masking and normalization
│   ├── calculation.py      # KPI engine
│   └── output.py           # Multi-format export
│
├── python/multi_agent/     # AI agent system
│   ├── orchestrator.py     # Agent routing and scenario management
│   ├── protocol.py         # Typed message interfaces (Pydantic)
│   ├── guardrails.py       # PII redaction and compliance
│   └── tracing.py          # OpenTelemetry cost/latency tracking
│
├── python/
│   ├── validation.py       # Data validation rules
│   ├── config.py           # Configuration (guardrails, SLAs)
│   ├── kpis/               # KPI calculation modules
│   └── supabase_pool.py    # Database connection pooling
│
├── config/
│   ├── pipeline.yml        # Pipeline configuration
│   ├── business_rules.yaml # Loan status, DPD buckets, risk categories
│   └── kpis/               # KPI definitions (formulas, thresholds, targets)
│
├── streamlit_app/          # Interactive dashboard
├── scripts/                # Utility scripts and pipeline runner
├── tests/                  # Test suite (>95% coverage)
└── docs/                   # Documentation
    ├── architecture/       # System design and ADRs
    ├── operations/         # Runbooks and deployment guides
    └── planning/           # Project plans and roadmaps
```

---

## Getting Started

### Prerequisites

- Python 3.9+ (3.10+ recommended for modern type hints)
- Git
- 4GB RAM minimum (8GB recommended)
- Optional: Docker, Azure CLI, Deno

### Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Validate structure
python scripts/validate_structure.py

# 3. Run pipeline with sample data
python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv

# 4. Run tests
make test  # or: pytest

# 5. Launch dashboard
streamlit run streamlit_app.py
```

### Essential Commands

```bash
# Code quality
make format      # black + isort
make lint        # ruff, flake8, pylint
make type-check  # mypy

# Testing
pytest                    # All tests
pytest -m integration     # Integration tests (requires Supabase)
pytest python/multi_agent/ # Multi-agent tests only

# Pipeline execution modes
python scripts/run_data_pipeline.py --mode validate  # Config validation only
python scripts/run_data_pipeline.py --mode dry-run   # Ingestion only
python scripts/run_data_pipeline.py --input <path>   # Full execution
```

---

## Configuration

### Environment Variables

Required for production:

- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `OPENAI_API_KEY`: OpenAI API key (for multi-agent system)

Optional:

- `ANTHROPIC_API_KEY`: Anthropic Claude API key
- `GOOGLE_API_KEY`: Google Gemini API key
- `AZURE_APPLICATION_INSIGHTS_CONNECTION_STRING`: Azure monitoring

### Configuration Files

- **Pipeline**: `config/pipeline.yml` - ETL phases, thresholds, output formats
- **Business Rules**: `config/business_rules.yaml` - Loan statuses, DPD buckets
- **KPIs**: `config/kpis/kpi_definitions.yaml` - Formulas, thresholds, targets
- **Python Settings**: `python/config.py` - Financial guardrails, risk parameters

---

## Development Guidelines

### Code Style

- **Formatting**: black (line-length=100), isort (black profile)
- **Type Hints**: Required for all new code (Python 3.10+ native syntax preferred)
- **Logging**: Use `from python.logging_config import get_logger; logger = get_logger(__name__)`
- **Currency**: ALWAYS use `Decimal` for money (NEVER float)
- **Error Handling**: Specific exceptions with structured logging context

### Testing Standards

- **Coverage**: >95% required (enforced by SonarQube)
- **Integration Tests**: Marked with `@pytest.mark.integration`
- **Mocking**: LLM calls mocked in unit tests (no API keys needed)

### Security & Compliance

- **PII Masking**: Automatic in Phase 2 transformation
- **Secret Scanning**: Enforced by comprehensive CI/CD workflows
- **Compliance Reports**: Generated per pipeline run in `data/compliance/`
- **Audit Trails**: All financial decisions traceable to code/data source

### Branch & Commit Conventions

- **Branches**: `feat/`, `fix/`, `chore/`, `docs/`, `refactor/`, `test/`, `perf/`
- **Commits**: Conventional Commits format
  - Example: `feat(pipeline): add batch processing`
  - Example: `fix(kpis): correct PAR-30 calculation for edge cases`

---

## Critical Governance ("Vibe Solutioning")

### Zero Tolerance for Fragility

- No syntax errors, infinite loops, or incomplete code
- No unhandled edge cases
- Production-ready from day one

### Traceability is King

- Every financial decision traceable to exact code/data source
- Comprehensive audit trails with immutable event logs
- Deterministic computations (Decimal for currency, NO floats)

### Code is Law

- Compliance embedded, not retrofitted
- Governance enforced by comprehensive CI/CD workflows (CodeRabbit, SonarQube, Bandit)
- Human review as fallback, automation as primary

---

## Data Governance Policy

**Golden Rules**:

1. `.md` files document **HOW to get data**, not **WHAT the data is**
2. NEVER hard-code metrics in docs (e.g., "Current AUM is $7.4M" ❌)
3. Planning docs in `docs/planning/` MUST include "⚠️ STRATEGIC PLANNING - TARGETS ONLY" header
4. Live data from `fact_loans`, `kpi_timeseries_daily` - query, don't copy
5. Archive old extractions to `archives/` with timestamps

---

## Integration Points

### Supabase (Primary Database)

- Connection pooling with health checks
- Prometheus-compatible Metrics API (~200 database performance metrics)
- Async operations for high throughput

### Azure Functions (Deployment)

- Serverless architecture for pipeline execution
- Configuration in `azure.yaml`, `host.json`, `local.settings.json`
- CI/CD via GitHub Actions workflows

### Observability Stack

- **OpenTelemetry**: Multi-agent tracing (cost, latency)
- **Azure Application Insights**: Application performance monitoring
- **Grafana**: Custom dashboards for loan portfolio metrics
- **Supabase Metrics API**: Database performance monitoring

---

## Known Technical Debt

### Priority 1 (Critical) - ✅ RESOLVED (2026-01-30)

All critical debt items have been resolved:

- ✅ KPI calculation silent failures → Structured logging with full context
- ✅ Missing traceback in phase errors → Full traceback in all error responses
- ✅ No idempotency in orchestrator → Content-based run_id with result caching
- ✅ No Supabase connection pooling → Async pool with health checks

**Full details**: See `docs/CRITICAL_DEBT_FIXES_2026.md`

### Priority 2 (Important)

- **Script sprawl**: Several one-off maintenance scripts in `scripts/` from legacy migrations
- **Recommendation**: Move to `archives/maintenance/` and consolidate common patterns

---

## Architectural Decisions (ADRs)

### 1. Separation of `src/agents/` vs `python/multi_agent/`

**Status**: INTENTIONAL - Do NOT consolidate

- `src/agents/`: Lightweight infrastructure (LLM providers, monitoring)
- `python/multi_agent/`: Full domain-specific multi-agent system
- Different purposes, clear separation of concerns

### 2. Dashboard Strategy

- `streamlit_app/`: Primary interface for both internal analysis and customer-facing insights
- Python-based for rapid iteration and data exploration
- Serves internal teams and external clients

### 3. Configuration-Over-Code Philosophy

- New KPIs added via YAML, not code changes
- Business rules externalized to `config/business_rules.yaml`
- Reduces deployment risk, enables non-technical stakeholder adjustments

---

## Scaling Considerations

**Current Phase**: Active growth phase expanding Assets Under Management (AUM)

> 📊 **Note**: Current AUM and scaling targets should be queried from `fact_loans` and `kpi_timeseries_daily` tables. See Data Governance Policy for details.

### Identified Bottlenecks

1. **KPI Calculation Latency**: Consider Polars adoption for larger datasets
2. **Multi-Agent LLM Costs**: Tracing system tracks this; optimize prompt engineering
3. **Supabase Read Throughput**: Connection pooling in place; monitor query performance

### Next Technical Milestones

1. Real-time KPI streaming (current: batch daily/weekly)
2. Event-driven architecture for agent triggers (current: manual invocation)
3. ML model integration for fraud/pricing agents (current: rule-based + LLM)

---

## Resources

### Documentation

- **README.md**: Comprehensive setup and feature guide
- **REPO_STRUCTURE.md**: Directory organization and module layout
- **CHANGELOG.md**: Version history and updates
- **.github/copilot-instructions.md**: Detailed development guidelines
- **docs/architecture/**: System design and technical specifications
- **docs/operations/**: Runbooks and deployment guides

### External Links

- [GitHub Repository](https://github.com/Arisofia/abaco-loans-analytics)
- Supabase Metrics API: See `docs/SUPABASE_METRICS_INTEGRATION.md`
- Production Readiness: See `PRODUCTION_READINESS_REPORT.md`

### Support & Contact

For questions or issues:

1. Check `docs/operations/` for runbooks
2. Review `CHANGELOG.md` for recent changes
3. Open an issue on GitHub with context and logs

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

**Last Updated**: 2026-02-03  
**Platform Version**: v2.0 (Unified Pipeline Architecture)  
**Status**: Production-Ready ✅
