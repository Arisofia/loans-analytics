# ABACO LOANS ANALYTICS - OPERATIONS RUNBOOK

**Status**: 🟢 ACTIVE  
**Version**: 1.0  
**Last Updated**: 2026-01-03

---

## 1. System Overview

The ABACO Financial Intelligence Platform provides automated KPI calculation, portfolio monitoring, and executive reporting for loan portfolios. The system integrates data from Cascade API, HubSpot, and manual Looker exports.

### Core Components
- **Analytics Pipeline**: Python-based engine for data ingestion, transformation, and KPI calculation.
- **Executive Dashboard**: Streamlit-based visualization platform.
- **Observability Layer**: Azure Monitor (Application Insights) and Jaeger for distributed tracing.

---

## 2. Environment Setup

### Prerequisites
- Python 3.11 or 3.12
- Docker (for local observability)
- Azure CLI (for cloud management)

### Initial Installation
```bash
# Clone the repository and install dependencies
make install-dev
```

### Configuration
1. Copy `.env.example` to `.env`.
2. Configure mandatory variables:
   - `APPLICATIONINSIGHTS_CONNECTION_STRING`: For Azure tracing.
   - `HUBSPOT_API_KEY`: For customer data integration.
   - `DATABASE_URL`: Connection string for the analytical database (PostgreSQL/Supabase).

---

## 3. Data Pipeline Operations

### Running Complete Analytics
To calculate all standard and extended KPIs from the latest data:
```bash
make analytics-run
```
**Outputs**:
- `exports/complete_kpi_dashboard.json`: Consolidated KPI results.
- `exports/analytics_facts.csv`: Data feed for Figma dashboards.
- `exports/quarterly_scorecard.csv`: Executive performance summary.

### Generating Executive Reports
To generate a standalone HTML executive summary:
```bash
python3 generate_executive_report.py
```
**Output**: `executive_report.html`

### Manual Data Ingestion
Place CSV exports in the following directories for automated pick-up:
- `data/abaco/`: Core loan tapes and payment records.
- `data/raw/looker_exports/`: Direct exports from Looker.

---

## 4. Data Quality & Reporting

### Automated Quality Audits
The pipeline now includes a Phase 5 **DataQualityReporter** that evaluates datasets against required schemas, numeric types, and null-value thresholds.

**Audit Categories**:
- **Critical**: Missing required columns (Score deduction: 20 pts).
- **Warning**: Type mismatches or invalid dates (Score deduction: 10 pts).
- **Info**: Null values in key columns (Score deduction: 2 pts).

### Generating Quality Reports
Audits are automatically run during ingestion. To manually generate a report for a specific dataframe:
```python
from pipeline.validation import DataQualityReporter
reporter = DataQualityReporter(df)
report = reporter.run_audit(required_columns=["loan_id", "total_receivable_usd"])
print(report.to_markdown())
```

---

## 5. Dashboard Operations

### Running Locally
```bash
make run-dashboard
```
The dashboard will be available at `http://localhost:8501`.

### Production Deployment
The dashboard is hosted on Azure App Service.
- **Service Name**: `abaco-analytics-dashboard`
- **Deployment**: Automatic via GitHub Actions on push to `main`.
- **Startup Command**: `bash startup.sh`

---

## 5. Observability & Monitoring

### Local Tracing (Jaeger)
To view distributed traces locally:
1. Start Jaeger:
   ```bash
   docker run --rm -p 4318:4318 -p 16686:16686 jaegertracing/all-in-one:latest
   ```
2. Set environment variable: `export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318`
3. Access UI at `http://localhost:16686`.

### Cloud Tracing (Azure)
Traces are automatically sent to Application Insights if `APPLICATIONINSIGHTS_CONNECTION_STRING` is set.
- **Portal**: Azure Portal > Application Insights > abaco-dashboard-ai.
- **Key Metrics**: Pipeline execution time, API latency, and error rates.

---

## 6. Maintenance & Quality Control

### Code Quality Audit
Before submitting changes, run the full quality suite:
```bash
make quality
```
This runs:
1. **Formatting**: Black + isort.
2. **Linting**: Pylint + Flake8 + Ruff.
3. **Type Checking**: Mypy.
4. **Testing**: Pytest.

### Cleanup
To remove temporary files and caches:
```bash
make clean
```

---

## 7. Troubleshooting

| Issue | Resolution |
|-------|------------|
| Missing KPIs | Verify `config/pipeline.yml` mappings and source CSV columns. |
| Dashboard Offline | Check Azure App Service health at `/?page=health`. |
| Tracing Errors | Verify `OTEL_EXPORTER_OTLP_ENDPOINT` connectivity. |
| Ingestion Failures | Check `pipeline/validation.py` for schema enforcement rules. |

---
**AI-driven improvements based on Vibe Solutioning standards**


**Dependency note:** If you use `langchain` and its related subpackages in downstream projects, prefer constraining `langchain-core` to a known-compatible range (for example `langchain-core>=0.3.34,<0.4.0`) in that project's requirements to avoid cross-repo dependency resolution conflicts.
