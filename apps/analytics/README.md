# Abaco Analytics Pipeline API

This service provides a FastAPI-based interface for the Abaco Loans Analytics pipeline. It allows for triggering pipeline runs and retrieving the latest KPI results.

## Getting Started

### Prerequisites
- Python 3.9+
- Dependencies installed: `pip install -r python/requirements.txt`

### Running the API
From the repository root:
```bash
python3 apps/analytics/api/main.py
```
The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### `GET /api/kpis/latest`
Returns the KPI results, quality checks, and metadata from the most recent successful pipeline execution.

### `POST /api/pipeline/trigger`
Triggers a new pipeline run.
- **Payload**: `{ "input_file": "path/to/data.csv" }`
- **Default Input**: `data/archives/abaco_portfolio_calculations.csv`

## Pipeline Orchestration
The pipeline is orchestrated using Prefect and follows a modular 4-phase architecture:
1. **Ingestion**: `src/pipeline/data_ingestion.py`
2. **Transformation**: `src/pipeline/data_transformation.py`
3. **Calculation**: `src/pipeline/kpi_calculation.py`
4. **Output**: `src/pipeline/output.py`

## Configuration
- **Pipeline Settings**: `config/pipeline.yml`
- **Business Rules**: `config/business_rules.yaml`
- **KPI Definitions**: `config/kpis/kpi_definitions.yaml`

## Artifacts
Pipeline outputs are stored in `logs/runs/<run_id>/`. Each run generates a JSON manifest containing the computed metrics and an audit trail.
