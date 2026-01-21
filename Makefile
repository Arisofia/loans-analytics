.PHONY: setup test lint clean docker-up docker-down quality quality-check

# Setup environment
setup:
	python3 -m pip install -r requirements.txt
	pre-commit install

# Run all tests
test:
	python3 -m pytest tests/unit tests/test_analytics_metrics.py tests/test_enterprise_analytics_engine.py

# Linting and formatting
lint:
	black .
	isort .
	pylint python apps/analytics/src

# Run comprehensive code quality checks
quality:
	@bash scripts/run_quality_checks.sh

# Alias for quality
quality-check: quality

# Docker Lifecycle
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Analytics API
run-api:
	uvicorn apps.analytics.src.main:app --host 0.0.0.0 --port 8000 --reload

# Prefect Orchestration
prefect-server:
	prefect server start

deploy-flow:
	python3 apps/analytics/src/flows/ingestion_flow.py

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
