.PHONY: help setup format lint type-check test clean run-analytics

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
	@echo "make clean          - Remove build artifacts and cache"
	@echo "make run-analytics  - Execute the complete analytics pipeline"

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
	$(BIN)/flake8 src apps/web/src
	$(BIN)/pylint src apps/web/src

type-check:
	$(BIN)/mypy src

test:
	$(BIN)/pytest

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf build dist *.egg-info
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

run-analytics:
	$(BIN)/python run_complete_analytics.py