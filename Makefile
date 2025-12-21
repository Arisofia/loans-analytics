.PHONY: install test run-pipeline run-dashboard clean check-maturity

install:
	pip install -r requirements.txt

test:
	pytest

run-pipeline:
	python scripts/run_data_pipeline.py

run-dashboard:
	streamlit run streamlit_app.py

check-maturity:
	python repo_maturity_summary.py

clean:
	rm -rf __pycache__ .pytest_cache
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	rm -rf .coverage htmlcov