# 🚀 Abaco Loans Analytics - Unified Pipeline Platform

[![Pipeline Status](https://img.shields.io/badge/Pipeline-Operational-brightgreen)]()
[![Structure](https://img.shields.io/badge/Structure-100%25%20Complete-success)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

> **✅ Repository Structure: COMPLETE (100%)** - All 14 expected components validated. See [STRUCTURE_COMPLETION_SUMMARY.md](STRUCTURE_COMPLETION_SUMMARY.md) for details.

This repository hosts the **Abaco Financial Intelligence Platform**, featuring a unified 4-phase data pipeline architecture with AI-powered multi-agent analytics.

---

## 🌟 Key Features

### **Unified Data Pipeline (v2.0)**

- ✅ **4-Phase Architecture**: Ingestion → Transformation → Calculation → Output
- ✅ **Production Ready**: Complete implementation with 1,875+ lines of pipeline code
- ✅ **Automated Orchestration**: Single entry point with multiple execution modes
- ✅ **Configuration-Driven**: Master config files for pipeline, business rules, and KPIs

### **Multi-Agent AI System**

- **9 Specialized Agents**: Risk, Growth, Ops, Compliance, Collections, Fraud, Pricing, Retention, Database Design
- **33 Tests Passing**: 18 KPI integration + 15 specialized agent tests
- **7 Pre-built Scenarios**: Multi-step workflows for fintech lending
- **Real-time Validation**: KPI-aware with anomaly detection

### **Analytics & Visualization**

- **Interactive Dashboard**: Streamlit app for pipeline run visualization and KPI monitoring
- **Grafana Monitoring**: Docker-based observability dashboards
- **19 KPI Definitions**: Comprehensive formulas with thresholds and targets

---

## 📋 Prerequisites

### **System Requirements**

- Python 3.9 or higher
- Git
- 4GB RAM minimum (8GB recommended)

### **Optional Tools**

- Deno 2.0+ (for repository validation)
- Azure CLI (for cloud deployment)
- Docker (for Grafana monitoring)

---

## ⚡ Quick Start

### **1. Clone Repository**

```bash
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics
```

### **2. Set Up Python Environment**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### **3. Validate Repository Structure**

Use the canonical command listed in `docs/operations/SCRIPT_CANONICAL_MAP.md` under "Validate structure".

### **4. Run the Unified Pipeline**

```bash
# Full pipeline execution with sample data
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv

# Dry-run (ingestion only)
python scripts/data/run_data_pipeline.py --mode dry-run

# Validate configuration
python scripts/data/run_data_pipeline.py --mode validate
```

### **5. Launch Analytics Dashboard**

```bash
streamlit run streamlit_app.py
# Opens http://localhost:8501
```

### **6. Start Grafana Monitoring (Optional)**

```bash
# Quick start with automated setup
bash scripts/monitoring/auto_start_monitoring.sh

# Or manual setup
export GRAFANA_ADMIN_PASSWORD="your_secure_password"
docker-compose -f docker-compose.monitoring.yml up -d

# Access: http://localhost:3001
```

---

## 📚 Complete User Guides

**New to the platform? Start here:**

### 🎯 **[User Operations Guide](docs/OPERATIONS.md)** ⭐ START HERE

Complete guide answering:

- **Where is Grafana?** How to start monitoring dashboards
- **Where can I see agent feedback?** View AI agent conversations and insights
- **Where to upload files?** Daily data processing workflows
- **Where are predictions?** Current AI capabilities and future ML roadmap
- **How to create users?** Authentication setup for all components

### 🔮 **[ML & Continuous Learning Roadmap](docs/ML_CONTINUOUS_LEARNING_ROADMAP.md)**

Strategic plan for predictive models:

- Default risk prediction
- Customer churn forecasting
- Dynamic pricing optimization
- Fraud detection scoring
- Automated retraining infrastructure

### 🔐 **[Authentication Setup Guide](docs/API_SECURITY_GUIDE.md)**

Secure your platform with:

- Streamlit built-in auth (15 min setup)
- FastAPI OAuth2 + JWT (production-grade)
- Supabase Auth (cloud-ready)
- Role-based access control (RBAC)
- Security best practices

### 📊 **[Grafana Quickstart](docs/OBSERVABILITY.md)**

Monitoring infrastructure:

- Prometheus metrics (520+ Supabase metrics)
- Pre-configured dashboards
- Alert rules for critical events
- Self-hosted or cloud deployment

---

## 📁 Repository Structure

### **Core Pipeline** (`src/pipeline/`)

```
src/pipeline/
├── orchestrator.py      # 4-phase coordinator
├── ingestion.py         # Phase 1: Data collection & validation
├── transformation.py    # Phase 2: Cleaning & normalization
├── calculation.py       # Phase 3: KPI computation
├── output.py           # Phase 4: Results distribution
└── config.py           # Configuration management
```

### **Configuration** (`config/`)

```
config/
├── pipeline.yml              # Master pipeline configuration
├── business_rules.yaml       # Loan status, DPD buckets, risk categories
└── kpis/
    └── kpi_definitions.yaml  # 19 KPI formulas with thresholds
```

### **Scripts** (`scripts/`)

```
scripts/
├── run_data_pipeline.py     # Main CLI entry point
└── validate_structure.py    # Repository structure validator
```

### **Multi-Agent System** (`python/multi_agent/`)

- 9-agent orchestration with fintech expertise
- Historical context management
- Real-time KPI integration
- See [python/multi_agent/README.md](python/multi_agent/README.md)

### **Dashboard** (`streamlit_app/` + `streamlit_app.py`)

- Streamlit dashboard for portfolio, risk, and growth views
- Python-native visualizations with Polars
- Deployed to Azure App Service

### **Documentation** (`docs/`)

- 📚 **[docs/README.md](docs/README.md)** - Active documentation index
- 🎯 **Core Docs**: Setup, Operations, Governance, Observability
- 🏗️ Architecture and design references
- 🔧 Runbooks, deployment, and security guides
- 📋 Planning documents and roadmaps

**Recent Updates:**

- ✅ Canonical command consolidation completed
- ✅ Legacy maintenance scripts removed
- ✅ Active docs aligned to current workflow

For complete structure details: [.repo-structure.json](.repo-structure.json)

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root (do NOT commit this file - it contains secrets):

```bash
# Pipeline Configuration
PIPELINE_ENV=development  # or production

# Database
SUPABASE_URL=<your-url>
SUPABASE_ANON_KEY=<your-key>

# Azure (Optional)
AZURE_STORAGE_ACCOUNT=<your-account>
APPLICATIONINSIGHTS_CONNECTION_STRING=<your-string>

# AI/LLM Providers (Optional - for multi-agent system)
# Set API keys for providers you plan to use in config/config.py
```

⚠️ **Security**: Never commit `.env` files. Store credentials in environment variables or GitHub Secrets.

### **Pipeline Settings** (`config/pipeline.yml`)

- **Ingestion**: Data sources (CSV files, Supabase), validation rules
- **Transformation**: Null handling, type normalization, outlier detection
- **Calculation**: KPI engine settings, time-series aggregations, anomaly detection
- **Output**: Export formats (Parquet/CSV/JSON), database config, dashboard refresh

### **Business Rules** (`config/business_rules.yaml`)

- Loan status mappings (active, delinquent, defaulted, closed)
- DPD buckets (0, 1-30, 31-60, 61-90, 90+ days)
- Risk categories with score thresholds
- Financial constants and operational parameters

### **KPI Definitions** (`config/kpis/kpi_definitions.yaml`)

19 pre-configured KPIs across 6 categories:

#### **KPI Naming Convention**

KPIs follow a **hierarchical naming pattern**: `{category}_{metric_type}_{granularity}`

Examples:

- `portfolio_outstanding_balance_daily` - Portfolio Category, Outstanding Balance metric, Daily granularity
- `assetquality_par30_monthly` - Asset Quality Category, PAR-30 metric, Monthly granularity
- `growth_disbursement_volume_weekly` - Growth Category, Disbursement Volume metric, Weekly granularity

#### **KPI Categories & Definitions**

- **Portfolio Performance** (4): Outstanding balance, loan count, average size, yield
  - Measured daily/weekly for portfolio health tracking
  - Used for trend analysis and forecasting
- **Asset Quality** (4): PAR-30, PAR-90, default rate, loss rate
  - Measured daily for early warning system
  - Critical for risk management and Collections prioritization
- **Cash Flow** (3): Collections rate, recovery rate, cash on hand
  - Measured daily for liquidity management
  - Key for operational planning
- **Growth** (3): Disbursement volume, new loans, portfolio growth
  - Measured weekly/monthly for strategic planning
  - Tracks expansion metrics
- **Customer** (3): Active borrowers, repeat rate, lifetime value
  - Measured monthly for customer analytics
  - Supports retention and acquisition strategies
- **Operational** (2): Processing time, automation rate
  - Measured daily for efficiency monitoring
  - Drives process improvements

---

## 📦 Requirements & Dependencies

### **Core Dependencies** (requirements.txt)

#### **Data Processing**

- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0,<3.0` - Numerical computing
- `pyarrow>=14.0` - Parquet file support
- `polars>=0.20` - Fast dataframe operations
- `pandera[strategies]>=0.20.0` - Data validation

#### **Web & Dashboard**

- `streamlit>=1.33.0` - Interactive dashboard
- `plotly>=6.0.0` - Interactive visualizations
- `altair>=4.0,<7` - Declarative visualizations

#### **Pipeline & Orchestration**

- `prefect>=2.14.0` - Workflow orchestration
- `pydantic>=2.0` - Data validation
- `PyYAML>=6.0` - Configuration parsing

#### **AI & Language Models**

- `openai>=1.3.0` - OpenAI API client
- `anthropic>=0.7.0` - Anthropic API client
- `google-generativeai>=0.3.0` - Google AI
- `langchain>=0.3.13` - LLM framework
- `langchain-openai>=0.2.14` - OpenAI integration
- `langchain-anthropic>=0.3.7` - Anthropic integration

#### **Observability & Tracing**

- `opentelemetry-api>=1.20.0` - Distributed tracing
- `azure-monitor-opentelemetry-exporter>=1.0.0b30` - Azure monitoring
- `opencensus-ext-azure==1.1.15` - Azure Application Insights

#### **Cloud & Database**

- `azure-identity>=1.12.0` - Azure authentication
- `azure-storage-blob>=12.27.0` - Azure Blob Storage
- `psycopg[binary]>=3.1.0` - PostgreSQL client

### **Installation Commands**

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt

# Verify installation
python -c "import pandas, streamlit, pydantic; print('✅ Core dependencies installed')"
```

---

## 🔍 Validation & Testing

### **Repository Structure Validation**

Run the single canonical structure validation command from `docs/operations/SCRIPT_CANONICAL_MAP.md`.

### **Pipeline Testing**

```bash
# Run unit tests
pytest tests/

# Run agent tests
pytest tests/agents/ -v

# Run integration tests
pytest tests/integration/

# Run with coverage
pytest --cov=src --cov=python
```

### **Data Quality Checks**

```bash
# Test data integrity
pytest tests/test_data_integrity.py

# Validate pipeline with sample data
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode validate
```

---

## 🛠️ Developer Tools

### **GitHub Copilot Agents**

Custom AI agents for code optimization and development assistance:

#### **Code Optimizer Agent** (`@code_optimizer`)

Specialized agent for optimizing Python code with fintech-specific expertise:

- **Performance Optimization**: Data processing, database queries, computational efficiency
- **Financial Accuracy**: Enforces Decimal precision for monetary calculations
- **Security & Compliance**: PII protection, audit trails, vulnerability detection
- **Code Quality**: Type hints, structured logging, error handling patterns

**Usage in VS Code Copilot Chat:**

```
@code_optimizer Review this function for performance bottlenecks
@code_optimizer Check if this calculation uses Decimal properly
@code_optimizer Find N+1 query problems in this Supabase code
@code_optimizer Review this code for PII leakage
```

**Documentation:**

- Configuration: [.github/agents/code_optimizer.md](.github/agents/code_optimizer.md)
- Usage Examples: [.github/agents/USAGE_EXAMPLES.md](.github/agents/USAGE_EXAMPLES.md)
- Agent Guide: [.github/agents/README.md](.github/agents/README.md)

**Agent Capabilities:**

- Identifies slow operations in ETL pipeline
- Suggests vectorization with pandas/polars
- Detects float arithmetic in financial calculations
- Reviews for security vulnerabilities
- Validates structured logging patterns
- Checks compliance with fintech requirements

---

## 📊 Pipeline Usage

### **Command-Line Interface**

```bash
# Full pipeline execution
python scripts/data/run_data_pipeline.py --input data/raw/loans.csv

# With custom configuration
python scripts/data/run_data_pipeline.py --config config/custom_pipeline.yml

# Execution modes
python scripts/data/run_data_pipeline.py --mode full      # All 4 phases
python scripts/data/run_data_pipeline.py --mode validate  # Stop after transformation
python scripts/data/run_data_pipeline.py --mode dry-run   # Ingestion only

# Verbose logging
python scripts/data/run_data_pipeline.py --verbose
```

### **Pipeline Output**

Results are stored in timestamped directories:

```
logs/runs/<YYYYMMDD_HHMMSS>/
├── raw_data.parquet           # Phase 1 output
├── clean_data.parquet         # Phase 2 output
├── kpi_results.parquet        # Phase 3 output
├── calculation_manifest.json  # KPI lineage
├── kpis_output.parquet        # Phase 4 output (Parquet)
├── kpis_output.csv            # Phase 4 output (CSV)
├── kpis_output.json           # Phase 4 output (JSON)
└── pipeline_results.json      # Complete execution summary
```

### **Dashboard Usage**

1. Launch dashboard: `streamlit run streamlit_app.py`
2. Select pipeline run from dropdown
3. View metrics, phase results, and KPI calculations
4. Export results to CSV
5. Review technical details and logs

---

## 📚 Documentation

### **Getting Started**

- [QUICK_START.md](QUICK_START.md) - 5-minute quick reference
- [UNIFIED_WORKFLOW.md](UNIFIED_WORKFLOW.md) - Complete workflow guide
- [WORKFLOW_DIAGRAMS.md](WORKFLOW_DIAGRAMS.md) - Visual data flows

### **Implementation Details**

- [PIPELINE_IMPLEMENTATION_SUCCESS.md](PIPELINE_IMPLEMENTATION_SUCCESS.md) - Implementation report
- [OPTIMIZATION_REPORT.md](OPTIMIZATION_REPORT.md) - Performance optimization results (43x speedup)
- [docs/PIPELINE_AUTOMATION_SUMMARY.md](docs/PIPELINE_AUTOMATION_SUMMARY.md) - **NEW**: Automation & performance tracking
- [.repo-structure.json](.repo-structure.json) - Repository blueprint
- [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Documentation navigation

### **Advanced Topics**

- [docs/architecture/](docs/architecture/) - System design and specifications
- [docs/operations/](docs/operations/) - Deployment and runbooks
- [docs/planning/](docs/planning/) - Project plans and roadmaps

---

## 🏗️ Development

### **Project Structure Validation**

Always validate structure before making changes:

Use the canonical command map:
- `docs/operations/SCRIPT_CANONICAL_MAP.md`

### **Code Quality & Maintenance**

For the canonical maintenance command and allowed variants, see:
- `docs/operations/SCRIPT_CANONICAL_MAP.md`
- `docs/REPOSITORY_MAINTENANCE.md`

### **Adding New KPIs**

1. Edit `config/kpis/kpi_definitions.yaml`
2. Add formula, unit, description, and thresholds
3. Run pipeline to test: `python scripts/data/run_data_pipeline.py --mode validate`
4. No code changes required - configuration-driven!

---

## 🛡️ Operational Excellence & Governance

### **Observability Architecture**

The platform uses a **two-layer observability strategy**:

#### **Layer 1: Pipeline Observability** (Grafana + Prometheus)

Monitors data pipeline health, performance, and operational metrics:

- **Metrics Collected**:
  - Pipeline execution time (ingestion, transformation, calculation, output phases)
  - Data quality scores (null percentage, outlier counts, validation failures)
  - KPI calculation results and lineage tracking
  - Phase-by-phase error rates and failure reasons
- **Tools**:
  - **Prometheus**: Scrapes metrics from pipeline runs
  - **Grafana**: Dashboards for portfolio health, daily KPI monitoring, phase performance
  - **Storage**: Time-series database for historical analysis
- **Key Dashboards**:
  - Pipeline Run Dashboard: Success/failure rates, execution times
  - Data Quality Dashboard: Null percentages, anomaly detection
  - KPI Results Dashboard: Daily/weekly KPI values with trend lines
  - Portfolio Health Dashboard: PAR-30, PAR-90, default rate trends

#### **Layer 2: Application Observability** (OpenTelemetry + Azure Monitor)

Traces AI agent decision-making, API calls, and multi-agent interactions:

- **Traces Generated**:
  - Agent request → decision → response flow
  - LLM API call latency and token usage
  - Multi-agent orchestration time (risk → compliance → pricing workflows)
  - Database query performance and connection pool health
- **Tools**:
  - **OpenTelemetry API**: Distributed tracing instrumentation
  - **Azure Monitor Exporter**: Sends traces to Application Insights
  - **Context Propagation**: Maintains trace ID across multi-agent workflows
- **Observability Patterns**:
  - `python/multi_agent/tracing.py`: Cost tracking and latency measurements
  - `python/supabase_pool.py`: Connection pool metrics and query observability
  - `src/pipeline/orchestrator.py`: Phase-level span creation for execution tracking

#### **Monitoring Metrics Reference**

| Metric              | Source                      | Update Frequency | Use Case             |
| ------------------- | --------------------------- | ---------------- | -------------------- |
| KPI Values          | Pipeline Phase 3            | Daily            | Executive dashboards |
| Calculation Lineage | `calculation_manifest.json` | Per run          | Audit trails         |
| Agent Decision Time | OpenTelemetry spans         | Per request      | Performance tuning   |
| Data Quality Score  | Pipeline Phase 2            | Per ingestion    | Quality gates        |
| Pool Health         | `supabase_pool.py` metrics  | Per query        | Capacity planning    |

#### **Compliance & Governance**

- **Auditability**: All KPI outputs include lineage artifacts (`calculation_manifest.json`) and timestamped run metadata.
- **PII Protection**: Sensitive data redacted in logs and traces (see `python/supabase_pool.py` for credential masking).
- **Data Retention**: Pipeline runs archived in `logs/runs/` with configurable retention.
- **Observability SLA**: Metrics available within 5 minutes of pipeline completion.

### **Delivery Standards**

- **Security & Compliance**: Maintain secrets in `.env` only; never commit credentials or PII. Use credential masking in all logging contexts.
- **Data Quality**: Enforce schema validation and anomaly detection before KPI publication.
- **Performance**: Track pipeline run health, latency, and failure rates via Grafana for operational visibility and OpenTelemetry for application tracing.

---

## 🤝 Contributing

1. Validate structure using `docs/operations/SCRIPT_CANONICAL_MAP.md`
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test: `pytest tests/`
4. Validate again using the same canonical command from `docs/operations/SCRIPT_CANONICAL_MAP.md`
5. Commit: `git commit -m "feat: your feature"`
6. Push and create PR

---

## 📄 License

Proprietary - Abaco Financial Services

---

## 🆘 Support & Troubleshooting

### **Common Issues**

**Pipeline fails to start:**

```bash
# Check Python version
python --version  # Should be 3.9+

# Verify dependencies
pip install -r requirements.txt

# Validate configuration
python scripts/data/run_data_pipeline.py --mode dry-run
```

**Structure validation fails:**

Use the canonical validator command from `docs/operations/SCRIPT_CANONICAL_MAP.md`, then verify expected directories exist:

```bash
ls -la src/pipeline/ config/ scripts/
```

**Dashboard won't load:**

```bash
# Check Streamlit installation
streamlit --version

# Run with error details
streamlit run streamlit_app.py --logger.level=debug
```

### **Getting Help**

- 📖 Check [docs/README.md](docs/README.md) - Complete documentation index
- 📚 Master Guides:
  - [docs/SETUP_GUIDE_CONSOLIDATED.md](docs/SETUP_GUIDE_CONSOLIDATED.md) - Complete setup
  - [docs/OPERATIONS.md](docs/OPERATIONS.md) - Operations manual
  - [docs/GOVERNANCE.md](docs/GOVERNANCE.md) - Engineering governance
- 🔍 Review [docs/checklists/REVIEWER_CHECKLIST.md](docs/checklists/REVIEWER_CHECKLIST.md) for review standards

---

## ✅ Status

- **Pipeline**: ✅ Operational (v2.0)
- **Structure**: ✅ 100% Complete (14/14 components)
- **Tests**: ✅ 232 passing (was 207, fixed 25 scenario tests)
- **Documentation**: ✅ Consolidated & Organized (Phase 2 complete)
- **Production**: ✅ Ready (CTO Audit: B+ rating)

**Last Updated**: January 31, 2026
