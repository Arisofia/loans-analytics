# ABACO Financial Intelligence Platform

ABACO delivers an executive-grade analytics and governance stack for lending teams. The platform pairs a Next.js dashboard with Python risk pipelines, Azure deployment scripts, and traceable KPI governance. A dual interface is available: Streamlit for rapid exploration and an automated data pipeline for KPI computation and audit trailing.

## Stack map
- **apps/web**: Next.js dashboard for portfolio, risk, and growth views.
- **infra/azure**: Azure infra-as-code and deployment scripts.
- **data_samples**: Anonymized datasets for repeatable development and testing.

For the combined Next.js + FastAPI fintech dashboard (Figma-first, Plotly, AI insights, and KPI endpoints), follow `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md`.

## Java and Gradle setup

## Getting started
- Validate repository structure before running tooling:
  ```
  deno run --allow-all main.ts
  ```
  `--unstable` is unnecessary in Deno 2.0; add specific `--unstable-*` flags only when required.
- Web: see `apps/web` for Next.js dashboard setup.
- Python quick start:
  ```bash
  pip install -r requirements.txt
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
