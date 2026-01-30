.PHONY: help setup format lint type-check test clean
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
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf build dist *.egg-info
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

# NOTE: run-analytics target removed (legacy script deleted in Phase B)
# Pipeline modernization tracked separately
