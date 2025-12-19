# ABACO Financial Intelligence Platform

ABACO delivers an executive-grade analytics and governance stack for lending teams. The platform pairs a Next.js dashboard with Python risk pipelines, Azure deployment scripts, and traceable KPI governance. A dual interface is available: Streamlit for rapid exploration and an automated data pipeline for KPI computation and audit trailing.

## Stack map
- **apps/web**: Next.js dashboard for portfolio, risk, and growth views.
- **apps/analytics**: Python scoring, stress testing, and KPI pipelines.
- **python/**: Centralized analytics helpers (`analytics.py`, `validation.py`, `financial_analysis.py`, `kpi_engine.py`) used by scripts and dashboards.
- **streamlit_app.py**: Canonical Streamlit dashboard entry point.
- **scripts/run_data_pipeline.py**: Automated pipeline runner for portfolio snapshots.
- **infra/azure**: Azure infra-as-code and deployment scripts.
- **data_samples**: Anonymized datasets for repeatable development and testing.
- **Integrations**: Figma / Notion / Slack setup guide at `docs/integrations.md` (see `docs/integration-readiness.md` for service checks).

## Observability, KPIs, and lineage
- **KPI catalog**: Use `docs/KPI-Operating-Model.md` to define owners, formulas, and lineage links for every metric; keep PR and issue references for auditability.
- **Dashboards**: Ensure every visualization lists source tables, refresh timestamp, and on-call owner. Target vs. actual, sparkline trends, and SLA badges should be present on executive views.
- **Data quality**: Track null/invalid rates, schema drift counts, ingestion success %, and freshness lag; surface alerts into the dashboard and CI comments.

## Governance and compliance guardrails
- Enforce PR reviews, lint/test gates, and SonarQube quality gates before merging to main.
- Store secrets in GitHub or cloud KMS; never commit credentials or sample PII.
- Require audit logs for dashboard publishes/exports and validate access controls for sensitive fields.
- Align contributions to the `docs/Analytics-Vision.md` narrative to keep KPIs, prompts, and dashboards within fintech standards.

## Getting started
- Validate repository structure before running tooling:
  ```
  deno run --allow-all main.ts
  ```
  `--unstable` is unnecessary in Deno 2.0; add specific `--unstable-*` flags only when required.
- Web: see `apps/web` for Next.js dashboard setup.
- Analytics: use `apps/analytics` pipelines for risk and KPI computation; keep formulas versioned and tested.
- Infra: apply `infra/azure` scripts for environment provisioning; confirm `docs/integration-readiness.md` for service readiness and pre-checks.
- Python quick start:
  ```bash
  pip install -r requirements.txt
  streamlit run streamlit_app.py            # Dashboard
  python scripts/run_data_pipeline.py       # KPI pipeline
  pytest                                    # Test suite
  ```

## Essential knowledge base
- `docs/Analytics-Vision.md`: Vision, Streamlit blueprint, and narrative alignment for KPIs and prompts.
- `docs/KPI-Operating-Model.md`: Ownership, formulas, dashboard standards, lineage, GitHub guardrails, and audit controls.
- `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md`: Blueprint for the fintech dashboard UI (Next.js), analytics API (FastAPI), data contracts, and deployment/CI requirements.
- `docs/Copilot-Team-Workflow.md`: Inviting teams to GitHub Copilot, validation/security workflows, and Azure/GitHub/KPI checklists during the Enterprise trial.
- `docs/ContosoTeamStats-setup.md`: Setup, secrets, migrations, Docker validation, and Azure deployment for the bundled ContosoTeamStats .NET 6 Web API.
- `docs/Fitten-Code-AI-Manual.md`: Fitten Code AI installation, GitHub integration, FAQs, and local inference testing.
- `docs/GitHub-Workflow-Runbook.md`: Branching strategy, quality gates, agent coordination, and merge standards for traceable releases.
- `docs/MCP_CONFIGURATION.md`: Adding MCP servers via Codex CLI or `config.toml`, including Context7, Figma, Chrome DevTools, and running Codex as an MCP server.
- `docs/Zencoder-Troubleshooting.md`: Remediation checklist for the VS Code Zencoder extension (`zencoder-cli ENOENT`).
