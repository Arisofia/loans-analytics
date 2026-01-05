# AI-MultiAgent-Ecosystem – Abaco Analytics

This repository hosts the Abaco Financial Intelligence Platform, including:

- Raw Abaco CSV loan tapes under data/abaco
- Synthetic support tables under data/support
- SQL definitions for core views and KPIs under sql/
- Python/Streamlit dashboard under dashboard/
- Observability and tracing with Azure Monitor OpenTelemetry

## Documentation

See docs/DATA_DICTIONARY.md for table documentation.
See docs/KPI_CATALOG.md for KPI definitions and SQL.
See docs/TRACING.md for observability and tracing setup.

## Quick Start

### Environment Setup

1. Copy `.env.example` to `.env` and configure your environment variables:
   ```bash
   cp .env.example .env
   ```

2. Set your Azure Application Insights connection string in `.env`:
   ```
   APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=...;IngestionEndpoint=..."
   ```

### Running with Tracing

Tracing is automatically enabled when the `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable is set.

See <https://github.com/Abaco-Technol/abaco-loans-analytics/blob/main/docs/TRACING.md> for detailed setup instructions.
## Observability

The workspace includes daily observability workflows that monitor:
- Pipeline health and execution metrics
- Agent performance and response times
- Data quality trends and anomalies

See `.github/workflows/opik-observability.yml` for workflow details.
