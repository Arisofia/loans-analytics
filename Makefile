.PHONY: help setup format lint type-check test clean docker-up docker-down docker-logs

PYTHON := python3
VENV := .venv
BIN := $(VENV)/bin
export PYTHONPATH := .

# Default target
help:
	@echo "Abaco Loans Analytics - Production Makefile"
	@echo "============================================"
	@echo "Development:"
	@echo "  make setup         - Create virtual env and install dependencies"
	@echo "  make format        - Format code with black and isort"
	@echo "  make lint          - Run ruff, flake8, and pylint"
	@echo "  make type-check    - Run mypy static type checking"
	@echo "  make test          - Run unit tests with pytest"
	@echo "  make clean         - Remove build artifacts and cache"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up     - Start all services (n8n, postgres, python_agents)"
	@echo "  make docker-down   - Stop all services"
	@echo "  make docker-logs   - Show logs from all services"
	@echo "  make docker-clean  - Remove all containers and volumes"

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r requirements.txt
	$(BIN)/pip install -r requirements-dev.txt
	@if [ -d .git ]; then $(BIN)/pre-commit install; fi

format:
	$(BIN)/black .
	$(BIN)/isort .

lint:
	$(BIN)/ruff check .
	$(BIN)/flake8 src tests
	$(BIN)/pylint src tests

type-check:
	$(BIN)/mypy src tests

test:
	$(BIN)/pytest -v

test-coverage:
	$(BIN)/pytest --cov=src --cov-report=html --cov-report=term

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov
	rm -rf build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

docker-clean:
	docker-compose down -v
	docker system prune -f