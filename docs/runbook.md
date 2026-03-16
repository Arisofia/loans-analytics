# Operational Runbook — Zero-Cost ETL Pipeline

> **Version:** 1.0 · **Date:** 2026-03-16  
> **Maintainer:** Abaco Loans Analytics team  
> **Branch:** `copilot/migrate-azure-to-free-architecture`

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Local Development Setup](#2-local-development-setup)
3. [Running the Pipeline Locally](#3-running-the-pipeline-locally)
4. [GitHub Actions CI/CD](#4-github-actions-cicd)
5. [Data Source Routing (loan_tape vs Control de Mora)](#5-data-source-routing)
6. [Crosswalk: loan_id ↔ operation_id](#6-crosswalk-loan_id--operation_id)
7. [DPD Calculation](#7-dpd-calculation)
8. [XIRR and APR Calculation](#8-xirr-and-apr-calculation)
9. [Exports](#9-exports)
10. [Required Secrets](#10-required-secrets)
11. [Troubleshooting](#11-troubleshooting)
12. [Rollback Procedure](#12-rollback-procedure)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                  Data Sources                             │
│                                                           │
│  loan_tape CSVs          Control-de-Mora CSVs             │
│  (≤ Jan 2026)            (≥ Feb 2026)                     │
└────────────────────────────────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │      PipelineRouter       │
         │  routes by snapshot month │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   LoanTapeLoader          │  ← loan_data, schedule,
         │   ControlMoraAdapter      │     real_payment, customer
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Crosswalk               │  ← loan_id ↔ operation_id
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   DPDCalculator           │  ← real DPD from base data
         │   MonthlySnapshotBuilder  │
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Exporter                │
         │   exports/*.csv           │
         │   exports/*.parquet       │
         └──────────────────────────┘
```

---

## 2. Local Development Setup

### Prerequisites

- Python 3.10+
- Docker (optional, for full stack)

### Install dependencies

```bash
# Create virtual environment
make setup

# Or manually:
pip install -r requirements.txt
pip install duckdb rapidfuzz pyarrow  # additional zero-cost deps
```

### Environment variables (non-secret, local only)

```bash
# Create .env (never commit this file)
cat > .env <<'EOF'
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
EOF
```

---

## 3. Running the Pipeline Locally

### Quick start

```bash
# Run all tests
make test

# Full pipeline (ingest + schema + snapshot)
make run

# Or step-by-step:
make etl-local INPUT=data/raw/control_mora_feb2026.csv
make zero-cost-schema
make snapshot-build MONTH=2026-02-28
```

### Loan tape ingestion (≤ Jan 2026)

```bash
make etl-local INPUT=data/raw/loan_data.csv
```

Place these files in `data/raw/`:
- `loan_data.csv` (or `loan_tape.csv`, `prestamos.csv`)
- `payment_schedule.csv` (or `schedule.csv`, `cronograma.csv`)
- `real_payment.csv` (or `payments.csv`, `pagos_reales.csv`)
- `customer.csv` (optional)
- `collateral.csv` (optional)

### Control-de-Mora ingestion (≥ Feb 2026)

```bash
make etl-local INPUT=data/raw/control_mora_feb2026.csv
make snapshot-build MONTH=2026-02-28
```

### Python API

```python
from src.zero_cost import PipelineRouter, Exporter, DPDCalculator

# Auto-selects correct source by month
router = PipelineRouter()
tables = router.route(
    snapshot_month="2026-02-28",
    loan_tape_dir="data/raw/",
    control_mora_path="data/raw/control_mora_feb2026.csv",
)

# Calculate DPD
calc = DPDCalculator()
snapshot = calc.build_snapshots(
    tables["dim_loan"],
    tables["fact_schedule"],
    tables["fact_real_payment"],
    month_ends=["2026-02-28"],
)

# Export
exporter = Exporter("exports/")
exporter.export_tables(tables)
exporter.export_snapshot(snapshot)
exporter.write_manifest(snapshot_month="2026-02-28")
```

---

## 4. GitHub Actions CI/CD

### Workflows

| Workflow | File | Trigger |
|----------|------|---------|
| ETL Pipeline | `etl-pipeline.yml` | Push, daily 06:00 UTC, monthly 08:00 UTC |
| Deploy (free tier) | `deploy-free-tier.yml` | Push to main, manual |
| Docs | `docs-deploy.yml` | Push to main |

### Cron schedule

| Schedule | Time (UTC) | Purpose |
|----------|------------|---------|
| `0 6 * * *` | Daily 06:00 | Loan tape ingest |
| `0 8 1 * *` | 1st of month 08:00 | Monthly snapshot |

### Manual trigger

```
GitHub → Actions → ETL Pipeline (Zero-Cost) → Run workflow
  ├── input_csv: data/raw/control_mora_feb2026.csv
  ├── mode: full
  ├── snapshot_month: 2026-02-28
  └── run_type: snapshot
```

### Artifacts uploaded per run

- `pipeline-output-{run_number}`: `data/processed/`, `exports/`, `logs/`
- `snapshot-{run_number}`: `data/duckdb/`, `exports/`

Retention: 30 days.

---

## 5. Data Source Routing

The `PipelineRouter` automatically selects the correct data source:

| Snapshot month | Source | Reason |
|---------------|--------|--------|
| ≤ January 2026 | `loan_tape` | Full loan-tape data available |
| ≥ February 2026 | `control_mora` | Control-de-Mora CSV is the primary source |

**Pivot date:** `2026-02-01` (configurable via `PipelineRouter(pivot_month=...)`)

```python
router = PipelineRouter()
print(router.source_for("2026-01-31"))  # "loan_tape"
print(router.source_for("2026-02-28"))  # "control_mora"
```

---

## 6. Crosswalk: loan_id ↔ operation_id

The `Crosswalk` class maps `loan_id` (loan tape) to `operation_id` (Control de Mora).

### Build crosswalk

```python
from src.zero_cost import Crosswalk

cw = Crosswalk(fuzzy_name_threshold=80, date_tolerance_days=7)
cw.build(loan_tape_df, control_mora_df)
cw.save("data/duckdb/crosswalk.parquet")
cw.export_unmatched("exports/unmatched_records.csv")
```

### Match types

| `match_type` | `reason_code` | Description |
|-------------|---------------|-------------|
| `exact` | `exact_key_match` | loan_id matched operation_id directly |
| `fuzzy` | `fuzzy_name_date_match` | Name similarity ≥ threshold AND date within tolerance |
| `unmatched` | `unmatched_loan_tape` | Loan tape loan with no match in Control de Mora |
| `unmatched` | `unmatched_control_mora` | Control-de-Mora record with no match in loan tape |

### Unmatched records

`exports/unmatched_records.csv` always exists (empty if all matched). The `reason_code` column is always non-empty.

---

## 7. DPD Calculation

Real DPD is calculated from base data, not from the DPD field in Control-de-Mora.

### Algorithm

```
For each (loan_id, reference_date):
  1. List all installments due ≤ reference_date
  2. Compute cumulative scheduled principal
  3. Compute cumulative paid principal ≤ reference_date
  4. Find first installment where cum_scheduled > cum_paid
  5. DPD = (reference_date - first_unpaid_date).days (0 if current)
```

### DPD buckets

| Bucket | DPD Range |
|--------|-----------|
| `current` | 0 days |
| `1-30` | 1–30 days |
| `31-60` | 31–60 days |
| `61-90` | 61–90 days |
| `91-180` | 91–180 days |
| `181-360` | 181–360 days |
| `360+` | > 360 days |

### PAR flags

| Flag | Condition |
|------|-----------|
| `par_1` | DPD ≥ 1 |
| `par_30` | DPD ≥ 30 |
| `par_60` | DPD ≥ 60 |
| `par_90` | DPD ≥ 90 |

---

## 8. XIRR and APR Calculation

### XIRR

```python
from src.zero_cost import xirr, loan_xirr, portfolio_xirr

# Standalone
rate = xirr([-10000, 3000, 3000, 5000], ["2025-01-01", "2025-07-01", "2026-01-01", "2026-07-01"])

# Per-loan
rate = loan_xirr(dim_loan_df, fact_real_payment_df, "L-001")

# All loans
rates_series = portfolio_xirr(dim_loan_df, fact_real_payment_df)
```

**Sign convention:** negative = outflows (disbursements), positive = inflows (payments).  
**Returns NaN** when XIRR cannot converge (no sign change, missing payments).  
This is equivalent to Excel's `#NUM!` error.

### Contractual APR

```python
from src.zero_cost import contractual_apr

# Convert 24% nominal monthly to Effective Annual Rate
ear = contractual_apr(0.24, payments_per_year=12)
# ear ≈ 0.2682 (26.82%)
```

### Edge cases

| Case | Behavior |
|------|----------|
| All cash flows same sign | `ValueError` raised |
| No payments recorded | Returns `float('nan')` |
| Irregular dates | Handled via fractional year calculation |
| No sign change in [−0.999, 10.0] | Bisection tries wider brackets; NaN if all fail |

---

## 9. Exports

All pipeline runs write to `exports/`:

| File | Format | Description |
|------|--------|-------------|
| `dim_loan.{csv,parquet}` | CSV + Parquet | Loan dimension table |
| `fact_schedule.{csv,parquet}` | CSV + Parquet | Scheduled payments |
| `fact_real_payment.{csv,parquet}` | CSV + Parquet | Actual payments |
| `fact_monthly_snapshot.{csv,parquet}` | CSV + Parquet | Monthly portfolio snapshot |
| `crosswalk.{csv,parquet}` | CSV + Parquet | loan_id ↔ operation_id mapping |
| `unmatched_records.csv` | CSV only | Unmatched loans with reason_code |
| `kpi_summary.{csv,parquet}` | CSV + Parquet | Executive KPI summary |
| `run_manifest.json` | JSON | File list + SHA-256 hashes + metadata |

The `exports/` directory is uploaded as a GitHub Actions artifact on every run.

---

## 10. Required Secrets

### Required (pipeline fails without these)

| Secret | Description | Where to get |
|--------|-------------|--------------|
| `SUPABASE_URL` | Supabase project URL | Supabase dashboard → Project settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Service-role key (write) | Supabase dashboard → Project settings → API |

### Required (by some pipeline steps)

| Secret | Description |
|--------|-------------|
| `SUPABASE_ANON_KEY` | Anon/public key (read) |

### Optional (deployment)

| Secret | Used by | Description |
|--------|---------|-------------|
| `RENDER_API_KEY` | deploy-free-tier.yml | Render.com API key |
| `RENDER_SERVICE_ID` | deploy-free-tier.yml | Render.com service ID |
| `RAILWAY_TOKEN` | deploy-free-tier.yml | Railway API token |
| `FLY_API_TOKEN` | deploy-free-tier.yml | Fly.io API token |

### Adding secrets

```
GitHub repository → Settings → Secrets and variables → Actions → New repository secret
```

> ⚠️ **Never commit secrets to the repository.**  
> The `preflight` job in `etl-pipeline.yml` will fail if required secrets are missing,
> preventing the pipeline from running with invalid credentials.

---

## 11. Troubleshooting

### Pipeline fails with "Missing required secrets"

Add the missing secrets in GitHub → Settings → Secrets. See [Required Secrets](#10-required-secrets).

### `unmatched_records.csv` has too many rows

1. Check that `loan_id` in loan tape matches `lend_id` or `numero_desembolso` in Control de Mora.
2. Lower `fuzzy_name_threshold` (default 80) to allow looser name matching.
3. Increase `date_tolerance_days` (default 7) if disbursement dates differ.

```python
from src.zero_cost import Crosswalk
cw = Crosswalk(fuzzy_name_threshold=70, date_tolerance_days=14)
```

### XIRR returns NaN for many loans

- Verify that `fact_real_payment` has at least one positive payment per loan.
- Ensure dates are parsed correctly (use `pd.to_datetime` with explicit format).
- Check for loans with zero disbursement amount.

### DuckDB schema init fails

```bash
# Check that the DDL file exists
ls db/star_schema/duckdb/create_star_schema_duckdb.sql

# Manually initialise
make zero-cost-schema

# Or with explicit path
python scripts/data/init_duckdb_schema.py --db data/duckdb/analytics.duckdb
```

### Column not found after CSV load

The adapters use column alias maps. If a new column name is encountered:

1. Add an entry to the relevant `_*_ALIASES` dict in `loan_tape_loader.py` or `control_mora_adapter.py`.
2. Fields with no alias are passed through unchanged.
3. Fields marked `"no especificado"` will have `reason_code` set automatically by the Crosswalk.

### Troubleshooting firewall / DNS blocks in GitHub Actions

GitHub Actions runners have full internet access by default, but some environments or security policies may block outbound DNS lookups or HTTPS connections. If the `test` or `run-pipeline` jobs fail with connection errors, timeouts, or `socket.gaierror`, follow these steps:

**Symptoms**

```
socket.gaierror: [Errno -2] Name or service not known
requests.exceptions.ConnectionError: HTTPSConnectionPool(host='...', port=443)
urllib3.exceptions.NewConnectionError: Failed to establish a new connection
```

**Diagnosis**

The most common causes are:

1. **Test code makes live network calls** — A test imports a module that eagerly connects to Supabase or an external API on import or fixture setup.
2. **DNS resolver is rate-limited or slow** — GitHub-hosted runners use shared DNS resolvers; transient failures are possible.
3. **Corporate runner / self-hosted runner with egress filtering** — If you use self-hosted runners behind a firewall, outbound HTTPS may be blocked.

**Fix A — Ensure tests are self-contained (recommended)**

All `src/zero_cost/` tests use local DataFrames only — no live network calls are made.  If you see DNS errors in the test job, verify that no new test imports a module that connects to Supabase at import time:

```bash
# Scan for suspicious imports in tests
grep -r "supabase\|requests\.get\|urllib.*open" tests/ --include="*.py"
```

If a live-call test is identified, either:
- Mock the network call with `unittest.mock.patch`, or
- Mark it `@pytest.mark.integration` and exclude it with `pytest -m "not integration"` (the current `Makefile` target already does this).

**Fix B — Add connection timeout to pytest (defensive)**

In `pytest.ini` or `conftest.py`:

```ini
# pytest.ini — add socket timeout so DNS failures surface quickly
[pytest]
timeout = 30
```

Install `pytest-timeout` and add it to `requirements.txt`:

```bash
pip install pytest-timeout
```

**Fix C — Self-hosted runner egress allow-list**

If you run on a self-hosted runner behind a firewall, ensure the following hostnames are reachable:

| Destination | Port | Purpose |
|-------------|------|---------|
| `pypi.org`, `files.pythonhosted.org` | 443 | `pip install` |
| `github.com`, `api.github.com` | 443 | Actions checkout, artifact upload |
| `*.supabase.co` | 443 | Supabase API (production pipeline only) |
| `objects.githubusercontent.com` | 443 | Actions cache |

**Fix D — Skip network-sensitive steps in dry-run mode**

The preflight job automatically switches to `dry-run` mode when the input CSV is absent.  In `dry-run` mode, no Supabase calls are made.  You can also force this manually:

```bash
# Trigger a dry-run via workflow_dispatch
gh workflow run etl-pipeline.yml -f mode=dry-run
```

**Artifact validation failures**

If the `Validate pipeline outputs` step fails with `rows in unmatched_records.csv have no reason_code`:

1. Check crosswalk output: `exports/unmatched_records.csv`
2. Each unmatched row must have a non-empty `reason_code` column explaining why it could not be matched.
3. Common reason codes: `no_match_found`, `ambiguous_match`, `date_out_of_range`.
4. Re-run with lower fuzzy threshold: `Crosswalk(fuzzy_name_threshold=70)`.

---

## 12. Rollback Procedure

> ⚠️ All Azure infrastructure remains **untouched**.  
> The zero-cost migration is **additive only** — no rollback is needed to restore Azure operations.

To disable the zero-cost workflows:

1. Go to GitHub → Actions → ETL Pipeline (Zero-Cost).
2. Click the "..." menu → **Disable workflow**.

To re-enable Azure workflows:

1. Go to GitHub → Actions → `deploy-multicloud.yml` (or relevant Azure workflow).
2. Click the "..." menu → **Enable workflow**.

Existing Azure credentials, `infra/`, `azure.yaml`, and all Azure-related code remain intact on the `main` branch.
