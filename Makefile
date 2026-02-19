.PHONY: help setup format lint type-check test clean monitoring-start monitoring-stop monitoring-logs monitoring-health service-status dev
PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
export PYTHONPATH := .
# Default target
help:
	@echo "Abaco Loans Analytics Automation"
	@echo "--------------------------------"
	@echo "make setup          - Create virtual env and install dependencies"
	@echo "make format         - Format code with black and isort"
	@echo "make lint           - Run pylint, flake8, and ruff"
	@echo "make type-check     - Run mypy static type checking"
	@echo "make test           - Run unit tests with pytest"
	@echo "make clean          - Run canonical repository maintenance cleanup"
	@echo "make dev            - Start API server with hot-reload (uvicorn)"
	@echo "make service-status - Generate comprehensive service status report"
	@echo ""
	@echo "Monitoring Stack:"
	@echo "make monitoring-start    - Auto-start Prometheus + Grafana + Alertmanager"
	@echo "make monitoring-stop     - Stop monitoring stack"
	@echo "make monitoring-logs     - View monitoring logs"
	@echo "make monitoring-health   - Check monitoring stack health"
setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -r dev-requirements.txt
	if [ -d .git ]; then $(BIN)/pre-commit install; fi
format:
	$(BIN)/black .
	$(BIN)/isort .
lint:
	$(BIN)/ruff check .
	$(BIN)/flake8 src python scripts
	$(BIN)/pylint src python scripts
type-check:
	$(BIN)/mypy src
test:
	$(BIN)/pytest
clean:
	@bash scripts/maintenance/repo_maintenance.sh --mode=standard

# Service Status Report
service-status:
	@if [ -x "$(BIN)/python" ]; then \
		"$(BIN)/python" scripts/maintenance/generate_service_status_report.py; \
	else \
		"$(PYTHON)" scripts/maintenance/generate_service_status_report.py; \
	fi

# Monitoring Stack Automation
monitoring-start:
	@bash scripts/monitoring/auto_start_monitoring.sh

monitoring-stop:
	@docker-compose -f docker-compose.monitoring.yml down

monitoring-logs:
	@docker-compose -f docker-compose.monitoring.yml logs -f

monitoring-health:
	@bash scripts/monitoring/health_check_monitoring.sh

# NOTE: run-analytics target removed (legacy script deleted in Phase B)
# Pipeline modernization tracked separately

# Development Server (hot-reload)
dev:
	@echo "Starting API server on http://127.0.0.1:8000 with hot-reload..."
	$(BIN)/uvicorn python.apps.analytics.api.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir python --reload-dir src --reload-dir config
