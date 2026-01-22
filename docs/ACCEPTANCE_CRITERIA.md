# Acceptance Criteria for Production Readiness

This document defines the measurable criteria that must be met for the **Abaco Loans Analytics** platform to be considered "Production-Ready". These criteria guide the transformation process and serve as the final checklist before full operational handover.

## 1. Reliability & Stability

- **Pipeline Success Rate**: 100% of scheduled pipeline runs must complete successfully for 14 consecutive days.
- **Data Freshness**: Dashboard must reflect data no older than 24 hours (for batch) or 1 hour (for near-real-time ingestion).
- **Rollback Capability**: System must support 1-command rollback to the previous stable version of both code and configuration.

## 2. Code Quality & Maintainability

- **Test Coverage**:
  - > 90% line coverage for critical business logic (KPI formulas, data transformation).
  - > 70% overall project coverage.
- **Linting & Type Safety**:
  - 0 critical linting errors (Ruff/ESLint).
  - 100% Type safety in core pipeline phases (Mypy/TypeScript).
- **Modular Architecture**: All 4 pipeline phases (Ingestion, Transformation, Calculation, Output) must be strictly decoupled with defined interfaces.

## 3. Security & Compliance

- **Secret Management**: 0 hardcoded secrets in the repository. All secrets must be managed via environment variables or Azure Key Vault.
- **PII Protection**: 100% of PII fields (defined in `config/pii_fields.yaml`) must be masked or excluded from final output artifacts.
- **Audit Trail**: Every pipeline run must generate a manifest containing:
  - Run ID and timestamp.
  - Input data hash.
  - Data quality scores.
  - User/System actor attribution.

## 4. Performance

- **Ingestion Scale**: Pipeline must handle a 50MB CSV file within < 5 minutes on standard hardware.
- **Dashboard Latency**: Key performance indicators (KPIs) must load in the frontend in < 2 seconds for processed datasets.

## 5. Documentation & Operations

- **Runbooks**: Complete, tested runbooks for:
  - Pipeline failure recovery.
  - KPI definition updates.
  - New data source onboarding.
- **Architecture**: `ARCHITECTURE.md` must accurately reflect the "Unified Modular Pipeline" state.
- **KPI Catalog**: Single source of truth for all formulas, owners, and thresholds.
