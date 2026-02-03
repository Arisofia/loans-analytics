# Abaco Loans Analytics

## Overview

**Abaco Loans Analytics** is a production-grade fintech lending analytics platform for B2B invoice factoring in Latin America. It provides liquidity against accounts receivable while enforcing strict risk guardrails and portfolio analytics to support scaling Assets Under Management (AUM) with controlled default rates (<4%).

This document is a **high-level platform overview only**. Detailed architecture, KPIs, quick start commands, and repository structure are defined in the canonical documentation listed below.

---

## Where to read more (single source of truth)

- **Architecture, KPIs, features, repo structure**: see the root [README.md](README.md).
- **Full documentation index and topic-specific guides**: see [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md).
- **Documentation policy and conventions**: see [docs/DOCUMENTATION_POLICY.md](docs/DOCUMENTATION_POLICY.md).
- **Repository operations**: see [docs/REPO_OPERATIONS_MASTER.md](docs/REPO_OPERATIONS_MASTER.md).

> **Note**: When running scripts, always use full paths with subdirectories (e.g., `python scripts/data/run_data_pipeline.py`, `python scripts/maintenance/validate_structure.py`) as shown in this document's examples.

---

## Platform at a glance

At a high level, Abaco Loans Analytics combines:

### 1. Unified Data Pipeline (`src/pipeline/`)

A 4-phase ETL orchestration system for loan portfolio analytics:

- **Phase 1**: Ingestion → CSV/Supabase data intake with schema validation
- **Phase 2**: Transformation → PII masking + data normalization (regulatory compliance)
- **Phase 3**: Calculation → 19 KPIs across 6 categories (risk, growth, collections, etc.)
- **Phase 4**: Output → Multi-format export (Parquet/CSV/JSON) + compliance reports

**Entry Point**: `scripts/data/run_data_pipeline.py`

### 2. Multi-Agent AI System (`python/multi_agent/`)

A set of specialized LLM-powered agents for lending intelligence, including:

- **Risk Analyst**: Portfolio risk assessment and early warning signals
- **Growth Strategist**: Expansion opportunities and market insights
- **Ops Optimizer**: Process efficiency and operational improvements
- **Compliance Officer**: Regulatory adherence and audit trails
- **Collections Manager**: Recovery strategies and payment tracking
- **Fraud Detector**: Anomaly detection and suspicious pattern identification
- **Pricing Analyst**: APR optimization and competitive positioning
- **Retention Specialist**: Client lifetime value and churn prevention

---

## Quick Start

For end-to-end onboarding (environment setup, pipeline execution, tests, and dashboard launch), see the **Quick Start** section in the root [README.md](README.md).
---

## Key Resources

### Documentation
- **[README.md](README.md)**: Comprehensive setup and feature guide
- **[REPO_STRUCTURE.md](REPO_STRUCTURE.md)**: Directory organization and module layout
- **[CHANGELOG.md](CHANGELOG.md)**: Version history and updates
- **[.github/copilot-instructions.md](.github/copilot-instructions.md)**: Detailed development guidelines
- **[docs/architecture/](docs/architecture/)**: System design and technical specifications
- **[docs/operations/](docs/operations/)**: Runbooks and deployment guides

### External Links
- [GitHub Repository](https://github.com/Arisofia/abaco-loans-analytics)
- Supabase Metrics API: See [docs/SUPABASE_METRICS_INTEGRATION.md](docs/SUPABASE_METRICS_INTEGRATION.md)
- Production Readiness: See [PRODUCTION_READINESS_REPORT.md](PRODUCTION_READINESS_REPORT.md)

### Support & Contact
For questions or issues:

1. Check [docs/operations/](docs/operations/) for runbooks
2. Review [CHANGELOG.md](CHANGELOG.md) for recent changes
3. Open an issue on GitHub with context and logs

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

For the latest platform version and production readiness status, see [CHANGELOG.md](CHANGELOG.md) and [PRODUCTION_READINESS_REPORT.md](PRODUCTION_READINESS_REPORT.md). This overview intentionally avoids hard-coded version or status values to remain evergreen.
