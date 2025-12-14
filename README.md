# ABACO Financial Intelligence Platform

## Overview
ABACO is a production-ready financial intelligence platform designed for loan portfolio analytics. It provides a dual-interface approach:
1.  **Streamlit Dashboard:** For interactive exploration of raw loan tapes, growth projections, and payer coverage.
2.  **Data Pipeline:** For automated processing of portfolio snapshots, KPI calculation (PAR30, PAR90, Collection Rate), and audit trailing.

## Repository Structure

### Core Logic (`python/`)
The business logic is consolidated into a clean Python package structure:
*   `analytics.py`: Loan-level metrics (Delinquency, Yield, LTV) used by the Dashboard.
*   `financial_analysis.py`: Advanced financial engineering (DPD buckets, HHI, Weighted Stats).
*   `kpi_engine.py`: Portfolio-level KPI orchestration.
*   `ingestion.py` & `validation.py`: Robust data loading and schema validation.
*   `theme.py`: Centralized design tokens for UI and exports.
*   `kpis/`: Dedicated modules for specific metrics (`par_30.py`, `par_90.py`, `collection_rate.py`, `portfolio_health.py`).

### Applications
*   `streamlit_app.py`: The canonical dashboard entry point.
*   `scripts/run_data_pipeline.py`: Automated pipeline for processing portfolio snapshots.

### Exports
*   `scripts/export_presentation.py`: Generates HTML/Markdown artifacts for presentations.
*   `scripts/export_copilot_slide_payload.py`: Generates JSON payloads for AI slide generation.

## Setup & Usage

### Prerequisites
*   Python 3.9+
*   Dependencies listed in `requirements.txt`

### Installation
```bash
pip install -r requirements.txt
```

### Running the Dashboard
```bash
streamlit run streamlit_app.py
```

### Running the Data Pipeline
```bash
python scripts/run_data_pipeline.py
```
The pipeline reads from `data_samples/abaco_portfolio_sample.csv` by default and outputs metrics to `data/metrics/`.

### Running Tests
```bash
pytest
```

## Key Metrics Definitions
*   **PAR 30 / PAR 90:** Portfolio at Risk > 30/90 days (Sum of DPD Balance / Total Receivable).
*   **Collection Rate:** Cash Available / Total Eligible Receivable.
*   **Portfolio Health:** Composite score (0-10) derived from PAR30 and Collection Rate.