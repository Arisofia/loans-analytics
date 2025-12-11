# ABACO — Loan Analytics Platform

## Architecture

- **apps/web**: Next.js corporate dashboard
- **apps/analytics**: Python pipelines for risk assessment, scoring, and KPIs
- **infra/azure**: Azure deployment scripts
- **data_samples**: Anonymized datasets for development

## Available Integrations

- Azure SQL / Cosmos / Storage
- Supabase
- Vercel
- OpenAI / Gemini / Claude
- SonarCloud
- GitHub Actions

Refer to `docs/integration-readiness.md` to verify the status of each integration and the prerequisites you must complete before using them.

## ContosoTeamStats

This repository contains ContosoTeamStats, a .NET 6 Web API for managing sports teams that ships with Docker, Azure deployment scripts, SendGrid/Twilio integrations, and SQL Server migrations.

Follow `docs/ContosoTeamStats-setup.md` for local setup, secrets, database provisioning, and container validation.

See `docs/Analytics-Vision.md` for the analytics vision, Streamlit blueprint, and the agent-ready narrative that keeps every KPI, scenario, and AI prompt aligned with our fintech-grade delivery.

## Java and Gradle Setup

Use a locally installed JDK (21+ recommended) and let Gradle's toolchain resolver download the appropriate compiler per module. Avoid adding `org.gradle.java.home` to version control so CI and developers can rely on their own `JAVA_HOME` or toolchains without path-specific overrides.

## Copilot Enterprise Workflow

Use `docs/Copilot-Team-Workflow.md` when inviting your team to Copilot, documenting the validation and security workflows, and keeping the Azure, GitHub Actions, and KPI checklist aligned with your 30-day Enterprise trial (App Service F1, ACR Basic, and free Azure security tiers). The doc includes prompts you can reuse whenever Copilot is guiding changes.

## Fitten Code AI

To integrate Fitten Code AI into this monorepo (local and GitHub), refer to `docs/Fitten-Code-AI-Manual.md`, which covers product introduction, installation, integration, FAQs, and local inference testing.

## MCP Configuration

Use `docs/MCP_CONFIGURATION.md` to add MCP servers via the Codex CLI or by editing `config.toml`, including examples for Context7, Figma, Chrome DevTools, and how to run Codex itself as an MCP server.

## Deno Helper

The repository exposes a tiny Deno helper at `main.ts` that verifies the expected directories before you execute tooling such as Fitten or analytics scripts. Run it with:

```sh
deno run --allow-all main.ts
```

Note: `--unstable` is no longer needed in Deno 2.0; only include the specific `--unstable-*` flags when you actually depend on unstable APIs.

## Troubleshooting VS Code Zencoder Extension

If you see `Failed to spawn Zencoder process: ... zencoder-cli ENOENT` while working in VS Code, follow the remediation checklist in `docs/Zencoder-Troubleshooting.md` to reinstall the extension and restore the missing binary.

## Deployment

This repository is configured for automated deployment to Azure Static Web Apps and integrates with SonarCloud for code quality analysis.
