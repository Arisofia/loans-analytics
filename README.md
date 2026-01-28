# Abaco Loans Analytics

Enterprise fintech analytics system powered by multi-agent orchestration.

[![CI](https://github.com/Arisofia/abaco-loans-analytics/workflows/ci/badge.svg)](https://github.com/Arisofia/abaco-loans-analytics/actions)
[![Security](https://github.com/Arisofia/abaco-loans-analytics/workflows/codeql/badge.svg)](https://github.com/Arisofia/abaco-loans-analytics/security)
[![Deploy](https://github.com/Arisofia/abaco-loans-analytics/workflows/deploy/badge.svg)](https://github.com/Arisofia/abaco-loans-analytics/actions)

---

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   AZURE WEB FORM                            │
│            (User Loan Data Submission)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   N8N WEBHOOK                               │
│        (Data Validation & Transformation)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                  SUPABASE DB                                │
│     (PostgreSQL + Real-time Subscriptions)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│        PYTHON MULTI-AGENT ORCHESTRATOR                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ • Protocol (Agent Communication)                     │   │
│  │ • Orchestrator (Router/Dispatcher)                   │   │
│  │ • Base Agent (Abstract base class)                   │   │
│  │ • Concrete Agents (Analytics, Risk, Validation...)  │   │
│  │ • Tracing (OpenTelemetry observability)             │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ANALYTICS RESULTS                              │
│     (Queries on Supabase Views + Dashboards)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+ with pnpm
- Supabase account

### Setup

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

### Development

```bash
# Python setup
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Run tests
make test

# Run linters
make lint

# Format code
make format
```

---

## Project Structure

```
├── .github/workflows/      # CI/CD (6 critical workflows)
├── apps/web/               # Next.js dashboard
├── python/                 # Python codebase
│   └── multi_agent/        # Multi-agent system
│       ├── orchestrator.py # Core dispatcher
│       ├── base_agent.py   # Abstract base
│       ├── agents.py       # Concrete implementations
│       ├── protocol.py     # Communication protocol
│       └── tracing.py      # OpenTelemetry setup
├── src/agents/             # Agent utilities
├── supabase/               # Database config
│   └── migrations/         # Schema versions
├── sql/                    # Analytics queries
│   ├── base_views.sql      # Core views
│   └── v_portfolio_risk.sql # Risk analytics
├── tests/                  # Test suite
├── scripts/                # Build/deploy scripts
├── docker-compose.yml      # Local environment
├── Dockerfile              # Python agent container
└── docs/UNIFIED.md         # Complete documentation
```

---

## Technology Stack

**Backend**
- Python 3.11+ (Multi-agent system)
- PostgreSQL 15 (via Supabase)
- n8n (Webhook orchestration)
- OpenTelemetry (Observability)

**Frontend**
- Next.js 15 (App Router)
- React 19
- Tailwind CSS 4.0
- Plotly (Charts)

**Infrastructure**
- Docker (Local development)
- GitHub Actions (CI/CD)
- Azure (Production hosting)
- Supabase (Managed PostgreSQL + Auth)

---

## Common Tasks

```bash
# Testing
make test              # Run test suite
pytest tests/ -v       # Verbose tests

# Code Quality
make lint              # Run linters (ruff, flake8, mypy)
make format            # Format code (black, isort)

# Docker
make docker-up         # Start services
make docker-down       # Stop services
make docker-logs       # View logs

# Deployment
make deploy            # Run CI checks + deploy prep
```

---

## Documentation

- **[docs/UNIFIED.md](docs/UNIFIED.md)** - Complete system documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[SECURITY.md](SECURITY.md)** - Security policies
- **[CLEANUP_PLAN.md](CLEANUP_PLAN.md)** - Repository cleanup details

---

## Key Features

✅ Real-time loan data ingestion  
✅ Automated risk assessment  
✅ Multi-agent intelligent processing  
✅ KPI tracking and reporting  
✅ Interactive dashboards  
✅ OpenTelemetry observability  
✅ Production-ready CI/CD  

---

## Contributing

1. Create feature branch: `git checkout -b feature/amazing-feature`
2. Make changes and commit: `git commit -m 'Add amazing feature'`
3. Run tests: `make test`
4. Run linters: `make lint`
5. Push branch: `git push origin feature/amazing-feature`
6. Open Pull Request

---

## License

See [LICENSE](LICENSE) file for details.

---

## Support

For questions or issues:
- Check [docs/UNIFIED.md](docs/UNIFIED.md)
- Search GitHub Issues
- Create new issue with details
- Contact: support@abacofinance.com

---

**Version**: 2.0  
**Last Updated**: 2026-01-28  
**Maintained by**: Abaco Analytics Team
