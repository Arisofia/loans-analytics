# KPI Implementation Inventory & Consolidation Tracker

**Status**: Foundation Document for Workstream 4 (Phase 3: Implementation Consolidation)  
**Last Updated**: 2026-03-19  
**Purpose**: Track all KPI implementations across codebase and consolidation progress

---

## Consolidation Status Overview

| Phase | Status | Description | ETA |
|-------|--------|-------------|-----|
| **Phase 1** | ✅ Complete | Registry definition in `config/kpis/kpi_definitions.yaml` | 2026-03-19 |
| **Phase 2** | 🔄 In Progress | Formula engine implementation and testing | 2026-03-31 |
| **Phase 3** | 📋 Planned | Migrate all KPI modules to use engine | 2026-04-30 |
| **Phase 4** | 📋 Planned | Consumer migration (APIs, dashboards, exports) | 2026-05-15 |
| **Phase 5** | 📋 Planned | Sunsetting old implementations | 2026-09-15 |

---

## KPI Implementations Inventory

### Core Portfolio Risk KPIs

#### 1. PAR-30 (Portfolio at Risk - 30 days)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(outstanding_balance WHERE dpd >= 30) / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status | Notes |
|----------|--------|--------|-------|
| **Python** | `backend/python/kpis/advanced_risk.py` | ❌ Duplicate | Uses column `outstanding`, no status filter |
| **Python** | `backend/python/kpis/portfolio_analytics.py` | ❌ Duplicate | Uses column `balance`, rounds to 2 decimals |
| **SQL** | Postgres view `analytics.par_30` | ❌ Duplicate | Uses `outstanding_balance`, no aggregation grain specified |
| **JavaScript** | Frontend dashboard | ❌ Duplicate | Client-side calculation from REST API |
| **API** | `GET /api/kpis/par_30` | ⏳ Requires Migration | Must use formula engine |

**Consolidation Plan**:
1. ☐ Verify regression test (historical data precision match)
2. ☐ Redirect Python implementations to engine
3. ☐ Update SQL view to call Python engine
4. ☐ Update API to return engine result + audit metadata
5. ☐ Deprecate old implementations

**Regression Test Result**: (Pending Phase 2 completion)

---

#### 2. PAR-60 (Portfolio at Risk - 60 days)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(outstanding_balance WHERE dpd >= 60) / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/advanced_risk.py:calculate_par_60()` | ❌ Duplicate |
| **SQL** | Postgres view `analytics.par_60` | ❌ Duplicate |
| **API** | `GET /api/kpis/par_60` | ⏳ Requires Migration |

**Consolidation Status**: Same pattern as PAR-30

---

#### 3. PAR-90 (Portfolio at Risk - 90 days)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(outstanding_balance WHERE dpd >= 90) / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/advanced_risk.py:calculate_par_90()` | ❌ Duplicate |
| **SQL** | Postgres view `analytics.par_90` | ❌ Duplicate |
| **Dashboard** | "Portfolio Risk" dashboard | ❌ Duplicate |
| **API** | `GET /api/kpis/par_90` | ⏳ Requires Migration |

**Consolidation Status**: Same pattern as PAR-30

---

#### 4. NPL Ratio (Non-Performing Loans - Broad)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(outstanding_balance WHERE dpd >= 30 OR status IN ('delinquent','defaulted')) / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |
| **Notes** | Broad definition (early warning); distinct from NPL-90 (strict Basel) |

**Current Implementations**:
| Location | Module | Status | Notes |
| **Python** | `backend/python/kpis/engine.py:KPIEngineV2.calculate_npl_ratio()` | ✅ Canonical | Already in engine |
| **Python** | `backend/python/kpis/advanced_risk.py:calculate_npl ()` | ❌ Duplicate | Different formula (no status check) |
| **SQL** | Custom query in analytics dashboards | ❌ Duplicate | Uses only DPD >= 30 |

**Consolidation Status**: Engine exists; need to consolidate other implementations

---

#### 5. NPL-90 Ratio (Non-Performing Loans - Strict Basel)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted') / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |
| **Notes** | Strict definition (90+ days or defaulted); regulatory standard |

**Current Implementations**:
| Location | Module | Status | Notes |
| **Python** | `backend/python/kpis/engine.py:KPIEngineV2.calculate_npl_90_ratio()` | ✅ Canonical | Already in engine |
| **SQL** | Regulatory reporting query | ❌ Potential Duplicate | Need to verify formula matches |

**Consolidation Status**: Engine exists; verify SQL alignment

---

### Cash Flow & Collections KPIs

#### 6. Collections Rate

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(last_payment_amount) / SUM(total_scheduled) * 100` |
| **Unit** | percentage |
| **Owner** | @data-engineering |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/collection_rate.py:calculate_collection_rate()` | ✅ Canonical | Main implementation |
| **Python** | `backend/python/kpis/lending_kpis.py:daily_collection_rate()` | ❌ Duplicate | Time-bucketed variant |
| **SQL** | Postgres view `analytics.collections_rate_daily` | ❌ Duplicate |

**Consolidation Status**: Candidate for engine migration

---

#### 7. Recovery Rate

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(last_payment_amount WHERE status = 'defaulted') / SUM(outstanding_balance WHERE status = 'defaulted') * 100` |
| **Unit** | percentage |
| **Owner** | @risk-finance |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/collection_rate.py:calculate_recovery_rate()` | ✅ Canonical |
| **SQL** | Custom analytics query | ❌ Potential Duplicate |

**Consolidation Status**: Candidate for engine migration

---

### Yield & Pricing KPIs

#### 8. Portfolio Yield (Average APR)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `AVG(interest_rate) * 100` |
| **Unit** | percentage |
| **Owner** | @pricing |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/unit_economics.py:portfolio_yield()` | ❌ Duplicate |
| **Python** | `backend/python/kpis/portfolio_analytics.py:avg_interest_rate()` | ❌ Duplicate |
| **SQL** | `analytics.kpi_monthly_pricing.weighted_apr` | ✅ Weighted variant | Different (weighted by outstanding) |

**Consolidation Status**: Need to clarify: simple avg vs. weighted avg

**Note**: There are TWO distinct formulas here:
- **Simple Average**: `AVG(interest_rate)` → portfolio_yield
- **Weighted Average**: `WEIGHTED_AVG(interest_rate)` → weighted_apr_ (formula name in YAML) 

These should be treated as separate KPIs!

---

#### 9. Weighted Portfolio Yield

**Note**: This is a DISTINCT KPI from Portfolio Yield (simple average)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(interest_rate * outstanding_balance) / SUM(outstanding_balance) * 100` |
| **Unit** | percentage |
| **Owner** | @pricing |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **SQL** | `analytics.kpi_monthly_pricing.weighted_apr` | ✅ Canonical |
| **Python** | `backend/python/kpis/unit_economics.py` | ❌ Duplicate (simple avg, not weighted) |

**Consolidation Status**: Clarify in YAML; create separate SimpleYield vs. WeightedYield KPIs

---

### Growth KPIs

#### 10. Disbursement Volume MTD

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `SUM(principal_amount WHERE origination_date >= MONTH_START)` |
| **Unit** | USD |
| **Owner** | @growth |
| **Registry Version** | 1.0 |
| **Frequency** | Daily (MTD updates) |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/portfolio_analytics.py` | ❌ Duplicate |
| **SQL** | Dashboard source query | ❌ Duplicate |
| **JavaScript** | "Growth Metrics" dashboard | ❌ Duplicate |

**Consolidation Status**: Candidate for engine migration

---

### Customer KPIs

#### 11. Active Borrowers Count

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `COUNT(DISTINCT borrower_id WHERE status IN ['active', 'defaulted'])` |
| **Unit** | count |
| **Owner** | @product |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | Multiple modules | ❌ Inconsistent | Some use status, some don't |
| **SQL** | Dashboard queries | ❌ Duplicate |

**Consolidation Status**: High priority (customer counting is critical metric)

---

### Advanced/Derived KPIs

#### 12. Cost of Risk

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `npl_ratio * lgd / 100` |
| **Unit** | percentage |
| **Owner** | @risk-finance |
| **Registry Version** | 1.0 |
| **Dependencies** | `npl_ratio`, `lgd` |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/advanced_risk.py` | ❌ Duplicate |
| **Formula** | `config/kpis/kpi_definitions.yaml` | ✅ Canonical |

**Consolidation Status**: Engine must support formula dependencies

---

#### 13. LTV (Loan-to-Value)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | `principal_amount / collateral_value * 100` (per-loan), then aggregated |
| **Unit** | percentage |
| **Owner** | @risk-finance |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/ltv.py:calculate_ltv_sintetico()` | ✅ Specialized | Complex calculation module |
| **Python** | Multiple KPI modules (imported) | ❌ Duplicate references |

**Consolidation Status**: Specialized module; should be wrapped in engine interface

---

#### 14. LTV Synthetic (Synthetic LTV for missing collateral)

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | Uses ML model to estimate missing collateral values |
| **Unit** | percentage |
| **Owner** | @data-science |
| **Registry Version** | 1.0 |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/ltv.py:calculate_ltv_sintetico()` | ✅ Canonical |

**Consolidation Status**: Specialized ML module; good candidate for engine wrapper

---

### Health Score & Composite KPIs

#### 15. Portfolio Health Score

| Attribute | Value |
|-----------|-------|
| **Registry Formula** | Weighted combination of multiple KPIs (see notes) |
| **Unit** | score (0-100) |
| **Owner** | @product |
| **Registry Version** | 1.0 |
| **Notes** | Composite KPI; formula involves multiple sub-KPIs |

**Current Implementations**:
| Location | Module | Status |
| **Python** | `backend/python/kpis/health_score.py` | ✅ Canonical |
| **Dashboard** | "Portfolio Dashboard" | ❌ Duplicate (client-side calculation) |

**Consolidation Status**: Engine must support composite/weighted KPI formulas

---

## Summary Statistics

### By Module

| Module | Total KPIs | Canonical | Duplicate | Status |
|--------|-----------|-----------|-----------|--------|
| `engine.py` | 2 | 2 | 0 | ✅ Canonical |
| `advanced_risk.py` | 6 | 0 | 6 | ❌ All Duplicate |
| `portfolio_analytics.py` | 5 | 0 | 5 | ❌ All Duplicate |
| `collection_rate.py` | 2 | 2 | 0 | ✅ Canonical |
| `unit_economics.py` | 4 | 0 | 4 | ❌ All Duplicate |
| `health_score.py` | 1 | 1 | 0 | ✅ Canonical |
| `ltv.py` | 2 | 2 | 0 | ✅ Specialized (good) |
| `lending_kpis.py` | 3 | 0 | 3 | ❌ All Duplicate |
| `strategic_reporting.py` | 2 | 0 | 2 | ❌ All Duplicate |
| `strategic_modules.py` | 1 | 0 | 1 | ❌ Duplicate |
| `graph_analytics.py` | 1 | 0 | 1 | ❌ Duplicate |
| `catalog_processor.py` | 1 | 1 | 0 | ✅ Catalog processor |
| **Other (SQL, JS, API)** | Many | Variable | Variable | ⏳ Audit pending |

### Fragmentation Risk Scores

| KPI | Risk Level | Reason |
|-----|-----------|--------|
| PAR-30/60/90 | 🔴 **Critical** | 4+ implementations, different column names, rounding |
| NPL Ratio | 🟡 **Medium** | Engine exists, but alternatives still in use |
| Collections Rate | 🟡 **Medium** | 2+ implementations, different time bucketing |
| Active Borrowers | 🔴 **Critical** | Inconsistent status filtering across modules |
| Portfolio Yield | 🟠 **High** | Confuses simple avg with weighted avg |
| LTV | 🟠 **High** | Complex model; multiple references but unclear SSOT |
| Cost of Risk | 🟠 **High** | Depends on npl_ratio + lgd; formula chain unclear |

---

## Consolidation Roadmap

### Phase 3A: Foundation KPIs (Week 1-2)
1. ☐ Migrate PAR-30, PAR-60, PAR-90 to engine
2. ☐ Regression test on 12+ months historical data
3. ☐ Redirect Python implementations to engine
4. ☐ Update SQL views to call engine

### Phase 3B: Risk & Collections (Week 3-4)
1. ☐ Migrate NPL Ratio, NPL-90, Collections Rate, Recovery Rate
2. ☐ Test with regulatory reporting data
3. ☐ Update APIs and dashboards

### Phase 3C: Growth & Customer (Week 5)
1. ☐ Migrate Disbursement Volume, Active Borrowers
2. ☐ Test with historical cohort data
3. ☐ Update growth dashboards

### Phase 3D: Advanced KPIs (Week 6)
1. ☐ Wrap LTV, Health Score, Cost of Risk
2. ☐ Test formula dependencies (Cost of Risk = npl_ratio * lgd)
3. ☐ Composite KPI support in engine

### Phase 3E: Cleanup (Week 7+)
1. ☐ Deprecate old implementations
2. ☐ Remove duplicate code
3. ☐ Update documentation

---

## Success Criteria

- ✅ Every KPI defined in registry
- ✅ Every KPI has >= 1 regression test (historical data precision match)
- ✅ Every KPI has audit trail (formula version, timestamp, actor)
- ✅ Zero duplicate implementations (code review enforces)
- ✅ All consumers (API, dashboard, batch) use same engine
- ✅ Dashboard KPI = API KPI = Batch KPI (exact match)

---

## References

- [KPI_SSOT_REGISTRY.md](KPI_SSOT_REGISTRY.md) - Consolidation framework and governance
- [config/kpis/kpi_definitions.yaml](../../config/kpis/kpi_definitions.yaml) - Canonical registry
- [docs/KPI_CATALOG.md](KPI_CATALOG.md) - Business definitions
- [docs/kpi_lineage.md](kpi_lineage.md) - Lineage and derivations

