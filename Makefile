.PHONY: setup test lint clean docker-up docker-down

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

# Docker Lifecycle
docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

# Cleanup
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
