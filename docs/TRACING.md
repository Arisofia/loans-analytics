# Tracing Configuration Guide

OpenTelemetry (OTEL) distributed tracing captures HTTP requests, database queries, and spans across the Abaco Analytics pipeline. This guide covers setup for development and production environments.

## Architecture

```text
┌─────────────────────────┐
│  Streamlit Dashboard    │
│  (dashboard/app.py)     │
└──────────┬──────────────┘
           │
           ├─→ HTTP Client (httpx/requests) ──→ Instrumented
           ├─→ Database (psycopg/sqlite3)    ──→ Instrumented
           └─→ Custom Spans                  ──→ User-defined
           │
           ↓
┌─────────────────────────────────────┐
│  OpenTelemetry SDK                  │
│  - TracerProvider                   │
│  - Batch Span Processor             │
│  - Auto-instrumentation             │
└──────────┬──────────────────────────┘
           │
           ├─→ Dev: OTLP HTTP to localhost:4318
           └─→ Prod: OTLP HTTP to Azure Monitor (via endpoint)
```

## Development Setup

### 1. Start Local OTEL Collector

For local development, run Jaeger or the OpenTelemetry Collector on port 4318:

#### Option A: Jaeger (all-in-one)

```bash
docker run --rm \
  -p 4318:4318 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest
```

Then access traces at: `http://localhost:16686`

#### Option B: OpenTelemetry Collector

Create `otel-collector-config.yaml`:

```yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
  memory_limiter:
    check_interval: 1s
    limit_mib: 512

exporters:
  logging:
    loglevel: debug
  jaeger:
    endpoint: http://localhost:14250

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch]
      exporters: [logging, jaeger]
```

Run:

```bash
docker run --rm \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 14250:14250 \
  -v $(pwd)/otel-collector-config.yaml:/etc/otel-collector-config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml
```

### 2. Set Environment Variables

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export LOG_LEVEL=DEBUG
```

Or add to `.env`:

```text
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
LOG_LEVEL=DEBUG
```

### 3. Start Dashboard with Tracing

```bash
source .venv/bin/activate
python -m streamlit run dashboard/app.py
```

### 4. View Traces

- **Jaeger UI**: `http://localhost:16686`
- **Search for service**: `abaco-dashboard`
- **Filter by span**: `http.method`, `db.statement`, etc.

## Production Setup (Azure)

### 1. Application Insights Resource

Ensure you have an Application Insights instance in Azure:

```bash
az monitor app-insights component create \
  --app abaco-dashboard-ai \
  --location eastus \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --application-type web
```

Retrieve the **Connection String**:

```bash
az monitor app-insights component show \
  --app abaco-dashboard-ai \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --query connectionString
```

### 2. Set Secrets in App Service

Add to Azure App Service configuration (via Azure CLI or Portal):

```bash
az webapp config appsettings set \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-dashboard \
  --settings \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=...;IngestionEndpoint=..." \
    OTEL_EXPORTER_OTLP_ENDPOINT="https://your-app-insights-endpoint/opentelemetry/v1/traces"
```

Or via **Azure Portal**:

1. Go to **App Service** > **Configuration** > **Application settings**
2. Add new settings:
   - `APPLICATIONINSIGHTS_CONNECTION_STRING` = (from above)
   - `OTEL_EXPORTER_OTLP_ENDPOINT` = `https://<region>.in.applicationinsights.azure.com/opentelemetry/v1/traces`

### 3. Verify in Application Insights

1. Go to Azure Portal > **Application Insights** > **abaco-dashboard-ai**
2. Navigate to **Transaction Search** or **Distributed Traces**
3. Look for `abaco-dashboard` service traces

## Instrumented Modules

The following are auto-instrumented via `opentelemetry-instrumentation-*`:

### HTTP Clients

- **httpx** — async HTTP client
- **requests** — synchronous HTTP client
- **urllib3** — low-level HTTP library

### Database Drivers

- **psycopg2/psycopg** — PostgreSQL (Supabase)
- **sqlite3** — SQLite (local databases)

### Custom Spans

Wrap your own code with spans:

```python
from tracing_setup import get_tracer  # dashboard (dashboard/tracing_setup.py)
# from src.tracing_setup import get_tracer  # pipeline modules

tracer = get_tracer(__name__)

def my_business_logic():
    with tracer.start_as_current_span("process_loan_data") as span:
        span.set_attribute("loan.id", loan_id)
        span.set_attribute("loan.status", "processing")

        # Your code here
        result = process_loan(loan_id)

        span.set_attribute("loan.status", "completed")
        return result
```

## Configuration Reference

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4318` | OTLP exporter endpoint |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | (unset) | Azure App Insights connection |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `OTEL_SDK_DISABLED` | `false` | Disable tracing globally |

### Code Configuration

In `src/tracing_setup.py`:

```python
from src.tracing_setup import init_tracing

# Initialize with custom endpoint
init_tracing(
    service_name="abaco-dashboard",
    service_version="1.0.0",
    otlp_endpoint="https://my-collector.example.com"
)
```

## Troubleshooting

### Spans not appearing

1. **Check OTEL endpoint is reachable**:

   ```bash
   curl -i http://localhost:4318/v1/traces
   # Expected: 400 Bad Request (OTEL expects POST with body)
   ```

2. **Verify tracing initialization**:

   ```bash
   python -c "from src.tracing_setup import init_tracing; init_tracing(); print('OK')"
   ```

3. **Enable debug logging**:

   ```bash
   export OTEL_LOG_LEVEL=DEBUG
   python -m streamlit run dashboard/app.py
   ```

4. **Check firewall/network**:

   ```bash
   # If using Azure, verify App Service can reach Application Insights
   curl -i https://your-app-insights-endpoint/opentelemetry/v1/traces
   ```

### High memory usage

OTEL batches spans to reduce memory. If still high:

```python
# In dashboard/app.py
from opentelemetry.sdk.trace.export import BatchSpanProcessor

processor = BatchSpanProcessor(exporter, max_queue_size=100, max_export_batch_size=50)
```

### Missing instrumentation

If HTTP or database calls aren't traced:

1. Ensure the library is installed:

   ```bash
   pip install opentelemetry-instrumentation-httpx
   ```

2. Verify `enable_auto_instrumentation()` is called in `dashboard/app.py`

3. Check that imports happen **after** instrumentation:

   ```python
   from src.tracing_setup import init_tracing, enable_auto_instrumentation
   init_tracing()
   enable_auto_instrumentation()

   import httpx  # Must be after instrumentation!
   ```

## Examples

### Trace an HTTP call to Cascade API

```python
from src.tracing_setup import get_tracer
import httpx

tracer = get_tracer(__name__)

async def fetch_cascade_data():
    with tracer.start_as_current_span("cascade_fetch") as span:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.cascadedebt.com/data",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            span.set_attribute("http.status_code", response.status_code)
            return response.json()
```

The HTTP call will be automatically instrumented with attributes like:

- `http.method` = GET
- `http.url` = <https://api.cascadedebt.com/data>
- `http.status_code` = 200
- `http.duration_ms` = 145

### Trace a database query

```python
from src.tracing_setup import get_tracer
import psycopg

tracer = get_tracer(__name__)

def fetch_kpi_values():
    with tracer.start_as_current_span("fetch_kpis") as span:
        conn = psycopg.connect(os.getenv("DATABASE_URL"))
        cursor = conn.cursor()

        # This query will be auto-instrumented
        cursor.execute("SELECT * FROM kpi_values WHERE as_of = %s", (today,))
        rows = cursor.fetchall()

        span.set_attribute("db.rows_fetched", len(rows))
        return rows
```

The query will be automatically traced with:

- `db.system` = postgresql
- `db.statement` = SELECT ...
- `db.client.connections.usage` = 1
- `db.duration_ms` = 23

## Best Practices

1. **Use meaningful span names**: `process_loan_data` not `do_stuff`
2. **Add semantic attributes**: `loan.id`, `borrower.name`, etc.
3. **Set status on errors**:

   ```python
   from opentelemetry.trace import Status, StatusCode

   try:
       process_loan()
   except Exception as e:
       span.set_status(Status(StatusCode.ERROR))
       span.record_exception(e)
       raise
   ```

4. **Use context propagation** for distributed traces across services
5. **Sample high-volume traces** in production (by default, all are sampled)

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/src/)
- [Azure Application Insights with OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
- [OTEL Collector Configuration](https://opentelemetry.io/docs/collector/configuration/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
