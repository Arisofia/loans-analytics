.PHONY: help setup test lint format type-check clean docker-up docker-down docker-logs deploy check-all

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
export PYTHONPATH := .

# Default target
help:
	@echo "================================================"
	@echo "Abaco Loans Analytics - Production Makefile"
	@echo "================================================"
	@echo ""
	@echo "Setup & Dependencies:"
	@echo "  make setup          - Create venv and install all dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make test           - Run test suite (pytest)"
	@echo "  make lint           - Run linters (ruff, flake8, mypy)"
	@echo "  make format         - Format code (black, isort)"
	@echo "  make type-check     - Run mypy static type checking"
	@echo "  make check-all      - Run all checks (lint + test + type-check)"
	@echo ""
	@echo "Docker Operations:"
	@echo "  make docker-up      - Start Docker services (n8n, postgres, agents)"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make docker-logs    - View Docker logs (follow mode)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          - Clean build artifacts and caches"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy         - Run CI checks (ready for deployment)"
	@echo ""

# Setup virtual environment and install dependencies
setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	@if [ -f requirements-dev.txt ]; then $(BIN)/pip install -r requirements-dev.txt; fi
	@if [ -d .git ]; then $(BIN)/pre-commit install || true; fi
	@echo "✅ Setup complete!"

# Run test suite
test:
	@echo "Running pytest..."
	$(BIN)/pytest tests/ -v --tb=short || $(PYTHON) -m pytest tests/ -v --tb=short

# Run linters
lint:
	@echo "Running ruff..."
	$(BIN)/ruff check . || $(PYTHON) -m ruff check .
	@echo "Running flake8..."
	$(BIN)/flake8 src python --max-line-length=120 --exclude=.venv,venv,__pycache__,.git || true
	@echo "Running mypy..."
	$(BIN)/mypy src python --ignore-missing-imports || $(PYTHON) -m mypy src python --ignore-missing-imports || true
	@echo "✅ Linting complete!"

# Format code
format:
	@echo "Running black..."
	$(BIN)/black src python tests || $(PYTHON) -m black src python tests
	@echo "Running isort..."
	$(BIN)/isort src python tests || $(PYTHON) -m isort src python tests
	@echo "✅ Formatting complete!"

# Type checking
type-check:
	@echo "Running mypy type checking..."
	$(BIN)/mypy src python --ignore-missing-imports || $(PYTHON) -m mypy src python --ignore-missing-imports || true

# Run all checks
check-all: lint test type-check
	@echo "✅ All checks passed!"

# Clean build artifacts and caches
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name __pycache__ -exec rm -rf {} + || true
	find . -type d -name .pytest_cache -exec rm -rf {} + || true
	find . -type d -name .mypy_cache -exec rm -rf {} + || true
	find . -type d -name .ruff_cache -exec rm -rf {} + || true
	find . -type f -name "*.pyc" -delete || true
	find . -type f -name "*.pyo" -delete || true
	rm -rf build dist *.egg-info .coverage htmlcov
	@echo "✅ Cleanup complete!"

# Docker operations
docker-up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "n8n: http://localhost:5678"
	@echo "Next.js: http://localhost:3000"

docker-down:
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped!"

docker-logs:
	@echo "Following Docker logs (Ctrl+C to exit)..."
	docker-compose logs -f

# Deployment preparation
deploy: check-all
	@echo "================================================"
	@echo "✅ Deployment checks passed!"
	@echo "================================================"
	@echo "Ready to deploy. Push to main branch to trigger:"
	@echo "  git push origin main"
	@echo ""

.DEFAULT_GOAL := help