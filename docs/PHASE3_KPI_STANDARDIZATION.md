# Phase 3 - Data and KPI Standardization

## A. Canonical KPI Architecture Definition

Canonical execution engine: `backend/src/kpi_engine/engine.py::run_metric_engine`

Authoritative compute modules:
- `backend/src/kpi_engine/risk.py`
- `backend/src/kpi_engine/revenue.py`
- `backend/src/kpi_engine/unit_economics.py`
- `backend/src/kpi_engine/cohorts.py`

Authoritative registries:
- `config/kpis/kpi_definitions.yaml` for metric formulas, semantics, thresholds, precision, and canonical function references
- `config/metrics/metric_registry.yaml` for runtime ownership and formula refs

Allowed consumers:
- pipeline decision phase
- pipeline output persistence/export layer
- API routes under `backend/loans_analytics/apps/analytics/api/routes/metrics.py`
- compatibility wrappers only if they delegate to canonical helpers

Forbidden pattern:
- independent financial KPI math outside `backend/src/kpi_engine/*`

## B. KPI Inventory Table

| KPI | Class | Status | Canonical | Notes |
|---|---|---|---|---|
| PAR30/PAR60/PAR90 | risk metric | implemented | `backend/src/kpi_engine/risk.py` | canonical ratio outputs |
| NPL Ratio | risk metric | implemented | `backend/src/kpi_engine/risk.py` | Basel-aligned point-in-time exposure |
| Default Rate By Count | risk metric | implemented | `backend/src/kpi_engine/risk.py` | canonical count-based default metric |
| Default Rate By Balance | risk metric | implemented | `backend/src/kpi_engine/risk.py` | canonical balance-based default metric |
| Expected Loss | risk metric | implemented | `backend/src/kpi_engine/risk.py` | EL = PD x LGD x EAD |
| Provision Coverage Ratio | accounting metric | implemented | `backend/src/kpi_engine/risk.py` | provisions / NPL exposure |
| Portfolio Yield | portfolio proxy metric | implemented | `backend/src/kpi_engine/revenue.py` | exposure-weighted annualized yield |
| Effective Interest Rate | accounting metric | implemented | `backend/src/kpi_engine/revenue.py` | daily-compounded EIR |
| Portfolio IRR | portfolio metric | implemented | `backend/src/kpi_engine/revenue.py` | true XIRR when dated cashflows exist |
| Portfolio IRR Proxy | proxy metric | implemented | `backend/src/kpi_engine/revenue.py` | finance fallback when no dated cashflows exist |
| Net Yield | accounting metric | implemented | `backend/src/kpi_engine/revenue.py` | finance mart derived |
| Spread | accounting metric | implemented | `backend/src/kpi_engine/revenue.py` | finance mart derived |
| Avg Ticket / Win Rate / Contribution Margin | portfolio/commercial metrics | implemented | `backend/src/kpi_engine/unit_economics.py` | canonical engine outputs |
| `portfolio_kpis()` legacy wrapper | deprecated consumer | redirected | `backend/src/analytics/__init__.py` | now delegates financial math to canonical helpers |
| segment default rate in pipeline output | duplicate | redirected | `backend/src/pipeline/output.py` | now calls canonical default-rate helper |
| segment portfolio yield in pipeline output | duplicate | redirected | `backend/src/pipeline/output.py` | now calls canonical yield helper |
| zero-cost snapshot PAR percentages | duplicate | redirected | `backend/src/zero_cost/monthly_snapshot.py` | now calls canonical PAR helpers |

## C. Exact Formulas and Rationale for Newly Added or Formalized KPIs

### Effective Interest Rate
- Name: Effective Interest Rate
- Formula: `(1 + avg_nominal_apr / 365)^365 - 1`
- Required inputs: `interest_rate` or `apr`
- Output type: `Decimal`
- Unit: ratio
- Precision expectation: 4 decimals, `ROUND_HALF_UP`
- Temporality: derived
- Rationale: converts nominal annual pricing into a compounding-consistent rate for audit and pricing governance.

### Portfolio IRR
- Name: Portfolio IRR
- Formula: `XIRR(cashflows, dates)` where disbursements are negative and payments are positive
- Required inputs: `disbursement_date`, `disbursement_amount`, `payment_date`, `payment_amount`
- Output type: `Decimal`
- Unit: ratio
- Precision expectation: 4 decimals, `ROUND_HALF_UP`
- Temporality: historical
- Rationale: institutional return metric based on dated cashflow reality, not balance proxies.

### Portfolio IRR Proxy
- Name: Portfolio IRR Proxy
- Formula: `(SUM(interest_income) + SUM(fee_income)) / AVG(debt_balance)`
- Required inputs: `interest_income`, `fee_income`, `debt_balance`
- Output type: `Decimal`
- Unit: ratio
- Precision expectation: 4 decimals, `ROUND_HALF_UP`
- Temporality: derived
- Rationale: controlled fallback when dated cashflow linkage is unavailable.

### Provision Coverage Ratio
- Name: Provision Coverage Ratio
- Formula: `SUM(provision_expense) / SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted')`
- Required inputs: `provision_expense`, `outstanding_balance`, `dpd`, `status`
- Output type: `Decimal`
- Unit: ratio
- Precision expectation: 4 decimals, `ROUND_HALF_UP`
- Temporality: point-in-time
- Rationale: audit-grade link between impairment recognition and non-performing exposure.

### Portfolio Yield
- Name: Portfolio Yield
- Formula: `SUM(outstanding_balance * interest_rate) / SUM(outstanding_balance) * 100`
- Required inputs: `outstanding_balance`, `interest_rate`
- Output type: `Decimal`
- Unit: percentage
- Precision expectation: 2 decimals, `ROUND_HALF_UP`
- Temporality: point-in-time
- Rationale: exposure-weighted pricing signal; avoids semantic drift from simple arithmetic mean.

## D. File-by-File Implementation Plan

- `backend/src/kpi_engine/risk.py`: canonicalize default-rate, NPL, delinquency, and provision-coverage helpers
- `backend/src/kpi_engine/revenue.py`: canonicalize portfolio yield and formalize IRR split between true and proxy
- `backend/src/kpi_engine/engine.py`: expose standardized Phase 3 metrics and flattening helper for downstream surfaces
- `backend/src/pipeline/output.py`: remove independent segment financial math and route through canonical helpers
- `backend/src/pipeline/calculation.py`: route default-rate derivatives through canonical helper
- `backend/src/analytics/__init__.py`: retain compatibility wrapper while delegating financial KPI math to canonical layer
- `backend/src/zero_cost/monthly_snapshot.py`: remove local PAR math and use canonical PAR functions
- `backend/loans_analytics/apps/analytics/api/service.py`: make YAML metadata authoritative over embedded fallback metadata
- `config/kpis/kpi_definitions.yaml`: formalize new KPI semantics and canonical references
- `config/metrics/metric_registry.yaml`: register new canonical metrics
- `tests/phase3/*`: precision, exclusivity, and cross-surface consistency coverage

## E. Corrected Code

Implemented in the files listed above.

## F. Test Suite Additions

- `tests/phase3/test_kpi_standardization.py`
  - exposure-weighted portfolio yield
  - provision coverage with status fallback
  - separation of default-by-count vs default-by-balance
- `tests/phase3/test_kpi_consistency.py`
  - canonical engine metric IDs updated for Phase 3
  - consistency across engine, API `/api/metrics/run`, and output persistence row preparation
- `tests/phase3/test_ssot_exclusivity.py`
  - verifies legacy wrappers and exports delegate to canonical helpers

## G. Data Model Integrity Recommendations

1. Enforce `payment.loan_id -> loan.loan_id` at ingestion pre-check level before transformation, not only in SQL migrations.
2. Add join-quality metrics: `payment_match_ratio`, `orphaned_payment_count`, `customer_match_ratio`, and persist them in run metadata.
3. Validate `payment_date >= disbursement_date` and fail the run when breached above tolerance.
4. Add balance reconciliation control: `original_principal ≈ recovered + outstanding + written_off` within a configurable tolerance.
5. Make fallback revenue mode explicit in `KPICatalogProcessor.get_monthly_revenue_df()` with an audit flag instead of silent fallback.
6. Add post-write row-count reconciliation when persisting `monitoring.kpi_values`.

## H. Phase 3 Completion Verdict

Phase 3 is materially completed for KPI governance hardening:
- canonical KPI execution engine established and reinforced
- key production-grade metrics formalized and registered
- major duplicate active computation paths redirected
- precision and cross-surface consistency tests added
- integrity recommendations documented for remaining cross-table lineage controls

Residual follow-up:
- migrate remaining legacy `backend/loans_analytics/kpis/*` analytical modules to explicit canonical wrappers or retire them
- implement cross-table referential checks at ingestion/transformation boundary for payment-loan linkage