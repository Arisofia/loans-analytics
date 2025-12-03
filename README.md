# ABACO — Loan Analytics Platform

ABACO delivers an executive-grade analytics and governance stack for lending teams. The platform pairs a Next.js dashboard with Python risk pipelines, Azure deployment scripts, and traceable KPI governance.

## Stack map
- **apps/web**: Next.js dashboard for portfolio, risk, and growth views.
- **apps/analytics**: Python scoring, stress testing, and KPI pipelines.
- **infra/azure**: Azure infra-as-code and deployment scripts.
- **data_samples**: Anonymized datasets for repeatable development and testing.

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
- Integrations: configure Figma, Notion, and Slack SDKs via `docs/integrations.md` (Node.js/TypeScript and Python examples, environment variables, and figma-export token export).

## Essential knowledge base
- `docs/Analytics-Vision.md`: Vision, Streamlit blueprint, and narrative alignment for KPIs and prompts.
- `docs/KPI-Operating-Model.md`: Ownership, formulas, dashboard standards, lineage, GitHub guardrails, and audit controls.
- `docs/Copilot-Team-Workflow.md`: Inviting teams to GitHub Copilot, validation/security workflows, and Azure/GitHub/KPI checklists during the Enterprise trial.
- `docs/ContosoTeamStats-setup.md`: Setup, secrets, migrations, Docker validation, and Azure deployment for the bundled ContosoTeamStats .NET 6 Web API.
- `docs/Fitten-Code-AI-Manual.md`: Fitten Code AI installation, GitHub integration, FAQs, and local inference testing.
- `docs/MCP_CONFIGURATION.md`: Adding MCP servers via Codex CLI or `config.toml`, including Context7, Figma, Chrome DevTools, and running Codex as an MCP server.
- `docs/Zencoder-Troubleshooting.md`: Remediation checklist for the VS Code Zencoder extension (`zencoder-cli ENOENT`).
- `docs/integrations.md`: Figma, Notion, and Slack SDK setup guides with environment variables, CLI token export, and client snippets for Node.js/TypeScript and Python.
