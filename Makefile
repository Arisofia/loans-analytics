.PHONY: help setup format lint type-check test test-quick test-baseline test-zero-cost e2e clean security-check monitoring-start monitoring-stop monitoring-logs monitoring-health service-status dev api agents kpis repo-map owner-map report-strategic train-scorecard-if-ready zero-cost-up zero-cost-down zero-cost-pipeline zero-cost-db zero-cost-schema etl-local snapshot-build run
PYTHON ?= $(shell \
	for p in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do \
		if command -v $$p >/dev/null 2>&1 && $$p -c "import pytest" >/dev/null 2>&1; then \
			command -v $$p; \
			exit 0; \
		fi; \
	done; \
	command -v python3 || command -v python \
)
VENV := .venv
BIN := $(VENV)/bin
export PYTHONPATH := .:backend:frontend
# Default target
help:
	@echo "Abaco Loans Analytics Automation"
	@echo "--------------------------------"
	@echo "Canonical Entry Points:"
	@echo "make api            - Start Analytics API (hot reload)"
	@echo "make agents         - List available multi-agent scenarios"
	@echo "make kpis           - Run unified KPI pipeline (real data)"
	@echo "make test           - Run default unit/integration-safe test suite"
	@echo "make test-quick     - Run full pytest suite in quiet mode"
	@echo "make test-baseline  - Validate full-suite baseline using pytest JSON report"
	@echo "make e2e            - Run opt-in E2E suite (RUN_E2E=1)"
	@echo "make clean          - Remove caches and build artifacts"
	@echo ""
	@echo "make setup          - Create virtual env and install dependencies"
	@echo "make format         - Format code with black and isort"
	@echo "make lint           - Run pylint, flake8, and ruff"
	@echo "make type-check     - Run mypy static type checking"
	@echo "make train-scorecard-if-ready - Train scorecard when data/raw CSV files exist"
	@echo "make security-check - Run bandit and safety checks"
	@echo "make dev            - Alias of make api"
	@echo "make repo-map       - Open architecture map (docs/README.md)"
	@echo "make owner-map      - Open ownership map (docs/OWNER_MAP.md)"
	@echo ""
	@echo "Monitoring Stack:"
	@echo "make monitoring-start    - Auto-start Prometheus + Grafana + Alertmanager"
	@echo "make monitoring-stop     - Stop monitoring stack"
	@echo "make monitoring-logs     - View monitoring logs"
	@echo "make monitoring-health   - Check monitoring stack health"
setup:
	@if ! command -v "$(PYTHON)" >/dev/null 2>&1; then \
		echo "Python executable '$(PYTHON)' not found. Run with PYTHON=python3.x"; \
		exit 1; \
	fi
	@"$(PYTHON)" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || { \
		echo "Python 3.10+ is required. Selected interpreter: $(PYTHON)"; \
		exit 1; \
	}
	"$(PYTHON)" -m venv --clear $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -r requirements-dev.txt
	@if [ -d .git ]; then \
		if [ -x "$(BIN)/pre-commit" ]; then \
			HOOKS_PATH=$$(git config --get core.hooksPath || true); \
			if [ -n "$$HOOKS_PATH" ]; then \
				echo "Skipping pre-commit hook install: core.hooksPath is set to $$HOOKS_PATH"; \
			elif ! $(BIN)/pre-commit install; then \
				echo "Skipping pre-commit hook install: pre-commit install failed"; \
			fi; \
		else \
			echo "Skipping pre-commit hook install: $(BIN)/pre-commit not found"; \
		fi; \
	fi
format:
	$(BIN)/black .
	$(BIN)/isort .
lint:
	$(BIN)/ruff check .
	$(BIN)/flake8 backend/src backend/python scripts
	$(BIN)/pylint backend/src backend/python scripts
type-check:
	$(BIN)/mypy --check-untyped-defs backend/src
test:
	"$(PYTHON)" -m pytest
test-quick:
	"$(PYTHON)" -m pytest -q
test-baseline:
	@mkdir -p artifacts
	"$(PYTHON)" -m pytest -q --json-report --json-report-file=artifacts/full-suite-report.json
	"$(PYTHON)" scripts/validation/check_full_suite_baseline.py --baseline .github/ci-baselines/full-suite-baseline.json --report artifacts/full-suite-report.json
test-zero-cost:
	"$(PYTHON)" -m pytest tests/zero_cost/ -v
e2e:
	RUN_E2E=1 "$(PYTHON)" -m pytest tests/e2e -m e2e
security-check:
	$(BIN)/bandit -r backend/src backend/python --quiet -x "**/test_*.py,**/tests.py"
	@if $(BIN)/pip list | grep -q safety; then $(BIN)/safety check --continue-on-error; else echo "safety not installed, skipping"; fi
clean:
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .mypy_cache .pytest_cache .ruff_cache htmlcov .coverage

# Monitoring Stack Automation
monitoring-start:
	@bash scripts/monitoring/auto_start_monitoring.sh

monitoring-stop:
	@docker compose --profile monitoring down

monitoring-logs:
	@docker compose --profile monitoring logs -f

monitoring-health:
	@bash scripts/monitoring/health_check_monitoring.sh

# NOTE: run-analytics target removed (legacy script deleted in Phase B)
# Pipeline modernization tracked separately

# Development/API entry point (hot-reload)
api:
	@echo "Starting API server on http://127.0.0.1:8000 with hot-reload..."
	"$(PYTHON)" -m uvicorn python.apps.analytics.api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir backend/python --reload-dir backend/src --reload-dir config
dev: api

# Multi-agent entry point
agents:
	"$(PYTHON)" -m python.multi_agent.cli list-scenarios

# KPI pipeline entry point
kpis:
	"$(PYTHON)" scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv

# Train scorecard model if required raw CSV files are present
train-scorecard-if-ready:
	"$(PYTHON)" scripts/ml/train_scorecard_if_ready.py

# Train default-risk model artifact for /predict/default endpoint
train-risk-model:
	"$(PYTHON)" scripts/ml/train_default_risk_model.py

repo-map:
	@echo "Open docs/README.md"
	@sed -n '1,200p' docs/README.md

owner-map:
	@echo "Open docs/OWNER_MAP.md"
	@sed -n '1,220p' docs/OWNER_MAP.md

# Strategic reporting
report-strategic:
	$(BIN)/python scripts/reporting/generate_strategic_report.py

# =============================================================================
# Docker Stack targets (Unified Compose)
# =============================================================================

## Start the local stack (API + dashboard)
up:
	@echo "Starting local stack (API + Dashboard)..."
	docker compose up --build api dashboard

## Stop the local stack
down:
	docker compose down

## Run ETL pipeline inside the stack (one-shot)
pipeline-run:
	@echo "Running ETL pipeline (Docker)..."
	docker compose --profile pipeline run --rm pipeline

## Start local PostgreSQL (mirrors Supabase schema)
db-up:
	docker compose --profile db up -d db

# Alias for backward compatibility (optional, but good for smooth transition)
zero-cost-up: up
zero-cost-down: down
zero-cost-pipeline: pipeline-run
zero-cost-db: db-up

## Initialise DuckDB star schema locally
zero-cost-schema:
	@echo "Initialising DuckDB star schema..."
	"$(PYTHON)" scripts/data/init_duckdb_schema.py

## Run ETL pipeline locally (no Docker) — zero-cost variant
etl-local:
	@echo "Running local ETL pipeline..."
	"$(PYTHON)" scripts/data/run_data_pipeline.py \
		--input $(or $(INPUT), data/samples/abaco_sample_data_20260202.csv) \
		--mode  $(or $(MODE), full) \
		--verbose

## Build monthly snapshot into DuckDB star schema
snapshot-build:
	@echo "Building monthly snapshot..."
	INPUT=$(or $(INPUT), data/samples/abaco_sample_data_20260202.csv) \
	MONTH=$(or $(MONTH),) \
	"$(PYTHON)" scripts/data/build_snapshot.py

## Run the full zero-cost ETL pipeline (ingest + snapshot)
## Equivalent to what GitHub Actions runs on every push to main
run:
	@echo "Running zero-cost ETL pipeline (ingest + snapshot)..."
	$(MAKE) etl-local
	$(MAKE) zero-cost-schema
	$(MAKE) snapshot-build

