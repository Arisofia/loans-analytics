# KPI Catalog – Loans Analytics

This catalog defines the core KPIs implemented in:

- **Python**: `src/analytics/kpi_catalog_processor.py`
- **SQL**: Postgres views under schema `analytics`
- **Pipeline engine**: `src/pipeline/transformation.py` and `src/pipeline/calculation.py`
  All consumers (Next.js APIs, BI, Python, ML) should rely on these as the **single source of truth**.

---

## 1. Base Views

### 1.1 `analytics.customer_segment`

**Purpose**
Centralized customer segmentation:

- `sector_segment`: `Gob` vs `Private`
- `business_segment`: `OC`, `CCF`, `DTE`, `Nimal`, `Top`, `Other`
- `industry_segment`: macro industry buckets
  **Source**
- `public.customer_data`
  **Key Fields**
- `customer_id`
- `segment_source`
- `sector_segment`
- `business_segment`
- `industry_segment`
- `subcategoria_linea`
- `kam_id`

---

### 1.2 `analytics.loan_month`

**Purpose**
Monthly loan-level snapshot with:

- Outstanding principal at month-end
- Days past due (DPD)
- Pricing fields (APR, fees)
  **Source**
- `public.loan_data`
- `public.real_payment`
  **Key Fields**
- `month_end`
- `loan_id`
- `customer_id`
- `disbursement_date`
- `disbursement_amount`
- `interest_rate_apr`
- `origination_fee`
- `origination_fee_taxes`
- `outstanding`
- `days_past_due`

---

## 2. Pricing & Revenue KPIs

### 2.1 `analytics.kpi_monthly_pricing`

**Purpose**
Monthly portfolio pricing metrics:

- Weighted APR
- Weighted origination fee rate
- Weighted other income rate
- Weighted effective rate (all-in)
  **Source**
- `analytics.loan_month`
- `public.real_payment`
  **KPIs**
- `weighted_apr`
  - APR weighted by outstanding
- `weighted_fee_rate`
  - `(origination_fee + origination_fee_taxes) / disbursement_amount`, weighted by outstanding
- `weighted_other_income_rate`
  - `(fee + other + tax + fee_tax – rebates) / disbursement_amount`, weighted by outstanding
- `weighted_effective_rate`
  - `weighted_apr + weighted_fee_rate + weighted_other_income_rate`
    **Grain**
- One row per `year_month`

---

## 3. Risk & Delinquency KPIs

### 3.1 `analytics.kpi_monthly_risk`

**Purpose**
Global monthly delinquency KPIs.
**Source**

- `analytics.loan_month`
  **KPIs**
- `total_outstanding`
- `dpd7_amount`, `dpd7_pct`
- `dpd15_amount`, `dpd15_pct`
- `dpd30_amount`, `dpd30_pct`
- `dpd60_amount`, `dpd60_pct`
- `dpd90_amount`, `default_pct` (DPD ≥ 90)
  **Grain**
- One row per `year_month`

---

## 4. Pipeline KPI Engine Standards

### 4.1 Loan Event Identity Standard

**Purpose**
Avoid false duplicate alarms when business loan IDs are reused over time.

**Standard**
- `loan_uid` is generated as a composite event key:
  - `loan_uid = loan_id + "_" + YYYYMMDD(origination_date)`
- Referential integrity checks use `loan_uid` as primary key (fallback to `loan_id` only when `loan_uid` is unavailable).

**Implication**
- A reused business ID (for example `LN-100` in different years) is treated as separate lending events.

### 4.2 KPI Grain Rules (Pipeline)

**Default grain**
- Payment/loan tape rows from transformed data.

**Unique-loan grain KPIs**
- The calculation engine applies unique-loan grain (dedupe by `loan_uid`, fallback `loan_id`) for:
  - `total_loans_count`
  - `average_loan_size`

**Tape-grain KPIs**
- All other KPIs keep tape-grain behavior unless explicitly overridden in code or definitions.

### 4.3 Additional Portfolio Risk KPIs (Pipeline)

These are calculated in `src/pipeline/calculation.py` and emitted with the KPI output:

- `npl_90_ratio` (%):
  - `(SUM(outstanding_balance WHERE dpd >= 90 OR status = 'defaulted') / SUM(outstanding_balance WHERE status IN ['active','defaulted'])) * 100`
- `defaulted_outstanding_ratio` (%):
  - `(SUM(outstanding_balance WHERE status = 'defaulted') / SUM(outstanding_balance WHERE status IN ['active','defaulted'])) * 100`
- `top_10_borrower_concentration` (%):
  - `(SUM(outstanding_balance of top 10 borrowers by outstanding in active/defaulted portfolio) / SUM(outstanding_balance WHERE status IN ['active','defaulted'])) * 100`

---

## 5. Executive Dashboard & Summary

### 5.1 `public.executive_dashboard`

**Purpose**
Consolidated view for board and investor reporting.
**Metrics Definition**

- **Ingresos mensuales (Revenue)**: `True Interest Payment + True Fee Payment + True Other Payment - True Rebates`. Excludes Principal and Taxes.
- **Sales (Ventas)**: Total monthly disbursements (`Disbursement Amount`).
- **Recurrence (%)**: `Interest / Ingresos`.
- **Clients EOP**: Cumulative unique customers with at least one disbursement.
- **Throughput 12M**: Sum of `True Principal Payment` in the last 12 months.
- **Rotation**: `Throughput 12M / Current AUM`.
- **APR Realized**: `LTM Interest / Avg AUM LTM`.
- **Yield incl. Fees**: `LTM Revenue / Avg AUM LTM`.
- **SAM Penetration**: `Throughput 12M / USD 0.9B`.
- **CAC**: `Commercial Expense / New Clients`.
- **LTV Realized**: `Cumulative Revenue / Cumulative Unique Customers`.
  **Source**
- `public.analytics_facts` (CSV Import)
- `src/analytics/kpi_catalog_processor.py`
