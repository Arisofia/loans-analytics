# Figma KPI Coverage Report

**Generated:** 2025-12-21  
**Figma Project:** [Create Dark Editable Slides](https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/Create-Dark-Editable-Slides?node-id=0-1&t=8coqxRUeoQvNvavm-1)  
**Verification Tool:** `scripts/verify_figma_kpi_coverage.py`

---

## Executive Summary

- **Total KPIs Defined:** 8
- **Fully Covered (repo → export → Figma):** 2/8 (25%)
- **Analytics Engine Coverage:** 7/8 (87.5%)
- **Streamlit Export Coverage:** 3/8 (37.5%)
- **Web Display Coverage:** 5/8 (62.5%)

**Status:** ⚠️ **75% of KPIs need updates to be visible in Figma**

---

## KPI Coverage Details

### ✅ FULLY COVERED (2 KPIs)

These KPIs are computed, exported, displayed, and ready for Figma:

| KPI | Category | Status | Location in Code |
|-----|----------|--------|------------------|
| **Portfolio Delinquency Rate** | Risk | ✅ Complete | engine.py, streamlit_app.py, PortfolioHealthKPIs.tsx |
| **Portfolio Yield** | Finance | ✅ Complete | engine.py, streamlit_app.py, PortfolioHealthKPIs.tsx |

---

### ⚠️ PARTIALLY COVERED (4 KPIs)

These KPIs are computed and displayed but **missing from Streamlit export** (won't reach Figma):

#### 1. **Average LTV Ratio** (Risk)
- **Status:** ❌ Not in streamlit export
- **Computed in:** enterprise_analytics_engine.py (✅)
- **Displayed in:** PortfolioHealthKPIs.tsx (✅)
- **Exported to:** ❌ Missing
- **Fix:** Add `ltv_ratio` to fact_table export in streamlit_app.py (line 396-407)

#### 2. **Average DTI Ratio** (Risk)
- **Status:** ❌ Not in streamlit export
- **Computed in:** enterprise_analytics_engine.py (✅)
- **Displayed in:** PortfolioHealthKPIs.tsx (✅)
- **Exported to:** ❌ Missing
- **Fix:** Add `dti_ratio` to fact_table export in streamlit_app.py (line 396-407)

#### 3. **Data Quality Score** (Compliance)
- **Status:** ❌ Not in streamlit export
- **Computed in:** enterprise_analytics_engine.py (✅)
- **Displayed in:** ❌ Missing from web component
- **Exported to:** ❌ Missing
- **Fix:** 
  - Add computation to streamlit_app.py
  - Add display to PortfolioHealthKPIs.tsx
  - Include in fact_table export

#### 4. **Average Null Ratio** (Compliance)
- **Status:** ❌ Not exported
- **Computed in:** enterprise_analytics_engine.py (✅)
- **Displayed in:** ❌ Missing from web component
- **Exported to:** ❌ Missing
- **Fix:** 
  - Add to streamlit dashboard display
  - Include in fact_table export

---

### ❌ NOT COVERED (2 KPIs)

These KPIs are missing or partially implemented:

#### 5. **Invalid Numeric Ratio** (Compliance)
- **Status:** ❌ Partially computed
- **Computed in:** enterprise_analytics_engine.py (✅)
- **Displayed in:** ❌ Missing from web component
- **Exported to:** ❌ Missing
- **Fix:** 
  - Add to streamlit dashboard
  - Add to PortfolioHealthKPIs.tsx
  - Include in fact_table export

#### 6. **Active Loans Count** (Traction)
- **Status:** ⚠️ Computed differently in web vs engine
- **Computed in:** PortfolioHealthKPIs.tsx (from props) vs enterprise_analytics_engine.py
- **Displayed in:** PortfolioHealthKPIs.tsx (✅)
- **Exported to:** ❌ Missing from streamlit
- **Fix:** 
  - Add `len(loan_df)` to fact_table export
  - Standardize computation across components

---

## Figma Section Mapping

| Section | Expected KPIs | Status | Coverage |
|---------|---------------|--------|----------|
| **Traction** | Active Loans Count | ⚠️ Partial | 0/1 (0%) - missing export |
| **Risk** | Delinquency Rate, LTV, DTI | ⚠️ Partial | 1/3 (33%) - 2 missing export |
| **Finance** | Portfolio Yield | ✅ Complete | 1/1 (100%) |
| **Compliance** | Quality Score, Null Ratio, Invalid Ratio | ❌ Missing | 0/3 (0%) |

---

## Data Export Pipeline

### Current Exports (streamlit_app.py, lines 396-414)

```python
fact_table = loan_df[
    ["loan_amount", "principal_balance", "interest_rate", "loan_status", 
     "ltv_ratio", "dti_ratio", "delinquency_rate"]
].copy()
```

**Missing from export:**
- `data_quality_score` ❌
- `average_null_ratio_percent` ❌
- `invalid_numeric_ratio_percent` ❌
- Active loan count (scalar, not series) ❌

### Recommended Fix

Expand fact_table to include all KPI columns:

```python
fact_table = loan_df[
    ["loan_amount", "principal_balance", "interest_rate", "loan_status", 
     "ltv_ratio", "dti_ratio", "delinquency_rate"]
].copy()

metrics = engine.run_full_analysis()
fact_table["data_quality_score"] = metrics["data_quality_score"]
fact_table["average_null_ratio_percent"] = metrics["average_null_ratio_percent"]
fact_table["invalid_numeric_ratio_percent"] = metrics["invalid_numeric_ratio_percent"]
fact_table["active_loans"] = len(loan_df)
```

---

## Step-by-Step Fix Plan

### Phase 1: Update Streamlit Export (HIGH PRIORITY)
**Location:** `streamlit_app.py` lines 351-414

1. Compute quality metrics from enterprise_analytics_engine
2. Add columns to fact_table for:
   - `data_quality_score`
   - `average_null_ratio_percent`
   - `invalid_numeric_ratio_percent`
   - `active_loans_count`
3. Re-run verification script to confirm

### Phase 2: Update Web Display (MEDIUM PRIORITY)
**Location:** `PortfolioHealthKPIs.tsx` lines 10-17

Add missing metrics to metricSet:
- Data Quality Score
- Average Null Ratio
- Invalid Numeric Ratio

### Phase 3: Verify Figma Integration (HIGH PRIORITY)
**Location:** Figma project (manual review)

1. Check if data columns are correctly mapped in Figma tables
2. Verify each KPI appears in correct section:
   - Traction: Active Loans Count
   - Risk: Delinquency Rate, LTV, DTI
   - Finance: Portfolio Yield
   - Compliance: Quality Metrics
3. Validate thresholds and conditional formatting

---

## Verification Commands

Run these commands to verify coverage:

```bash
python3 scripts/verify_figma_kpi_coverage.py
```

Expected output after fixes:
```
✅ ALL KPIs ARE PROPERLY COVERED AND READY FOR FIGMA
8/8 KPIs (100.0%) fully covered
```

---

## Quick Reference: What Each Export Contains

| File | Type | KPIs | Purpose |
|------|------|------|---------|
| `abaco_fact_table.csv` | CSV | 6/8 | Raw data for Figma data binding (currently missing Quality metrics) |
| `growth-path.html` | Plotly | 1 | Visual for Portfolio Yield projection |
| `sales-treemap.html` | Plotly | 0 | Segment visualization (bonus content) |
| `presentation-summary.md` | Markdown | 2 | Narrative context for Figma captions |

---

## Notes

- **KPI Mapping Source:** `data_samples/kpi_mapping.json`
- **Verification Script:** `scripts/verify_figma_kpi_coverage.py`
- **Next Steps:** Run Phase 1 fixes, re-run verification, then update Figma manually
- **Owner Responsibility:** Jenine should verify Figma updates after data export fixes
- **Figma Link:** https://www.figma.com/make/nuVKwuPuLS7VmLFvqzOX1G/Create-Dark-Editable-Slides

---

## Appendix: KPI Definitions

### Risk KPIs
- **Delinquency Rate:** % of portfolio 30+ days past due
- **LTV Ratio:** Loan-to-value, indicates borrower equity
- **DTI Ratio:** Debt-to-income, indicates borrower capacity

### Finance KPIs
- **Portfolio Yield:** Weighted avg interest rate across portfolio

### Traction KPIs
- **Active Loans:** Total number of loans in portfolio

### Compliance KPIs
- **Data Quality Score:** Overall data completeness (0-100%)
- **Null Ratio:** % of missing values
- **Invalid Numeric Ratio:** % of fields failing numeric validation
