# FastAPI Analytics Backend

FastAPI backend service for Abaco Loans Analytics platform.

## Overview

This is the REST API service that powers the analytics dashboard. It provides endpoints for data ingestion, KPI calculation, portfolio analysis, and AI-powered insights.

## Features

- **Data Ingestion**: CSV/XLSX upload and processing
- **KPI APIs**: Real-time metrics calculation and retrieval
- **Portfolio Analytics**: Loan performance, collections, rotation
- **Financial Metrics**: Revenue, profitability, APR analysis
- **Risk Assessment**: PAR-30, PAR-90, NPL, default rate tracking
- **Growth Analytics**: Client acquisition, TPV trends, cohort analysis
- **Marketing Insights**: Campaign performance, ROI, conversion rates
- **Data Quality**: Validation, completeness, accuracy monitoring
- **AI Integration**: OpenAI/Gemini for insights generation
- **Continuous Learning**: Model retraining triggers
- **OpenAPI Documentation**: Auto-generated API docs

## Tech Stack

- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Validation**: Pydantic v2
- **Database**: Supabase (PostgreSQL)
- **Caching**: Redis (optional)
- **Tracing**: OpenTelemetry
- **Testing**: pytest
- **Documentation**: OpenAPI/Swagger

## Getting Started

### Prerequisites

- Python 3.10+
- pip or poetry
- Supabase account (for database)
- OpenAI API key (for AI features)

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Development

```bash
# Run development server with auto-reload
uvicorn apps.analytics.api.main:app --reload --host 0.0.0.0 --port 8000

# Run with custom settings
uvicorn apps.analytics.api.main:app --reload --port 8000 --log-level debug

# Run tests
pytest apps/analytics/tests/

# Run with coverage
pytest apps/analytics/tests/ --cov=apps.analytics --cov-report=html
```

The API will be available at:
- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Environment Variables

Create a `.env` file with:

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# AI Providers
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key  # Optional
GOOGLE_API_KEY=your-google-key  # Optional

# Application
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://your-frontend.com

# Observability
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
APPLICATION_INSIGHTS_CONNECTION_STRING=your-appinsights-key
```

## API Endpoints

### Data Ingestion

- `POST /upload` - Upload CSV/XLSX for ingestion
- `GET /upload/status/{job_id}` - Check upload status
- `GET /data/sources` - List available data sources

### KPI Metrics

- `GET /kpis` - Get all KPIs
- `GET /kpis/{metric_name}` - Get specific KPI
- `GET /kpis/timeseries` - Get time-series data
- `GET /kpis/targets` - Get KPI targets and thresholds

### Analytics

- `GET /analytics/portfolio` - Portfolio performance metrics
- `GET /analytics/financial` - Financial analysis
- `GET /analytics/risk` - Risk assessment data
- `GET /analytics/growth` - Growth and acquisition metrics
- `GET /analytics/marketing` - Marketing campaign performance
- `GET /analytics/quality` - Data quality metrics

### AI Features

- `POST /ai/summary` - Generate AI summary of metrics
- `POST /ai/chat` - Conversational AI insights
- `POST /ai/anomaly-detection` - Detect anomalies in data
- `POST /retrain` - Trigger model retraining

### Health & Monitoring

- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `GET /version` - API version information

## Project Structure

```
apps/analytics/
├── api/
│   ├── main.py           # FastAPI application
│   ├── routes/           # API route handlers
│   ├── dependencies.py   # Dependency injection
│   └── middleware.py     # Custom middleware
├── src/
│   ├── enterprise_analytics_engine.py  # Core analytics logic
│   ├── sfv_metrics.py    # SFV-specific metrics
│   └── models/           # Pydantic models
├── tests/
│   ├── test_api.py       # API endpoint tests
│   └── test_analytics.py # Analytics logic tests
├── requirements.txt
└── README.md
```

## API Response Format

All endpoints return JSON in this format:

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-02-02T12:00:00Z",
  "version": "1.0.0"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Missing required field: loan_id",
    "details": { ... }
  },
  "timestamp": "2026-02-02T12:00:00Z"
}
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000` (Next.js dev)
- `https://your-frontend.vercel.app` (production frontend)

Configure via `CORS_ORIGINS` environment variable.

## Security

- **Authentication**: JWT tokens via Bearer authentication
- **Authorization**: Role-based access control (RBAC)
- **Rate Limiting**: 100 requests/minute per IP
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: Parameterized queries only
- **XSS Prevention**: Output sanitization

See `docs/API_SECURITY_GUIDE.md` for details.

## Deployment

### Docker

```bash
# Build image
docker build -t abaco-analytics .

# Run container
docker run -p 8000:8000 --env-file .env abaco-analytics
```

### Azure Functions

```bash
# Deploy to Azure
func azure functionapp publish abaco-analytics-api
```

### AWS Lambda

Use Mangum adapter for AWS Lambda deployment.

## Testing

```bash
# Run all tests
pytest apps/analytics/tests/

# Run with coverage
pytest apps/analytics/tests/ --cov=apps.analytics

# Run specific test file
pytest apps/analytics/tests/test_api.py

# Run with verbose output
pytest apps/analytics/tests/ -v
```

## Monitoring

- **Logs**: Structured JSON logging via `python/logging_config.py`
- **Traces**: OpenTelemetry distributed tracing
- **Metrics**: Prometheus metrics at `/metrics`
- **Health**: Health check at `/health`

## Documentation

- [API Security Guide](../../docs/API_SECURITY_GUIDE.md)
- [Fintech Dashboard Guide](../../docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md)
- [Architecture Overview](../../docs/architecture.md)
- [Operations Guide](../../docs/OPERATIONS.md)

## Status

⚠️ **Implementation Pending**: This directory structure is defined but not yet fully implemented. Current analytics logic is in `src/pipeline/` and `python/`.

## Integration

This backend integrates with:
- **Frontend**: `apps/web/` Next.js dashboard
- **Pipeline**: `src/pipeline/` data processing
- **Multi-Agent**: `python/multi_agent/` AI orchestration
- **Database**: Supabase PostgreSQL
- **Storage**: Azure Blob Storage

## Related Resources

- Frontend Dashboard: `apps/web/`
- Data Pipeline: `src/pipeline/`
- Multi-Agent System: `python/multi_agent/`
- Configuration: `config/pipeline.yml`
