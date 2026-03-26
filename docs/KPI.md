# KPI Reference (Canonical)

This is the canonical KPI document for the Loans Analytics repository.

It consolidates content previously spread across multiple files:
- KPI_CATALOG.md
- KPI_SSOT_REGISTRY.md
- KPI-Operating-Model.md

## Scope

This reference defines:
- Canonical KPI definitions and naming
- Formula authority and execution path
- Ownership, change control, and governance
- Required validation and audit trail for KPI updates

## Canonical Sources of Truth

- KPI definitions registry: config/kpis/kpi_definitions.yaml
- Formula execution engine: backend/python/kpis/formula_engine.py
- Core KPI calculations: backend/python/kpis/engine.py
- Risk-focused SSOT module: backend/python/kpis/ssot_asset_quality.py
- Data lineage reference: docs/kpi_lineage.md

## KPI Domains

- Portfolio and growth
- Risk and delinquency (PAR, NPL, default-related metrics)
- Pricing and yield
- Collections and efficiency
- Concentration and exposure

## Governance Model

- Business owner approves formula intent and thresholds.
- Data and analytics own implementation, test coverage, and release readiness.
- Every KPI formula change must update:
  - config/kpis/kpi_definitions.yaml
  - calculation code path in backend/python/kpis/
  - tests for formula correctness and edge cases
  - changelog and governance notes in docs/GOVERNANCE.md when policy-impacting

## Change Control Requirements

1. Open PR with business justification and impact analysis.
2. Update registry version and formula metadata.
3. Add or update tests for normal and edge scenarios.
4. Verify no drift across API, pipeline output, and dashboards.
5. Record release notes for KPI behavior changes.

## Precision and Safety Rules

- Use Decimal for financial values and ratios where applicable.
- Avoid float-based rounding for currency calculations.
- Ensure deterministic behavior for all KPI runs.
- Do not expose PII in KPI logs or exports.

## Operational Validation Checklist

- Formula output matches registry definition.
- Units are explicit and consistent (USD, percentage, count).
- Denominator and status filters are stable across consumers.
- API and pipeline outputs reconcile on the same snapshot window.
- Alerts and thresholds map to the same KPI identifiers.

## Related Documents

- docs/kpi_lineage.md
- docs/GOVERNANCE.md
- docs/KPI_CATALOG.md (compatibility pointer)
- docs/KPI_SSOT_REGISTRY.md (compatibility pointer)
- docs/KPI-Operating-Model.md (compatibility pointer)
