# Abaco Loans Analytics - AI Multi-Agent Platform

A production-focused financial intelligence platform powered by Python multi-agent systems for loan portfolio analysis, risk assessment, and automated reporting.

## Architecture

```
Azure Web Form → n8n Workflow Orchestration → Supabase Database → Python Multi-Agent Analytics
```

### System Flow
1. **Data Ingestion**: Azure Web Forms collect loan data
2. **Workflow Orchestration**: n8n processes and routes data
3. **Data Storage**: Supabase PostgreSQL stores structured data
4. **Analytics Engine**: Python multi-agent system performs:
   - Portfolio risk analysis
   - KPI calculations
   - Automated reporting
   - Predictive modeling

## Repository Structure

```
├── src/agents/          # Python multi-agent system
├── supabase/            # Database migrations & functions
├── sql/                 # SQL views and models
├── tests/               # Test suite
├── docs/                # Documentation (see UNIFIED.md)
├── .github/workflows/   # CI/CD pipelines
├── docker-compose.yml   # Local development environment
└── requirements.txt     # Python dependencies
```

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL (via Docker or Supabase)

### Local Development

1. **Clone and setup environment**:
```bash
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics
make setup  # Creates venv and installs dependencies
```

2. **Start services** (n8n, PostgreSQL, Python agents):
```bash
make docker-up
```

3. **Run tests**:
```bash
make test
```

4. **Access services**:
- n8n Workflow UI: http://localhost:5678
- Python Agents API: http://localhost:8000
- PostgreSQL: localhost:5432

### Development Commands

```bash
make help           # Show all available commands
make format         # Format code with black & isort
make lint           # Run ruff, flake8, pylint
make type-check     # Run mypy type checking
make test           # Run pytest suite
make test-coverage  # Run tests with coverage report
make clean          # Remove cache and artifacts
make docker-logs    # View service logs
make docker-down    # Stop all services
```

## Core Technologies

- **Language**: Python 3.11
- **Framework**: LangChain, LangGraph
- **LLM Providers**: OpenAI, Anthropic (Claude)
- **Database**: PostgreSQL (Supabase)
- **Orchestration**: n8n
- **Observability**: OpenTelemetry, Azure Monitor
- **Testing**: pytest, pytest-cov
- **Linting**: ruff, black, isort, flake8, pylint, mypy

## CI/CD

GitHub Actions workflows:
- **ci.yml**: Code quality, formatting, linting, testing
- **codeql.yml**: Security scanning
- **deploy.yml**: Production deployment
- **docker-ci.yml**: Docker image builds
- **lint_and_policy.yml**: Policy enforcement
- **pr-review.yml**: Automated PR reviews
- **unified_data_pipeline.yml**: Data pipeline validation

## Documentation

See **[docs/UNIFIED.md](docs/UNIFIED.md)** for comprehensive documentation including:
- System architecture
- Agent protocols
- KPI definitions
- Deployment guides
- API reference

## Environment Variables

Create a `.env` file (see `.env.example`):
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# LLM API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# n8n Configuration
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test: `make test lint format`
4. Commit changes: `git commit -m "feat: description"`
5. Push and create a Pull Request

## License

MIT License - See [LICENSE](LICENSE) file for details

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment guides
- Check [SECURITY.md](SECURITY.md) for security policies
