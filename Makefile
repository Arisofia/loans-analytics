.PHONY: install install-dev test test-cov run-pipeline run-dashboard clean check-maturity \
        lint format type-check audit-code quality

# Installation targets
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r dev-requirements.txt

# Testing targets
test:
	pytest

test-cov:
	pytest --cov=python --cov-report=html --cov-report=term

# Code quality targets
lint:
	@echo "Running pylint..."
	pylint python --exit-zero
	@echo "\nRunning flake8..."
	flake8 python --exit-zero
	@echo "\nRunning ruff check..."
	ruff check python --exit-zero

format:
	@echo "Running black..."
	black python
	@echo "\nRunning isort..."
	isort python

type-check:
	@echo "Running mypy..."
	mypy python --ignore-missing-imports

audit-code: lint type-check test-cov
	@echo "\n✅ Code audit complete: linting, type checking, and tests"

quality: format lint type-check test
	@echo "\n✅ Full quality check complete"

# Operational targets
run-pipeline:
	python scripts/run_data_pipeline.py

run-dashboard:
	streamlit run streamlit_app.py

check-maturity:
	python repo_maturity_summary.py

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	rm -rf .coverage htmlcov
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

help:
	@echo "Available targets:"
	@echo "  make install          - Install production dependencies"
	@echo "  make install-dev      - Install development dependencies"
	@echo "  make test             - Run tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make lint             - Run linters (pylint, flake8, ruff)"
	@echo "  make format           - Auto-format code (black, isort)"
	@echo "  make type-check       - Run mypy type checking"
	@echo "  make audit-code       - Run linting, type checking, and coverage"
	@echo "  make quality          - Full quality check (format, lint, type, test)"
	@echo "  make run-pipeline     - Run the data pipeline"
	@echo "  make run-dashboard    - Run Streamlit dashboard"
	@echo "  make check-maturity   - Check repository maturity"
	@echo "  make clean            - Clean up temporary files"
	@echo "  make help             - Show this help message"
