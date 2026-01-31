# 🚀 Abaco Loans Analytics - Unified Pipeline Platform

[![Pipeline Status](https://img.shields.io/badge/Pipeline-Operational-brightgreen)]()
[![Structure](https://img.shields.io/badge/Structure-100%25%20Complete-success)]()
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)]()
[![License](https://img.shields.io/badge/License-Proprietary-red)]()

This repository hosts the **Abaco Financial Intelligence Platform**, featuring a unified 4-phase data pipeline architecture with AI-powered multi-agent analytics.

---

## 🌟 Key Features

### **Unified Data Pipeline (v2.0)**

- ✅ **4-Phase Architecture**: Ingestion → Transformation → Calculation → Output
- ✅ **Production Ready**: Complete implementation with 1,875+ lines of pipeline code
- ✅ **Automated Orchestration**: Single entry point with multiple execution modes
- ✅ **Configuration-Driven**: Master config files for pipeline, business rules, and KPIs

### **Multi-Agent AI System**

- **8 Specialized Agents**: Risk, Growth, Ops, Compliance, Collections, Fraud, Pricing, Retention
- **29 Tests Passing**: 18 KPI integration + 11 specialized agent tests
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

```bash
# Verify all pipeline components are in place
python scripts/validate_structure.py

# Expected output: ✅ Repository Status: IMPLEMENTED - COMPLETE
```

### **4. Run the Unified Pipeline**

```bash
# Full pipeline execution with sample data
python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv

# Dry-run (ingestion only)
python scripts/run_data_pipeline.py --mode dry-run

# Validate configuration
python scripts/run_data_pipeline.py --mode validate
```

### **5. Launch Analytics Dashboard**

```bash
streamlit run streamlit_app.py
# Opens http://localhost:8501
```

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

- 8-agent orchestration with fintech expertise
- Historical context management
- Real-time KPI integration
- See [python/multi_agent/README.md](python/multi_agent/README.md)

### **Dashboard** (`streamlit_app/` + `streamlit_app.py`)

- Streamlit dashboard for portfolio, risk, and growth views
- Python-native visualizations with Polars
- Deployed to Azure App Service

### **Documentation** (`docs/`)

- 📚 **[docs/README.md](docs/README.md)** - Complete documentation index (updated Jan 31, 2026)
- 🎯 **Master Documents**: Setup Guide, CTO Audit Report, Operations Master
- 🏗️ Architecture guides and system design
- 🔧 Operations runbooks and deployment guides
- 📋 Planning documents and roadmaps
- 🗄️ **Archive**: 15 historical documents preserved (Phase 1 + Phase 2 consolidation)

**Recent Updates:**

- ✅ Phase 2 Consolidation Complete (Jan 31, 2026)
- ✅ 15 files archived, -2,685 lines from active docs
- ✅ 6 organized archive categories created
- ✅ Single source of truth per category established
- ✅ Zero naming conflicts

For complete structure details: [.repo-structure.json](.repo-structure.json)

---

## 🔧 Configuration

### **Environment Variables**

Create a `.env` file in the project root:

```bash
# Pipeline Configuration
PIPELINE_ENV=development  # or production

# Database (Optional)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Azure (Optional)
AZURE_STORAGE_ACCOUNT=your_storage_account
APPLICATIONINSIGHTS_CONNECTION_STRING=your_connection_string

# AI Agents (Optional)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

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

- **Portfolio Performance** (4): Outstanding balance, loan count, average size, yield
- **Asset Quality** (4): PAR-30, PAR-90, default rate, loss rate
- **Cash Flow** (3): Collections rate, recovery rate, cash on hand
- **Growth** (3): Disbursement volume, new loans, portfolio growth
- **Customer** (3): Active borrowers, repeat rate, lifetime value
- **Operational** (2): Processing time, automation rate

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

```bash
# Basic validation
python scripts/validate_structure.py

# Verbose output with file details
python scripts/validate_structure.py --verbose

# Expected output:
# ✅ Repository Status: IMPLEMENTED - COMPLETE
# Total Expected: 14
# Found: 14
# Missing: 0
# Completion: 100.0%
```

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
python scripts/run_data_pipeline.py --input data/raw/sample_loans.csv --mode validate
```

---

## 📊 Pipeline Usage

### **Command-Line Interface**

```bash
# Full pipeline execution
python scripts/run_data_pipeline.py --input data/raw/loans.csv

# With custom configuration
python scripts/run_data_pipeline.py --config config/custom_pipeline.yml

# Execution modes
python scripts/run_data_pipeline.py --mode full      # All 4 phases
python scripts/run_data_pipeline.py --mode validate  # Stop after transformation
python scripts/run_data_pipeline.py --mode dry-run   # Ingestion only

# Verbose logging
python scripts/run_data_pipeline.py --verbose
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

```bash
# Python validator (recommended)
python scripts/validate_structure.py --verbose

# Deno validator (alternative)
deno run --allow-all main.ts
```

### **Code Quality**

```bash
# Format code
black src/ python/ scripts/

# Lint code
pylint src/ python/ scripts/

# Type checking
mypy src/ python/ scripts/
```

### **Adding New KPIs**

1. Edit `config/kpis/kpi_definitions.yaml`
2. Add formula, unit, description, and thresholds
3. Run pipeline to test: `python scripts/run_data_pipeline.py --mode validate`
4. No code changes required - configuration-driven!

---

## 🛡️ Operational Excellence & Governance

### **Delivery Standards**

- **Auditability**: All KPI outputs must include lineage artifacts (`calculation_manifest.json`) and timestamped run metadata.
- **Security & Compliance**: Maintain secrets in `.env` only; never commit credentials or PII.
- **Data Quality**: Enforce schema validation and anomaly detection before KPI publication.
- **Observability**: Track pipeline run health, latency, and failure rates via Grafana/OTel.

### **Core KPIs for Executive Oversight**

- **Portfolio Health**: PAR-30, PAR-90, default rate, loss rate
- **Growth & Efficiency**: Disbursement volume, portfolio growth, automation rate
- **Cash & Collections**: Collections rate, recovery rate, cash on hand
- **Customer Value**: Active borrowers, repeat rate, LTV

---

## 🤝 Contributing

1. Validate structure: `python scripts/validate_structure.py`
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test: `pytest tests/`
4. Validate again: `python scripts/validate_structure.py`
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
python scripts/run_data_pipeline.py --mode dry-run
```

**Structure validation fails:**

```bash
# Re-run validation with details
python scripts/validate_structure.py --verbose

# Check for missing files
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
  - [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md) - Operations manual
  - [docs/CTO_AUDIT_REPORT.md](docs/CTO_AUDIT_REPORT.md) - Production audit
- 🔍 Review [docs/CODE_QUALITY_GUIDE.md](docs/CODE_QUALITY_GUIDE.md) for standards
- 🗄️ Check [docs/archive/](docs/archive/) for historical context

---

## ✅ Status

- **Pipeline**: ✅ Operational (v2.0)
- **Structure**: ✅ 100% Complete (14/14 components)
- **Tests**: ✅ 232 passing (was 207, fixed 25 scenario tests)
- **Documentation**: ✅ Consolidated & Organized (Phase 2 complete)
- **Production**: ✅ Ready (CTO Audit: B+ rating)

**Last Updated**: January 31, 2026
