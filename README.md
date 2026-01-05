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

Tracing is automatically enabled when the `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable is set. See [docs/TRACING.md](docs/TRACING.md) for detailed setup instructions.

## Observability

The workspace includes daily observability workflows that monitor:

- Pipeline health and execution metrics
- Agent performance and response times
- Data quality trends and anomalies

See `.github/workflows/opik-observability.yml` for workflow details.

## Required GitHub secrets (CI/CD)

Some workflows require repository secrets to perform deploys and integration tasks. The following is the most important secret for web deployment:

- `AZURE_STATIC_WEB_APPS_API_TOKEN_YELLOW_CLIFF_03015B20F`: token used by the Azure Static Web Apps deploy action for `apps/web`.

Set the secret via GitHub UI (Settings → Secrets and variables → Actions) or via `gh`:

```bash
# Interactive
gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN_YELLOW_CLIFF_03015B20F --repo Abaco-Technol/abaco-loans-analytics

# Non-interactive (from env var SWA_TOKEN)
echo "$SWA_TOKEN" | gh secret set AZURE_STATIC_WEB_APPS_API_TOKEN_YELLOW_CLIFF_03015B20F --repo Abaco-Technol/abaco-loans-analytics
```

Note: repository secrets are **not** available to workflow runs triggered from forked pull requests; use a branch on the main repo or a manual workflow dispatch to run deploys that require secrets.
