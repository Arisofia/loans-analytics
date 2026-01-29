# Repository Structure

This document describes the organization of the Abaco Loans Analytics repository after cleanup and reorganization.

## Directory Layout

```
abaco-loans-analytics/
├── apps/                   # Application code
│   └── web/               # Next.js frontend dashboard
├── python/                # Python backend and analytics
│   ├── multi_agent/      # 8-agent AI orchestration system
│   ├── kpis/             # KPI calculations and catalog
│   ├── ingest/           # Data ingestion pipeline
│   ├── models/           # Domain schemas and models
│   ├── financial_engine/ # Risk calculations
│   ├── utils/            # Shared utilities (dashboard, normalization)
│   ├── cli/              # Command-line tools
│   ├── config/           # Configuration (theme, tracing, sitecustomize)
│   ├── tests/            # Test suite
│   └── scripts/          # Batch jobs and utilities
├── docs/                  # Documentation
│   ├── architecture/     # System design, ADRs, specifications
│   ├── operations/       # Runbooks, deployment guides
│   ├── planning/         # Project plans, status updates
│   └── archive/          # Historical documentation
├── infra/                 # Infrastructure as Code
├── streamlit_app/         # Streamlit dashboard (alternative UI)
├── scripts/               # Build and deployment scripts
├── tests/                 # Integration tests
└── .github/               # CI/CD workflows

```

## Key Files

### Root Level (Essential Only)
- `README.md` - Project overview and quickstart
- `CHANGELOG.md` - Version history
- `SECURITY.md` - Security policy
- `LICENSE` - Project license
- `package.json` - Node.js dependencies
- `pyproject.toml` - Python package configuration
- `docker-compose.yml` - Docker orchestration

### Configuration Files
- `.github/workflows/` - CI/CD pipelines
- `python/config/` - Python-specific configuration
- `infra/` - Infrastructure configuration

## Python Module Structure

The `python/` directory follows standard Python package conventions:

- **Core Business Logic**: `multi_agent/`, `kpis/`, `financial_engine/`
- **Data Processing**: `ingest/`, `models/`
- **Utilities**: `utils/`, `cli/`, `config/`
- **Testing**: `tests/`

All Python utilities are now properly modularized under `python/` rather than scattered in the root.

## Documentation Organization

Documentation in `docs/` is organized by purpose:

- **architecture/** - For developers and architects
- **operations/** - For DevOps and deployment
- **planning/** - For project management and stakeholders
- **archive/** - For historical reference

## Recent Changes

This structure was established through repository cleanup:

1. **Phase 1**: Moved 9 root-level Python files into `python/` modules
2. **Phase 2**: Organized 14 root-level MD files into `docs/` hierarchy
3. Result: Cleaner, more navigable repository structure

For more details, see `CHANGELOG.md`.
