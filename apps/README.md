# Apps Directory

This directory contains the frontend and backend services for the Abaco Loans Analytics platform.

## Structure

```
apps/
├── web/          # Next.js frontend dashboard
└── analytics/    # FastAPI backend API service
```

## Components

### `apps/web/` - Next.js Dashboard (Frontend)

The Next.js web application provides an interactive dashboard for data exploration and KPI visualization.

**Features:**

- Corporate theme (Black #000000, Grayscale #808080, Purple #4B0082)
- Real-time KPI visualization with Plotly
- Portfolio, Financial, Risk, Growth, Marketing, and Data Quality views
- AI-powered insights and chat interface
- CSV/XLSX upload and processing
- Report export functionality

**Tech Stack:**

- Next.js 14+ with React
- TypeScript
- Tailwind CSS
- Plotly.js for charts
- Axios for API calls

**Development:**

```bash
cd apps/web
npm install
npm run dev
```

**Documentation:** See `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md`

### `apps/analytics/` - FastAPI Backend (API Service)

The FastAPI service provides REST API endpoints for data ingestion, KPI calculation, and AI insights.

**Features:**

- RESTful API for KPI retrieval
- CSV/XLSX data ingestion
- Portfolio, Financial, Risk, Growth, Marketing, Quality analytics endpoints
- AI insights generation (OpenAI/Gemini integration)
- Continuous learning triggers
- OpenAPI documentation

**Tech Stack:**

- FastAPI
- Python 3.10+
- Pydantic for validation
- OpenTelemetry for tracing

**Development:**

```bash
cd apps/analytics
pip install -r requirements.txt
uvicorn apps.analytics.api.main:app --reload --host 0.0.0.0 --port 8000
```

**API Documentation:** See `docs/API_REFERENCE.md` or `/docs` endpoint when running

## Integration

The frontend (`apps/web`) communicates with the backend (`apps/analytics`) via REST API:

- API base URL configured via `NEXT_PUBLIC_API_URL` environment variable
- CORS enabled for allowed origins
- Authentication via JWT tokens

## Deployment

- **Frontend**: Vercel/Netlify (Static Web App)
- **Backend**: Azure Functions, AWS Lambda, or containerized deployment
- **CI/CD**: GitHub Actions workflows in `.github/workflows/`

## Related Documentation

- [Fintech Dashboard Web App Guide](../docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md)
- [API Security Guide](../docs/API_SECURITY_GUIDE.md)
- [Operations Guide](../docs/OPERATIONS.md)
- [Architecture Overview](../docs/architecture.md)

## Status

⚠️ **Note**: This directory structure is defined per `.repo-structure.json` but implementation is pending. The current active dashboard is `streamlit_app.py` in the repository root.

For active production workflow, use:

```bash
# Run Streamlit dashboard (current)
streamlit run streamlit_app.py

# Run data pipeline
python scripts/data/run_data_pipeline.py
```
