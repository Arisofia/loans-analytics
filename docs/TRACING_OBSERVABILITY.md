# Tracing and Observability

This document describes the distributed tracing implementation for the Abaco Loans Analytics platform using Azure Monitor and OpenTelemetry.

## Overview

The platform uses Azure Application Insights with OpenTelemetry instrumentation to provide end-to-end distributed tracing across all Python services, including:

- Data ingestion pipelines
- Analytics calculations
- Streamlit dashboards
- Background jobs and scripts

## Architecture

### Components

1. **Azure Application Insights**: Cloud-based APM solution for collecting and analyzing telemetry
2. **OpenTelemetry**: Vendor-neutral instrumentation framework
3. **Azure Monitor OpenTelemetry Distro**: Microsoft's distribution that automatically configures OpenTelemetry for Azure

### Traced Components

- **Pipeline Orchestrator** (`python/pipeline/orchestrator.py`): Traces all 4 phases of the data pipeline
  - Ingestion phase
  - Transformation phase
  - Calculation phase
  - Output phase
  
- **Streamlit Applications**: Traces user interactions and data processing
  - Main dashboard (`dashboard/app.py`)
  - Analytics app (`streamlit_app.py`)

- **Data Pipeline Scripts** (`scripts/run_data_pipeline.py`): Traces batch execution

## Setup

### Prerequisites

1. Azure Application Insights resource (already provisioned via `infra/azure/main.bicep`)
2. Python packages installed from `requirements.txt`:
   - `azure-monitor-opentelemetry>=1.2.0`
   - `opentelemetry-api>=1.20.0`
   - `opentelemetry-sdk>=1.20.0`
   - `opentelemetry-instrumentation>=0.41b0`

### Configuration

#### Environment Variables

Set the following environment variables in your deployment:

```bash
# Required: Application Insights connection string from Azure Portal
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxx;IngestionEndpoint=https://...

# Optional: Custom service name (defaults to 'abaco-loans-analytics')
AZURE_APPINSIGHTS_SERVICE_NAME=abaco-loans-analytics

# Optional: Environment name (defaults to 'development')
PIPELINE_ENV=production  # or development, staging
PYTHON_ENV=production
```

#### Getting the Connection String

1. Navigate to Azure Portal → Your Application Insights resource
2. Go to "Properties" or "Overview"
3. Copy the "Connection String" value
4. Set it as `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable

### Local Development

For local development, create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env and add your APPLICATIONINSIGHTS_CONNECTION_STRING
```

## Usage

### Automatic Initialization

Tracing is automatically initialized at application startup in:

- `scripts/run_data_pipeline.py` - for batch pipelines
- `streamlit_app.py` - for the main Streamlit app
- `dashboard/app.py` - for the executive dashboard

### Manual Instrumentation

To add custom tracing to your modules:

```python
from python.tracing_setup import get_tracer

tracer = get_tracer(__name__)

def my_function():
    with tracer.start_as_current_span("my-operation"):
        # Your code here
        result = do_something()
        
        # Add custom attributes
        span = trace.get_current_span()
        span.set_attribute("custom.metric", result)
        
    return result
```

### Best Practices

1. **Span Names**: Use descriptive, hierarchical names (e.g., `pipeline.phase.ingestion`)
2. **Attributes**: Add meaningful attributes to spans for better filtering
3. **Error Handling**: Record exceptions in spans using `span.record_exception(exc)`
4. **Performance**: Be mindful of span creation overhead in tight loops

## Monitoring

### View Traces in Azure Portal

1. Navigate to Application Insights resource
2. Go to "Transaction search" or "Performance"
3. View end-to-end transactions and dependencies
4. Use "Application Map" to visualize service dependencies

### Key Metrics to Monitor

- **Pipeline Execution Time**: Duration of each pipeline run
- **Phase Timing**: Time spent in ingestion, transformation, calculation, output
- **Row Counts**: Number of rows processed at each phase
- **Error Rates**: Failed operations and exceptions
- **Anomaly Detection**: Number of anomalies detected in calculations

### Custom Queries (KQL)

```kusto
// Pipeline execution times by environment
dependencies
| where customDimensions.service_name == "abaco-data-pipeline"
| where operation_Name == "pipeline.execute"
| summarize avg(duration), max(duration) by tostring(customDimensions.["deployment.environment"])

// Failed pipeline runs
dependencies
| where customDimensions.["pipeline.status"] == "failed"
| project timestamp, operation_Name, message, customDimensions

// Row processing metrics
dependencies
| where operation_Name startswith "pipeline.phase"
| extend rows = toint(customDimensions.["pipeline.ingestion.rows"])
| where isnotnull(rows)
| summarize total_rows = sum(rows) by bin(timestamp, 1h)
```

## Troubleshooting

### Tracing Not Working

1. **Check Connection String**: Verify `APPLICATIONINSIGHTS_CONNECTION_STRING` is set correctly
2. **Check Logs**: Look for warning messages about tracing initialization
3. **Package Installation**: Ensure all OpenTelemetry packages are installed
4. **Network**: Verify connectivity to Azure endpoints (especially in containers)

### Missing Spans

- Check if tracing was initialized before the operation
- Verify span context is being propagated correctly
- For Azure Functions, review sampling settings in `host.json`; for other Python components (including Streamlit dashboards), review the OpenTelemetry SDK sampling configuration in `python/tracing_setup.py` or related setup code

### Performance Impact

- For Azure Functions, the default sampling rate can be configured in `host.json` (for example, 20 items/second)
- For other Python services using OpenTelemetry, configure sampling (e.g., parent-based or trace-id ratio samplers) via the OpenTelemetry SDK or Azure Monitor OpenTelemetry Distro settings
- Adjust sampling rate based on workload and environment
- Use adaptive or rate-limited sampling strategies for production environments

## Security Considerations

1. **Connection String**: Treat as a secret, do not commit to source control
2. **PII**: Avoid logging sensitive data in span attributes
3. **Compliance**: Ensure telemetry collection complies with data regulations
4. **Data Residency**: Application Insights data is stored in the selected Azure region

## Future Enhancements

- [ ] Add custom metrics for business KPIs
- [ ] Implement distributed tracing across microservices
- [ ] Add correlation with logs and metrics
- [ ] Set up alerts for anomalous patterns
- [ ] Implement SLI/SLO tracking

## References

- [Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable?tabs=python)
- [OpenTelemetry Python Documentation](https://opentelemetry.io/docs/instrumentation/python/)
- [Application Insights Overview](https://learn.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview)
