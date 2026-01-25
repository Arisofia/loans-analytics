# Configuration
PYTHON := python3.12
VENV_DIR := .venv
VENV_BIN := $(VENV_DIR)/bin

# Default target
.PHONY: all
all: install quality

# --- Setup & Installation ---

.PHONY: venv
venv:
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created in $(VENV_DIR)"

.PHONY: install
install: venv
	$(VENV_BIN)/pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements.txt
	$(VENV_BIN)/pip install black flake8 pytest pytest-cov mypy
	@echo "Dependencies installed."

# --- Quality & Testing ---

.PHONY: format
format:
	@echo "Running Black..."
	$(VENV_BIN)/black src tests scripts

.PHONY: lint
lint:
	@echo "Running Flake8..."
	$(VENV_BIN)/flake8 src tests scripts
	@echo "Running MyPy..."
	$(VENV_BIN)/mypy src

.PHONY: test
test:
	@echo "Running Tests..."
	$(VENV_BIN)/pytest tests/ --cov=src --cov-report=term-missing

.PHONY: quality
quality: format lint test
	@echo "✅ Quality check passed!"

# --- Cleanup ---

.PHONY: clean
clean:
	rm -rf $(VENV_DIR)
	find . -type f -name "*.pyc" -delete
audit-code: lint type-check test-cov

	find . -type d -name "__pycache__" -delete
		rm -rf .pytest_cache
		rm -rf .mypy_cache
		rm -rf .coverage

quality: format lint type-check test
	@echo "\n✅ Full quality check complete"

# ------------------------------------------------------------------------------
# Operational targets
# ------------------------------------------------------------------------------

run-pipeline:
	python3.12 scripts/run_data_pipeline.py

run-dashboard:
	streamlit run streamlit_app/app.py

# ------------------------------------------------------------------------------
# Audit / Lineage (Supabase)
# ------------------------------------------------------------------------------

audit-dry-run:
	@echo "Dry run is now integrated into the unified pipeline. Use --dry-run if implemented or check logs."
	python3.12 scripts/run_data_pipeline.py --input data/raw/abaco_portfolio_calculations.csv

audit-write:
	@echo "Audit writing is now integrated into the unified pipeline's output phase."
	python3.12 scripts/run_data_pipeline.py --input data/raw/abaco_portfolio_calculations.csv

check-maturity:
	python3.12 repo_maturity_summary.py

# ------------------------------------------------------------------------------
# Python environment management
# ------------------------------------------------------------------------------

env-clean:
	rm -rf .venv .venv-1

venv:
	$(MAKE) env-clean
	python3.12 -m venv .venv
	@echo "Activate with: source .venv/bin/activate"

venv-install: venv
	@echo "Setting up virtualenv with project dependencies..."
	. .venv/bin/activate && \
	python3.12 -m pip install --upgrade pip && \
	python3.12 -m pip install -r requirements.txt -r dev-requirements.txt

# KPI parity test (dual-engine governance)
test-kpi-parity:
	. .venv/bin/activate && RUN_KPI_PARITY_TESTS=1 python3.12 -m pytest -q tests/test_kpi_parity.py

# Analytics validation and execution
analytics-run:
	. .venv/bin/activate && python3.12 run_complete_analytics.py

analytics-sync:
	. .venv/bin/activate && python3.12 tools/check_kpi_sync.py --print-json

# ------------------------------------------------------------------------------
# VS Code .env warning info
# ------------------------------------------------------------------------------

vscode-envfile-info:
	@echo "To enable .env file loading in VS Code terminals, set 'python.terminal.useEnvFile' to true in your settings."

# ------------------------------------------------------------------------------
# Cleanup
# ------------------------------------------------------------------------------

clean:
	./scripts/cleanup.sh

# ------------------------------------------------------------------------------
# Help
# ------------------------------------------------------------------------------

help:
	@echo "Available targets:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install dev + prod dependencies"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make lint             - Run linters (pylint, flake8, ruff)"
	@echo "  make format           - Auto-format code (black, isort)"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make audit-code       - Lint + type-check + coverage"
	@echo "  make quality          - Full quality check (format + lint + type + test)"
	@echo "  make run-pipeline     - Run the data pipeline"
	@echo "  make run-dashboard    - Run Streamlit dashboard"
	@echo "  make check-maturity   - Check repository maturity"
	@echo "  make env-clean        - Remove local virtualenvs"
	@echo "  make venv             - Create a fresh .venv (no packages)"
	@echo "  make venv-install     - Create .venv and install requirements"
	@echo "  make test-kpi-parity  - Run KPI parity tests (Python vs SQL)"
	@echo "  make analytics-run    - Run complete analytics pipeline"
	@echo "  make analytics-sync   - Validate KPI sync and health"
	@echo "  make audit-dry-run    - Print enriched audit payload (no Supabase write)"
	@echo "  make audit-write      - Write audit/lineage rows to Supabase (requires env vars)"
	@echo "  make clean            - Clean up temporary files"
	@echo "  make help             - Show this help message"
