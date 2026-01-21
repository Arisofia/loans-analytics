
# ABACO — Loan Analytics Platform

- Raw Abaco CSV loan tapes under data/abaco
- Synthetic support tables under data/support
- SQL definitions for core views and KPIs under sql/
- Python/Streamlit dashboard under streamlit_app/
- Observability and tracing with Azure Monitor OpenTelemetry

## Ingestion Policy

Ingestion is supported via API and scheduled pipelines with audit controls (run IDs, lineage, and validation logs). Streamlit remains available for manual uploads and QA, but it is not the exclusive ingestion gate.

## Canonical Data Stores

- **BigQuery** is the analytics source of truth for warehouse tables, KPI views, and reporting.
- **Postgres (Supabase)** is the operational/dev store for the web app and integrations.
- **SQL Server** assets are legacy/migration-only and should not be used for new development.

## Stack map

- **apps/web**: Next.js dashboard for portfolio, risk, and growth views (canonical app router in `apps/web/src/app`, config in `apps/web/next.config.ts`).
- **apps/analytics**: Python scoring, stress testing, and KPI pipelines.
- **infra/azure**: Azure infra-as-code and deployment scripts.
- **data/**: Anonymized datasets for repeatable development and testing (subdirs abaco/ and support/).

See docs/DATA_DICTIONARY.md for table documentation.
See docs/KPI_CATALOG.md for KPI definitions and SQL.
See docs/TRACING.md for observability and tracing setup.

## Quick Start

### Environment Setup

## Essential knowledge base

- `docs/Analytics-Vision.md`: Vision, Streamlit blueprint, and narrative alignment for KPIs and prompts.
- `docs/KPI-Operating-Model.md`: Ownership, formulas, dashboard standards, lineage, GitHub guardrails, and audit controls.
- `docs/Copilot-Team-Workflow.md`: Inviting teams to GitHub Copilot, validation/security workflows, and Azure/GitHub/KPI checklists during the Enterprise trial.
- `docs/ContosoTeamStats-setup.md`: Setup, secrets, migrations, Docker validation, and Azure deployment for the bundled ContosoTeamStats .NET 6 Web API.
- `docs/Fitten-Code-AI-Manual.md`: Fitten Code AI installation, GitHub integration, FAQs, and local inference testing.
- `docs/MCP_CONFIGURATION.md`: Adding MCP servers via Codex CLI or `config.toml`, including Context7, Figma, Chrome DevTools, and running Codex as an MCP server.
- `docs/Zencoder-Troubleshooting.md`: Remediation checklist for the VS Code Zencoder extension (`zencoder-cli ENOENT`).

## Repository Policy: All changes to main must be made via Pull Request

Direct pushes to main are blocked by workflow and branch protection rules. See `.github/workflows/block-direct-push.yml` for enforcement. To contribute:

1. Create a feature branch.
2. Open a Pull Request.
3. Pass all required checks and reviews.
4. Merge via PR only.

## Code Quality

This repository uses multiple code quality tools to maintain high standards:

### Quick Commands

```bash
# Run all code quality checks
make quality

# Run specific tools
make lint              # Pylint, Black, isort
npm run lint --prefix apps/web  # ESLint for TypeScript
make test              # Run Python tests
```

### Tools Configured

- **ESLint**: TypeScript/JavaScript linting (apps/web)
- **Pylint**: Python linting and code analysis
- **SonarQube**: Comprehensive code quality analysis (CI only, see `.github/workflows/sonarqube.yml`)
- **Code Climate**: Maintainability and complexity analysis
- **Pre-commit hooks**: Automated checks before commits
- **Black & isort**: Python code formatting

### Documentation

- **Comprehensive Guide**: `docs/CODE_QUALITY_GUIDE.md` - Complete documentation for all tools
- **Engineering Standards**: `docs/ENGINEERING_STANDARDS.md` - Coding standards and best practices
- **Configuration Files**:
  - `.codeclimate.yml` - Code Climate configuration
  - `.pylintrc` - Pylint settings
  - `apps/web/eslint.config.mjs` - ESLint configuration
  - `sonar-project.properties` - SonarQube settings

### Getting Started

1. Install pre-commit hooks:

   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. Run quality checks before committing:

   ```bash
   make quality
   ```

3. View detailed guide:

   ```bash
   cat docs/CODE_QUALITY_GUIDE.md
   ```

For detailed usage instructions, troubleshooting, and best practices, see `docs/CODE_QUALITY_GUIDE.md`.

### CI Workflows

- Main CI: `.github/workflows/ci.yml`
- SonarQube: `.github/workflows/sonarqube.yml` (static analysis, security, code smells)
