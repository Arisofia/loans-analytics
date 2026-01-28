# Abaco Loans Analytics - Unified Documentation

**Version**: 2.0  
**Last Updated**: 2026-01-28  
**Status**: Production-Ready Architecture  

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Flow](#architecture-flow)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Technology Stack](#technology-stack)
6. [Project Structure](#project-structure)
7. [Development Guide](#development-guide)
8. [Deployment](#deployment)
9. [Monitoring & Observability](#monitoring--observability)
10. [Security](#security)

---

## System Overview

Abaco Loans Analytics is an enterprise fintech analytics platform powered by multi-agent orchestration. The system processes loan data through a sophisticated pipeline combining:

- **Azure Web Forms** for data collection
- **n8n** for webhook orchestration and data transformation
- **Supabase** (PostgreSQL) for real-time data storage
- **Python Multi-Agent System** for intelligent analytics
- **Next.js Dashboard** for visualization

### Key Features

- ✅ Real-time loan data ingestion
- ✅ Automated risk assessment and analytics
- ✅ Multi-agent intelligent processing
- ✅ KPI tracking and reporting
- ✅ Interactive dashboards
- ✅ OpenTelemetry observability

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   AZURE WEB FORM                            │
│            (User Loan Data Submission)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP POST
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   N8N WEBHOOK                               │
│        (Data Validation & Transformation)                   │
│  • Schema validation                                        │
│  • Data normalization                                       │
│  • Business rules enforcement                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ SQL INSERT
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  SUPABASE DB                                │
│     (PostgreSQL + Real-time Subscriptions)                  │
│  • loans table                                              │
│  • Real-time triggers                                       │
│  • Row-level security (RLS)                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Real-time subscription / Polling
                     ▼
┌─────────────────────────────────────────────────────────────┐
│        PYTHON MULTI-AGENT ORCHESTRATOR                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Protocol Layer (Agent Communication)                 │   │
│  │  • Message passing                                   │   │
│  │  • Task routing                                      │   │
│  │  • Event handling                                    │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ Orchestrator (Router/Dispatcher)                     │   │
│  │  • Task assignment                                   │   │
│  │  • Agent coordination                                │   │
│  │  • Result aggregation                                │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ Base Agent (Abstract base class)                     │   │
│  │  • Common capabilities                               │   │
│  │  • Standard interfaces                               │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ Concrete Agents                                      │   │
│  │  • Analytics Agent (Portfolio analysis)              │   │
│  │  • Risk Agent (Credit scoring, PAR calculation)      │   │
│  │  • Validation Agent (Data quality)                   │   │
│  │  • KPI Agent (Metrics calculation)                   │   │
│  │  • Compliance Agent (Regulatory checks)              │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ Tracing (OpenTelemetry observability)                │   │
│  │  • Span creation                                     │   │
│  │  • Metrics collection                                │   │
│  │  • Distributed tracing                               │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ WRITE BACK
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ANALYTICS RESULTS                              │
│     (Supabase Views + Next.js Dashboard)                    │
│  • SQL views (v_portfolio_risk, v_kpi_metrics)              │
│  • Next.js dashboard (apps/web)                             │
│  • Real-time updates                                        │
│  • Interactive charts                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Data Ingestion Layer

**Azure Web Form**
- Collects loan application data from users
- Basic client-side validation
- Submits to n8n webhook endpoint

**n8n Webhook Orchestrator**
- Receives HTTP POST from Azure Form
- Validates data schema
- Transforms and normalizes data
- Inserts into Supabase database
- Triggers downstream processing

**Location**: n8n workflows (configured via UI)

### 2. Database Layer

**Supabase (PostgreSQL)**
- Central data store
- Real-time subscriptions
- Row-level security (RLS)
- Materialized views for analytics

**Key Tables**:
- `loans` - Core loan data
- `kpi_metrics` - Calculated KPIs
- `risk_scores` - Risk assessments
- `agent_logs` - Processing history

**Location**: `supabase/migrations/`

### 3. Multi-Agent System

**Orchestrator** (`python/multi_agent/orchestrator.py`)
- Routes tasks to appropriate agents
- Manages agent lifecycle
- Aggregates results
- Handles errors and retries

**Base Agent** (`python/multi_agent/base_agent.py`)
- Abstract base class for all agents
- Common capabilities (logging, tracing, DB access)
- Standard interface for task execution

**Protocol** (`python/multi_agent/protocol.py`)
- Message format definitions
- Communication patterns
- Event schemas

**Concrete Agents** (`python/multi_agent/agents.py`)
- Analytics Agent - Portfolio analysis
- Risk Agent - Credit scoring, PAR calculation
- Validation Agent - Data quality checks
- KPI Agent - Metrics calculation
- Compliance Agent - Regulatory checks

**Tracing** (`python/multi_agent/tracing.py`)
- OpenTelemetry integration
- Distributed tracing
- Performance metrics

**Location**: `python/multi_agent/`

### 4. Analytics Layer

**SQL Views** (`sql/`)
- `base_views.sql` - Core analytical views
- `v_portfolio_risk.sql` - Risk analytics
- `v_kpi_metrics.sql` - KPI calculations

**Next.js Dashboard** (`apps/web/`)
- React 19 with Next.js 15
- Supabase client integration
- Interactive charts (Plotly)
- Real-time updates

**Location**: `apps/web/`, `sql/`

---

## Data Flow

### 1. Data Ingestion Flow

```
User Input → Azure Form → n8n Webhook → Supabase INSERT
```

1. User fills out Azure Web Form with loan data
2. Form submits HTTP POST to n8n webhook
3. n8n validates schema and transforms data
4. n8n inserts record into Supabase `loans` table
5. Supabase trigger notifies subscribed agents

### 2. Processing Flow

```
Supabase Trigger → Orchestrator → Agent → Results → Supabase Views
```

1. New loan record triggers real-time subscription
2. Orchestrator receives notification
3. Orchestrator routes to appropriate agents based on task type
4. Agents execute in parallel (analytics, risk, validation)
5. Results written back to Supabase
6. Materialized views updated

### 3. Query Flow

```
Dashboard → Supabase Views → Aggregated Data → Chart Rendering
```

1. Next.js dashboard queries Supabase views
2. Views provide pre-aggregated analytics
3. Dashboard renders interactive charts
4. Real-time subscriptions update UI automatically

---

## Technology Stack

### Backend
- **Python 3.11+** - Multi-agent system
- **PostgreSQL 15** (via Supabase) - Data storage
- **n8n** - Webhook orchestration
- **OpenTelemetry** - Observability

### Frontend
- **Next.js 15** (App Router) - Dashboard framework
- **React 19** - UI library
- **Tailwind CSS 4.0** - Styling
- **Plotly** - Interactive charts

### Infrastructure
- **Docker** - Local development
- **GitHub Actions** - CI/CD
- **Azure** - Production hosting
- **Supabase** - Managed PostgreSQL + Auth

### Development Tools
- **pytest** - Testing
- **ruff, flake8, mypy** - Linting
- **black, isort** - Formatting
- **pnpm** - Node package management

---

## Project Structure

```
.
├── .github/
│   └── workflows/          # CI/CD workflows (6 critical)
│       ├── ci.yml          # Code quality & tests
│       ├── deploy.yml      # Production deployment
│       ├── codeql.yml      # Security scanning
│       ├── docker-ci.yml   # Docker builds
│       ├── lint_and_policy.yml  # Code style
│       └── pr-review.yml   # AI PR review
├── apps/
│   └── web/                # Next.js dashboard
│       ├── src/
│       ├── public/
│       ├── package.json
│       └── next.config.js
├── python/                 # Python codebase
│   ├── multi_agent/        # Multi-agent system
│   │   ├── orchestrator.py
│   │   ├── base_agent.py
│   │   ├── agents.py
│   │   ├── protocol.py
│   │   ├── tracing.py
│   │   └── config.py
│   ├── models/             # Data models
│   ├── kpis/               # KPI calculators
│   └── scripts/            # Utility scripts
├── src/                    # Additional source
│   └── agents/             # Agent utilities
├── supabase/               # Database config
│   ├── migrations/         # Schema migrations
│   └── functions/          # Edge functions
├── sql/                    # Analytics SQL
│   ├── base_views.sql
│   ├── v_portfolio_risk.sql
│   └── v_kpi_metrics.sql
├── tests/                  # Test suite
│   ├── unit/
│   └── integration/
├── scripts/                # Build/deploy scripts
├── docs/                   # Documentation
│   └── UNIFIED.md          # This file
├── docker-compose.yml      # Local environment
├── Dockerfile              # Python agent container
├── pyproject.toml          # Python config
├── requirements.txt        # Python deps
├── package.json            # Root package config
├── pnpm-workspace.yaml     # Monorepo config
├── Makefile                # Common tasks
├── README.md               # Quick start
├── DEPLOYMENT.md           # Deployment guide
└── SECURITY.md             # Security policies
```

---

## Development Guide

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ with pnpm
- Supabase account (for production)

### Local Setup

```bash
# Clone repository
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics

# Create environment file
cp .env.example .env
# Edit .env with your Supabase credentials

# Start all services
docker-compose up

# Verify services
curl http://localhost:5678  # n8n
curl http://localhost:3000  # Next.js dashboard
```

### Development Workflow

```bash
# Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node dependencies (for apps/web)
cd apps/web
pnpm install

# Run tests
make test

# Run linters
make lint

# Format code
make format

# Build Docker images
make docker-up
```

### Testing

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage report
pytest --cov=python --cov-report=html
```

### Common Tasks

```bash
# Check code quality
make lint          # Run all linters
make format        # Format code
make test          # Run tests

# Docker operations
make docker-up     # Start services
make docker-down   # Stop services
make docker-logs   # View logs

# Deployment
make deploy        # Run CI checks + deploy prep
```

---

## Deployment

See **[DEPLOYMENT.md](../DEPLOYMENT.md)** for comprehensive deployment guide.

### Quick Deploy

```bash
# 1. Ensure all tests pass
make test

# 2. Ensure code quality
make lint

# 3. Push to main branch
git push origin main

# 4. GitHub Actions automatically:
#    - Runs CI checks
#    - Builds Docker images
#    - Deploys to Azure
#    - Runs smoke tests
```

### Environment Variables

**Required**:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key
- `NEXT_PUBLIC_SUPABASE_URL` - Public Supabase URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Public anon key

**Optional**:
- `N8N_BASIC_AUTH_USER` - n8n username
- `N8N_BASIC_AUTH_PASSWORD` - n8n password
- `OPENAI_API_KEY` - For AI features
- `LOG_LEVEL` - Logging verbosity (INFO, DEBUG)

---

## Monitoring & Observability

### Logging

**Structured Logging** (Python agents)
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Processing loan", extra={
    "loan_id": loan_id,
    "agent": "risk_agent"
})
```

**Log Locations**:
- Docker: `docker-compose logs -f`
- GitHub Actions: Workflow run logs
- Production: Azure App Insights

### Tracing

**OpenTelemetry** integration in `python/multi_agent/tracing.py`

```python
from python.multi_agent.tracing import trace_span

@trace_span("process_loan")
def process_loan(loan_id):
    # Automatically traced
    pass
```

**Metrics**:
- Request latency
- Agent execution time
- Database query performance
- Error rates

### KPI Dashboard

Query Supabase views for KPIs:
- `v_portfolio_risk` - Portfolio risk metrics
- `v_kpi_metrics` - Business KPIs
- `v_agent_performance` - Agent execution stats

Access via Next.js dashboard at `/kpis`

---

## Security

See **[SECURITY.md](../SECURITY.md)** for comprehensive security policies.

### Key Security Measures

1. **Secrets Management**
   - GitHub Secrets for CI/CD
   - Environment variables (never in code)
   - `.env` files in `.gitignore`

2. **Database Security**
   - Supabase Row-Level Security (RLS)
   - Service role keys for server-side only
   - Anon keys for client-side (limited access)

3. **Authentication**
   - Supabase Auth for dashboard
   - n8n basic auth for webhooks
   - API key rotation policy

4. **Code Scanning**
   - CodeQL (GitHub Actions)
   - Dependency vulnerability scanning
   - Pre-commit hooks

5. **Data Privacy**
   - PII masking in logs
   - Compliance with data regulations
   - Audit trails for data access

---

## Additional Resources

- **README.md** - Quick start guide
- **DEPLOYMENT.md** - Production deployment
- **SECURITY.md** - Security policies
- **CLEANUP_PLAN.md** - Repository cleanup details

### External Documentation

- [Supabase Docs](https://supabase.com/docs)
- [n8n Docs](https://docs.n8n.io/)
- [Next.js Docs](https://nextjs.org/docs)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)

---

## Support

For questions or issues:
1. Check this documentation
2. Search existing GitHub Issues
3. Create new issue with detailed description
4. Contact: [support@abacofinance.com](mailto:support@abacofinance.com)

---

**Last Updated**: 2026-01-28  
**Version**: 2.0  
**Maintained by**: Abaco Analytics Team
