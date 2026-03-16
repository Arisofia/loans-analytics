# Data Model — Zero-Cost Star Schema

> **Version:** 1.0 · **Date:** 2026-03-16
> **Target databases:** Supabase (PostgreSQL free tier) · DuckDB (local / offline)

---

## Overview

The Abaco Loans Analytics data model follows a **star schema** optimised for
monthly portfolio reporting, mora (delinquency) analysis, and KPI aggregations.

```
              ┌─────────────┐
              │  dim_client │
              └──────┬──────┘
                     │
┌──────────┐   ┌─────▼────────────────────────┐   ┌──────────┐
│ dim_time │───►  fact_monthly_snapshot        │◄───│ dim_loan │
└──────────┘   │  fact_disbursement            │   └──────────┘
               │  fact_payment                 │
               └───────────────────────────────┘
```

---

## Dimension Tables

### `dim_time`

Calendar dimension.  One row per month-end snapshot date.

| Column | Type | Description |
|--------|------|-------------|
| `time_id` | PK | Surrogate key |
| `snapshot_month` | DATE | Month-end date (e.g., `2026-01-31`) |
| `year` | SMALLINT | Year |
| `month` | SMALLINT | Month (1–12) |
| `quarter` | SMALLINT | Quarter (1–4) |
| `year_month` | CHAR(7) | `YYYY-MM` string for grouping |

---

### `dim_client`

Borrower/client master data.

| Column | Type | Description |
|--------|------|-------------|
| `client_sk` | PK | Surrogate key |
| `client_id` | VARCHAR | Business client identifier |
| `client_name` | VARCHAR | Full name |
| `identity_number` | VARCHAR | National ID / cedula |
| `created_at` | TIMESTAMPTZ | Record creation timestamp |

---

### `dim_loan`

Loan master attributes (SCD Type 1 — overwrites on change).

| Column | Type | Description |
|--------|------|-------------|
| `loan_sk` | PK | Surrogate key |
| `lend_id` | VARCHAR | Unified pipeline loan identifier |
| `numero_desembolso` | VARCHAR | Legacy Control-de-Mora identifier |
| `client_sk` | FK → dim_client | Client reference |
| `product_type` | VARCHAR | Loan product (e.g., `microcredito`) |
| `branch_code` | VARCHAR | Branch / agencia |
| `currency` | CHAR(3) | ISO currency code (default `USD`) |
| `disbursement_date` | DATE | Original disbursement date |
| `maturity_date` | DATE | Scheduled maturity date |
| `original_principal` | NUMERIC(18,4) | Original loan amount |
| `interest_rate` | NUMERIC(8,6) | Annual interest rate |
| `term_months` | SMALLINT | Loan term in months |

> **lend_id ↔ NumeroDesembolso mapping:**  
> The `LendIdMapper` class in `src/zero_cost/lend_id_mapper.py` builds and
> persists this bidirectional mapping from Control-de-Mora CSV exports.

---

## Fact Tables

### `fact_disbursement`

One row per disbursement event.

| Column | Type | Description |
|--------|------|-------------|
| `disbursement_sk` | PK | Surrogate key |
| `loan_sk` | FK → dim_loan | Loan reference |
| `client_sk` | FK → dim_client | Client reference |
| `time_id` | FK → dim_time | Time reference |
| `disbursement_date` | DATE | Actual disbursement date |
| `principal_amount` | NUMERIC(18,4) | Disbursed amount |
| `currency` | CHAR(3) | Currency |
| `channel` | VARCHAR | Disbursement channel |
| `product_type` | VARCHAR | Product type |
| `branch_code` | VARCHAR | Branch code |

---

### `fact_payment`

One row per payment received.

| Column | Type | Description |
|--------|------|-------------|
| `payment_sk` | PK | Surrogate key |
| `loan_sk` | FK → dim_loan | Loan reference |
| `client_sk` | FK → dim_client | Client reference |
| `time_id` | FK → dim_time | Payment month reference |
| `payment_date` | DATE | Actual payment date |
| `principal_paid` | NUMERIC(18,4) | Principal component |
| `interest_paid` | NUMERIC(18,4) | Interest component |
| `fees_paid` | NUMERIC(18,4) | Fee component |
| `total_paid` | NUMERIC(18,4) | Sum of all components |
| `currency` | CHAR(3) | Currency |
| `payment_method` | VARCHAR | e.g., `cash`, `transfer` |

---

### `fact_monthly_snapshot`

**Primary reporting fact table.**  One row per (loan × month).  Captures the
portfolio state at each month-end for mora and KPI reporting.

| Column | Type | Description |
|--------|------|-------------|
| `snapshot_sk` | PK | Surrogate key |
| `loan_sk` | FK → dim_loan | Loan reference |
| `client_sk` | FK → dim_client | Client reference |
| `time_id` | FK → dim_time | Month reference |
| `snapshot_month` | DATE | Month-end date |
| `principal_outstanding` | NUMERIC(18,4) | Outstanding principal balance |
| `total_overdue_amount` | NUMERIC(18,4) | Total overdue (capital + interest) |
| `interest_outstanding` | NUMERIC(18,4) | Accrued unpaid interest |
| `fees_outstanding` | NUMERIC(18,4) | Accrued unpaid fees |
| `dpd` | SMALLINT | Days Past Due |
| `mora_bucket` | VARCHAR(16) | Bucket: `current`, `1-30`, `31-60`, `61-90`, `91-180`, `181-360`, `360+` |
| `is_overdue` | BOOLEAN | `dpd > 0` |
| `par_1` | BOOLEAN | `dpd >= 1` |
| `par_30` | BOOLEAN | `dpd >= 30` |
| `par_60` | BOOLEAN | `dpd >= 60` |
| `par_90` | BOOLEAN | `dpd >= 90` |
| `months_on_book` | SMALLINT | Months since disbursement |
| `monthly_income` | NUMERIC(18,4) | Payments received in this month |
| `source` | VARCHAR | Data source (`control_mora`, `pipeline`) |

---

## KPI Views

All views are defined in `db/star_schema/views/kpi_views.sql` and work with
both PostgreSQL (Supabase) and DuckDB.

| View | Description |
|------|-------------|
| `v_monthly_disbursements` | New loans and disbursed amounts per month |
| `v_monthly_outstanding_balance` | Active portfolio balance at month-end |
| `v_monthly_mora` | DPD bucket breakdown per month |
| `v_par_monthly` | PAR 1/30/60/90 percentages per month |
| `v_monthly_income` | Collections (principal, interest, fees) per month |
| `v_monthly_apr_proxy` | Annualised Percentage Return proxy |
| `v_kpi_summary` | One-row-per-month executive dashboard KPI summary |

---

## DPD Bucket Classification

| Bucket | DPD Range |
|--------|-----------|
| `current` | 0 days |
| `1-30` | 1–30 days |
| `31-60` | 31–60 days |
| `61-90` | 61–90 days |
| `91-180` | 91–180 days |
| `181-360` | 181–360 days |
| `360+` | > 360 days |

---

## Local Usage (DuckDB)

```bash
# 1. Initialise star schema
make zero-cost-schema

# 2. Build monthly snapshot from Control-de-Mora CSV
make snapshot-build INPUT=data/raw/control_mora_ene2026.csv MONTH=2026-01-31

# 3. Query with DuckDB CLI or Python
python - <<'EOF'
import duckdb
con = duckdb.connect("data/duckdb/analytics.duckdb")
print(con.execute("SELECT * FROM v_kpi_summary").df())
EOF
```

---

## Supabase (PostgreSQL) Usage

```bash
# Apply schema to Supabase
psql "$SUPABASE_DB_URL" -f db/star_schema/create_star_schema.sql
psql "$SUPABASE_DB_URL" -f db/star_schema/views/kpi_views.sql
```

---

## Source Files

| File | Purpose |
|------|---------|
| `db/star_schema/create_star_schema.sql` | PostgreSQL DDL |
| `db/star_schema/duckdb/create_star_schema_duckdb.sql` | DuckDB DDL |
| `db/star_schema/views/kpi_views.sql` | KPI views (both dialects) |
| `src/zero_cost/storage.py` | DuckDB + Parquet storage backend |
| `src/zero_cost/lend_id_mapper.py` | lend_id ↔ NumeroDesembolso mapping |
| `src/zero_cost/control_mora_adapter.py` | Control-de-Mora CSV adapter |
| `src/zero_cost/monthly_snapshot.py` | Monthly snapshot builder |
| `src/zero_cost/fuzzy_matcher.py` | Fuzzy income ↔ disbursement matching |
| `scripts/data/init_duckdb_schema.py` | Schema initialisation script |
| `scripts/data/build_snapshot.py` | Snapshot build script |
