# ABACO — Loan Analytics Platform

Arquitectura:

- **apps/web**: Next.js dashboard corporativo.
- **apps/analytics**: pipelines de Python para riesgo, scoring y KPIs.
- **infra/azure**: scripts de despliegue Azure.
- **data_samples**: datasets anonimizados para desarrollo.

Integraciones disponibles:

- Azure SQL / Cosmos / Storage
- Supabase
- Vercel
- OpenAI / Gemini / Claude
- SonarCloud
- GitHub Actions

## ContosoTeamStats

This repository contains ContosoTeamStats, a .NET 6 Web API for managing sports teams that ships with Docker, Azure deployment scripts, SendGrid/Twilio integrations, and SQL Server migrations. Follow docs/ContosoTeamStats-setup.md for local setup, secrets, database provisioning, and container validation.

See docs/Analytics-Vision.md for the analytics vision, Streamlit blueprint, and the agent-ready narrative that keeps every KPI, scenario, and AI prompt aligned with our fintech-grade delivery.

For the combined Next.js + FastAPI fintech dashboard (Figma-first, Plotly, AI insights, and KPI endpoints), follow `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md`.

This repository contains ContosoTeamStats, a .NET 6 Web API for managing sports teams that ships with Docker, Azure deployment scripts, SendGrid/Twilio integrations, and SQL Server migrations. Follow docs/ContosoTeamStats-setup.md for local setup, secrets, database provisioning, and container validation.

## Copilot Enterprise workflow

Use `docs/Copilot-Team-Workflow.md` when inviting your team to Copilot, documenting the validation and security workflows, and keeping the Azure, GitHub Actions, and KPI checklist aligned with your 30-day Enterprise trial (App Service F1, ACR Basic, and free Azure security tiers). The doc includes prompts you can reuse whenever Copilot is guiding changes.

 contains ContosoTeamStats, a .NET 6 Web API for managing sports teams that ships with Docker, Azure deployment scripts, SendGrid/Twilio integrations, and SQL Server migrations. Follow docs/ContosoTeamStats-setup.md for local setup, secrets, database provisioning, and container validation.

## Fitten Code AI 编程助手

Para integrar Fitten Code AI en este monorepo (local y GitHub), consulta `docs/Fitten-Code-AI-Manual.md`, que cubre la introducción al producto, instalación, integración, preguntas frecuentes y pruebas de inferencia local.

## Deno helper

The repository exposes a tiny Deno helper at `main.ts` that verifies the expected directories before you execute tooling such as Fitten or analytics scripts. Run it with:

```
deno run --allow-all main.ts
```

`--unstable` is no longer needed in Deno 2.0; only include the specific `--unstable-*` flags when you actually depend on unstable APIs.
