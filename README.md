# AI-MultiAgent-Ecosystem – Abaco Analytics

This repository hosts the Abaco Financial Intelligence Platform, including:

## 🌟 Highlights

- **8-Agent System**: Risk, Growth, Ops, Compliance + Collections, Fraud, Pricing, Retention
- **29 Tests Passing**: 18 KPI integration + 11 specialized agents
- **7 Pre-built Scenarios**: Multi-step workflows for fintech lending
- **KPI-Aware**: Real-time validation and anomaly detection
- **Production-Ready**: Full observability, guardrails, and tracing

## Repository Structure

For a complete overview of the repository organization, see [REPO_STRUCTURE.md](REPO_STRUCTURE.md).

Quick navigation:
- **Python Backend**: `python/` - Multi-agent system, KPIs, data processing
- **Web Frontend**: `apps/web/` - Next.js dashboard
- **Documentation**: `docs/` - Architecture, operations, planning guides
- **Infrastructure**: `infra/` - Azure IaC and deployment

## Stack map

- **apps/web**: Next.js dashboard for portfolio, risk, and growth views.
- **python/multi_agent**: 8-agent orchestration system with fintech expertise ([docs](python/multi_agent/README.md))
- **python/kpis**: KPI calculations and catalog processing
- **python/utils**: Shared utilities for dashboard and data normalization
- **infra/azure**: Azure infra-as-code and deployment scripts.
- **data_samples**: Anonymized datasets for repeatable development and testing.

For the combined Next.js + FastAPI fintech dashboard (Figma-first, Plotly, AI insights, and KPI endpoints), follow `docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md` (if available).

## Getting started

- Validate repository structure before running tooling:
  ```bash
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

All project documentation is now organized in the `docs/` directory:
- **Architecture**: System design and technical specifications (`docs/architecture/`)
- **Operations**: Deployment guides and runbooks (`docs/operations/`)
- **Planning**: Project plans and status updates (`docs/planning/`)
- **Archive**: Historical documentation (`docs/archive/`)

See `docs/README.md` for the complete documentation index.
