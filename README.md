# AI-MultiAgent-Ecosystem – Abaco Analytics

This repository hosts the Abaco Financial Intelligence Platform, including:

## 🌟 Highlights

- **8-Agent System**: Risk, Growth, Ops, Compliance + Collections, Fraud, Pricing, Retention
- **29 Tests Passing**: 18 KPI integration + 11 specialized agents
- **7 Pre-built Scenarios**: Multi-step workflows for fintech lending
- **KPI-Aware**: Real-time validation and anomaly detection
- **Production-Ready**: Full observability, guardrails, and tracing

## Stack map

- **apps/web**: Next.js dashboard for portfolio, risk, and growth views.
- **python/multi_agent**: 8-agent orchestration system with fintech expertise ([docs](python/multi_agent/README.md))
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
All project documentation has been consolidated into a single source of truth:
- `UNIFIED_DOCS.md`: Comprehensive guide covering Analytics Vision, KPI Operating Models, Fintech Dashboard blueprints, and Workflow Runbooks.
