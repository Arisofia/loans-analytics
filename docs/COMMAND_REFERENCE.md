# Abaco Loans Analytics — Command Reference

This document collects common commands and workflows used by the project.

## 🔧 Core Setup Commands

### Initial Setup (First Time Only)

```bash
# Clone and enter the repository
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics

# Copy environment configuration
cp .env.example .env

# Edit .env with your credentials (Azure, Supabase, etc.)
# Required: APPLICATIONINSIGHTS_CONNECTION_STRING
nano .env  # or your preferred editor
```

### Virtual Environment Setup

```bash
# Option 1: Fresh venv with all dependencies
make venv-install

# Option 2: Create venv only (no packages)
make venv

# Option 3: Just install dependencies (if venv already exists)
make install-dev

# Activate the virtual environment
source .venv/bin/activate
```

## 📊 Code Quality Commands (Quality Gate)

### Quick Quality Checks

```bash
# Fast linting (non-blocking, exits with 0)
make lint

# Auto-format all code
make format

# Type checking with mypy
make type-check
```

### Full Quality Audit (Comprehensive)

```bash
# Complete audit: lint + type-check + coverage
make audit-code

# Ultimate quality check: format + lint + type-check + tests
make quality
```

## Testing Commands

```bash
# Run all tests
make test

# Run tests with coverage report (generates HTML)
make test-cov

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Specific Test Suites

```bash
# KPI Parity Tests (Python vs SQL dual-engine validation)
make test-kpi-parity

# Analytics Pipeline Tests (FI-ANALYTICS-002)
pytest tests/fi-analytics/ -v

# Single test file
pytest tests/test_ingestion.py -v

# Single test function
pytest tests/test_ingestion.py::test_basic_ingestion -v

# Tests with keyword filter
pytest -k "quality" -v
```

## 🚀 Data Pipeline Commands

### Run Analytics Pipeline

```bash
# Complete analytics pipeline execution
make analytics-run

# Verify KPI synchronization and health
make analytics-sync

# Dry-run audit (preview, no Supabase write)
make audit-dry-run

# Write audit/lineage to Supabase (requires SUPABASE_* env vars)
make audit-write
```

### Run Data Ingestion

```bash
# Execute the data pipeline
make run-pipeline

# With specific config (if needed)
python3 scripts/run_data_pipeline.py --config custom_config.yml
```

## 📈 Dashboard & Observability

### Run Streamlit Dashboard

```bash
# Launch the Streamlit dashboard
make run-dashboard

# Dashboard opens at: http://localhost:8501
```

### Check Repository Maturity

```bash
# Scan repo for maturity metrics
make check-maturity
```

## 🔍 Development Workflow Commands

### Git Workflow

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, then stage and commit
git add .
git commit -m "feat: your commit message"

# Push to GitHub
git push origin feature/your-feature-name

# Create pull request on GitHub
gh pr create --title "Your PR Title" --body "Description"
```

### Environment Management

```bash
# Clean up old virtualenvs
make env-clean

# Clean up Python cache files
make clean

# Full clean (caches, .coverage, .mypy_cache)
make clean

# VS Code .env file info
make vscode-envfile-info
```

## 📋 Complete Makefile Target Reference

| Command              |                               Purpose |   Time |
| -------------------- | ------------------------------------: | -----: |
| make install         |       Install production dependencies |    ~2m |
| make install-dev     | Install all dependencies (dev + prod) |    ~3m |
| make venv            |      Create clean virtual environment |   ~30s |
| make venv-install    |        Create venv + install all deps |    ~3m |
| make test            |                    Run all unit tests |   ~30s |
| make test-cov        |        Tests + coverage report (HTML) |    ~1m |
| make lint            |                Pylint + Flake8 + Ruff |   ~15s |
| make format          |             Black + isort auto-format |   ~10s |
| make type-check      |                  mypy type validation |   ~10s |
| make audit-code      |          Lint + type-check + coverage |    ~1m |
| make quality         |    Format + lint + type + test (FULL) |    ~2m |
| make run-pipeline    |                 Execute data pipeline | ~5-10m |
| make run-dashboard   |             Start Streamlit dashboard |    ~5s |
| make analytics-run   |                Run complete analytics |   ~15m |
| make analytics-sync  |                   Validate KPI health |    ~2m |
| make test-kpi-parity |               KPI v1 vs v2 validation |    ~3m |
| make audit-dry-run   |              Preview audit (no write) |   ~30s |
| make audit-write     |               Write audit to Supabase |    ~2m |
| make check-maturity  |                    Repo maturity scan |    ~1m |
| make clean           |                Clean cache/temp files |    ~5s |
| make env-clean       |                    Remove virtualenvs |    ~5s |
| make help            |            Show all available targets |    ~1s |

## 🎬 Recommended Development Workflows

### Daily Workflow (Start of Day)

```bash
# Activate environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Run quality check
make quality

# Install any new dependencies
make install-dev
```

### Before Committing

```bash
# Format code
make format

# Run tests
make test

# Type check
make type-check

# If all pass, commit
git add .
git commit -m "feat: your message"
```

### Before Creating PR

```bash
# Full quality audit
make audit-code

# Run complete test suite with coverage
make test-cov

# Check specific failing tests
pytest tests/test_file.py::test_function -v

# View coverage gaps
open htmlcov/index.html
```

## Production Deployment

```bash
# Full quality gate (MUST PASS)
make quality

# Analytics validation
make analytics-sync

# Write audit trail
make audit-write

# Create release commit
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## 🔐 Environment Variables Setup

### Required for Full Operations

```bash
# Azure
export APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=...;IngestionEndpoint=..."

# Supabase (Data Layer)
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_KEY="your-api-key"
export SUPABASE_SERVICE_KEY="your-service-key"

# ...existing code...

# OpenAI/Anthropic
# OPENAI_API_KEY: REPLACE_WITH_OPENAI_API_KEY  # set as environment variable
# ANTHROPIC_API_KEY: REPLACE_WITH_ANTHROPIC_API_KEY  # set as environment variable

# Meta Ads
export META_ACCESS_TOKEN="..."
export META_APP_ID="..."

# ...existing code...

# ...existing code...
```

Store these in `.env` (git-ignored).

## 🐛 Troubleshooting Commands

### Test Execution Issues

```bash
# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run with specific markers
pytest -m analytics

# Generate junit XML for CI
pytest --junit-xml=test-results.xml
```

### Type Checking Issues

```bash
# Run mypy with verbose output
mypy src --show-traceback

# Generate type coverage report
mypy src --html=mypy_report

# Ignore specific errors temporarily
mypy src --ignore-missing-imports
```

### Linting Issues

```bash
# Show pylint details
pylint src --verbose

# Disable specific pylint rules
# Add to .pylintrc or use:
pylint src --disable=C0111,W0212

# Fix some issues automatically
flake8 src --fix
```

## 📦 Dependency Management

```bash
# List installed packages
pip list

# Check for outdated packages
pip list --outdated

# Check for conflicts
pip check

# Generate requirements.txt
pip freeze > requirements.txt
```

### Update Dependencies

```bash
# Update specific package
pip install --upgrade package-name

# Update all packages (CAREFUL)
pip install --upgrade -r requirements.txt

# Add new dependency
pip install new-package
pip freeze | grep new-package >> requirements.txt
```

## 🚨 CI/CD Integration

### Local CI Simulation

```bash
# Run the same checks as GitHub CI
make quality

# Generate coverage for sonarqube
pytest --cov=src --cov-report=xml --cov-report=html

# Validate workflows locally
actionlint .github/workflows/ci.yml
yamllint .github/workflows/ci.yml
```

### Debugging Failed CI

```bash
# Check workflow syntax
actionlint .github/workflows/*.yml

# Run specific test that failed in CI
pytest tests/test_file.py::test_function -vv

# Check Python version compatibility
python3 --version
python3 -m sys
```

## 📚 Additional Resources

| Resource              | Location                      |
| --------------------- | ----------------------------- |
| Architecture          | docs/ARCHITECTURE.md          |
| Engineering Standards | docs/ENGINEERING_STANDARDS.md |
| Operations Runbook    | docs/OPERATIONS.md            |
| Migration Guide       | docs/MIGRATION.md             |
| API Documentation     | docs/API.md                   |
| KPI Catalog           | docs/KPI_CATALOG.md           |
| Data Dictionary       | docs/DATA_DICTIONARY.md       |
| Tracing Guide         | docs/TRACING.md               |

## ⚡ Quick Command Cheatsheet

```bash
# Setup
make venv-install && source .venv/bin/activate

# Code Quality
make format && make quality

# Testing
make test-cov

# Analytics
make analytics-sync && make analytics-run

# Commit & Push
git add . && git commit -m "feat: message" && git push

# Deploy
make audit-write  # Write audit trail before deploy
```
