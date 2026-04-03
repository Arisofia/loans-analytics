# KPI Lineage & Dependency Graph

**Document Status**: P8 Documentation Remediation (2026-03-20)  
**Pillar**: Financial Precision & KPI SSOT (P4/P5)  
**Owner**: Data Analytics Team

## Overview

This document maps KPI calculation dependencies, upstream data sources, and transformation lineage.

## Lineage Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                             │
│  CSV Input → Database (Supabase) → DuckDB Local Analytics       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ↓
        ┌──────────────────────────────────┐
        │   INGESTION PHASE                │
        │  (Load & validate raw data)      │
        └──────────────┬───────────────────┘
                       │
                       ↓
        ┌──────────────────────────────────┐
        │ TRANSFORMATION PHASE              │
        │ • Null handling (smart strategy) │
        │ • Outlier detection (IQR)        │
        │ • Status normalization           │
        │ • Currency conversion            │
        └──────────────┬───────────────────┘
                       │
         ┌─────────────┴─────────────┐
         ↓                           ↓
    ┌──────────────┐          ┌──────────────┐
    │ Loan Table   │          │ Payment Log  │
    │ (principals) │          │ (collections)│
    └──────┬───────┘          └──────┬───────┘
           │                         │
           └─────────────┬───────────┘
                         ↓
          ┌──────────────────────────────────┐
          │  CALCULATION PHASE               │
          │  (Core KPI Engine)               │
          └──────────┬─────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      ↓              ↓              ↓
   ┌──────────┐  ┌───────────┐  ┌─────────┐
   │ Asset    │  │ Risk      │  │ Finance │
   │ Quality  │  │ Metrics   │  │ Metrics │
   └──────────┘  └───────────┘  └─────────┘
      │              │              │
      └──────────────┼──────────────┘
                     ↓
          ┌──────────────────────────────────┐
          │  OUTPUT PHASE                    │
          │  (Results → Supabase + Exports)  │
          └──────────────────────────────────┘
```

## KPI Dependency Tree

### Asset Quality Metrics (SSoT Authority: `ssot_asset_quality.py`)

```
Outstanding Balance (raw)
    ↓
    ├→ [Filter: DPD ≥ 30] → PAR30 (%)
    ├→ [Filter: DPD ≥ 60] → PAR60 (%)
    ├→ [Filter: DPD ≥ 90] → PAR90 (%)
    ├→ [Filter: DPD ≥ 90 OR Status='defaulted'] → NPL-90 Proxy (%)
    └→ [Filter: DPD ≥ 180 OR Status='defaulted'] → NPL-180 Proxy (%)

NPL Ratio (Broad)
    ├→ Outstanding Balance [DPD ≥ 30 OR Status in ['delinquent','defaulted']]
    ├→ Source: engine.py:_calculate_derived_risk_kpis() → calculate_asset_quality_metrics()
    └→ Formula: SUM(balance WHERE dpd ≥ 30 OR delinquent/defaulted) / SUM(balance) * 100

NPL-90 Ratio (Strict)
    ├→ Outstanding Balance [DPD ≥ 90 OR Status='defaulted']
    ├→ Source: engine.py:_calculate_derived_risk_kpis() → npl_90_proxy alias
    └→ Formula: SUM(balance WHERE dpd ≥ 90 OR defaulted) / SUM(balance) * 100
```

### Risk Metrics

```
Default Risk Probability (XGBoost Model)
    ├→ Inputs: APR, DPD, Term, Line Utilization, LTV, Payment History
    ├→ Model: backend/loans_analytics/models/default_risk_model.py
    ├→ Output: Probability [0.0, 1.0]
    └→ Used for: Portfolio-level default expectation, stress testing

LTV Sintético (Synthetic Factoring LTV)
    ├→ Formula: Capital Desembolsado / (Valor Nominal Factura × (1 - Tasa Dilusión))
    ├→ Source: engine.py:_calculate_ltv_sintetico()
    ├→ Output: Portfolio mean + high-risk pct (LTV > 1.0)
    └→ Undefined when denominator = 0 → NaN (not silent 0)

Defaulted Outstanding Ratio
    ├→ Source: Status = 'defaulted' only (not DPD-based)
    ├→ Formula: SUM(balance WHERE status='defaulted') / SUM(balance) * 100
    └→ Subset of: NPL-90 Ratio
```

### Finance Metrics

```
Collection Efficiency (6M)
    ├→ Collected Payments (last 6m) / Scheduled Payments (last 6m) * 100
    ├→ Fallback: Disbursements (6m) if scheduled unavailable
    ├→ Source: strategic_modules.py:build_compliance_dashboard()
    └→ Used in: Compliance reporting, guardrail monitoring

DSCR (Debt Service Coverage Ratio)
    ├→ Source: formula_engine.py with registry lookup
    ├→ Threshold: Min 1.25x (CFO guardrail)
    └→ Components: NOI, Total Debt Service

Portfolio APR (Annual Percentage Rate)
    ├→ Weighted average: Σ(APR × Outstanding Balance) / Σ(Outstanding Balance)
    ├→ Owner: Head of Pricing
    └→ Target range: business_parameters.yml
```

### Concentration Metrics

```
Top-1 Borrower Concentration
    ├→ Max single obligor balance / Total active balance * 100
    ├→ Guardrail: ≤ 15% (per MAX_SINGLE_OBLIGOR_CONCENTRATION)
    └→ Source: engine.py:_top_10_borrower_concentration()

Top-10 Concentration
    ├→ Sum of top 10 obligor balances / Total active balance * 100
    ├→ Guardrail: ≤ 45% (per MAX_TOP_10_CONCENTRATION)
    └→ Source: engine.py:_top_10_borrower_concentration()
```

## Data Lineage: Loan Record Journey

```
CSV Input File
    ↓
[Ingestion] Validate schema, load into DataFrame
    ↓
[Transformation] 
    ├→ Normalize status (Spanish → English: "Moroso" → "delinquent")
    ├→ Fill nulls (smart strategy based on %)
    ├→ Detect/handle outliers (IQR)
    ├→ Convert currency (local → USD if needed)
    └→ Add opacity flags (_is_missing columns)
    ↓
[Calculation]
    ├→ Compute per-loan risk score (XGBoost default model)
    ├→ Compute per-loan LTV (synthético factoring)
    ├→ Aggregate by status (active, delinquent, defaulted)
    ├→ Compute portfolio-level asset quality (PAR, NPL)
    └→ Compute concentration (top-N borrowers)
    ↓
[Output]
    ├→ Write to kpi_values (Supabase)
    ├→ Write to historical context (temporal tracking)
    ├→ Export CSV for external reporting
    └→ Archive for audit trail
```

## External Data Dependencies

| Source | File(s) | Frequency | Used For |
|--------|---------|-----------|----------|
| **Raw CSV Input** | `data/samples/`, `--input` param | Ad-hoc | Loan principal data |
| **Config Rules** | `config/business_rules.yaml` | On deployment | Status mapping, outlier thresholds |
| **Financial Targets** | `config/business_parameters.yml` | Quarterly review | Guardrail comparisons |
| **KPI Registry** | `config/kpis/` | On KPI definition change | Formula authority |

## Backward Compatibility Notes

### Deprecations

1. **`backend/src/agents/multi_agent/__init__.py`** (Deprecated 2026-03)
   - Old import path: `from backend.src.agents.multi_agent import ...`
    - New import path: `from backend.loans_analytics.multi_agent import ...`
   - Removal target: Q2 2026
   - Status: Explicit imports with DeprecationWarning

2. **`backend/data-processor/`** (Deprecated 2026-01)
   - Use `src/pipeline/` (canonical) instead
   - Removal target: Q1 2026

### Formula Version History

| Metric | Version | Date | Change | Impact |
|--------|---------|------|--------|--------|
| PAR90 | 1.0 | 2025-12-01 | Initial (pure DPD≥90) | PSL baseline |
| PAR90 | 1.1 | 2026-01-15 | Added status='defaulted' | +0.3pp |
| PAR90 | 1.2 | 2026-03-20 | Reverted to pure DPD | -0.3pp (fix for test regression) |
| NPL Ratio | 1.0 | 2025-12-01 | DPD≥30 + delinquent/defaulted | Portfolio-level risk |

---

**For complete KPI definitions**, see `KPI.md`.  
**For ownership & change procedures**, see `KPI.md`.
