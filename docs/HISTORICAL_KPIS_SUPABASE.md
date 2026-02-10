# Historical KPIs Supabase Integration (Phase G4.2.1)

## Overview

This document describes the production data contract for **historical KPI time-series data** in Supabase and the configuration required to run REAL mode in Phase G4.2.1.

**Key Features:**

- Daily granularity (extensible to hourly)
- Multi-tenant / multi-product support
- Efficient time-range queries by KPI and date
- Full backward compatibility with G4.1 MOCK mode

---

## Database Schema

### Table: `public.historical_kpis`

**Purpose:** Store daily KPI observations with business context and audit metadata.

**Grain:** One row per `(kpi_id, portfolio_id, product_code, segment_code, date)` combination.

#### Columns

| Column          | Type            | Null | Default | Description                                           |
| --------------- | --------------- | ---- | ------- | ----------------------------------------------------- |
| `id`            | `bigserial`     | NO   | Auto    | Primary key                                           |
| `kpi_id`        | `text`          | NO   | —       | KPI identifier (e.g., "npl_ratio", "cost_of_risk")    |
| `portfolio_id`  | `text`          | YES  | NULL    | Portfolio segment (e.g., "retail", "sme", "mortgage") |
| `product_code`  | `text`          | YES  | NULL    | Product code (e.g., "PLN", "CC", "MTG")               |
| `segment_code`  | `text`          | YES  | NULL    | Customer segment (e.g., "mass", "affluent", "micro")  |
| `date`          | `date`          | NO   | —       | KPI observation date (daily)                          |
| `ts_utc`        | `timestamptz`   | NO   | `now()` | Data ingestion timestamp (UTC)                        |
| `value_numeric` | `numeric(18,6)` | YES  | NULL    | Main numeric KPI value (6 decimal places)             |
| `value_int`     | `bigint`        | YES  | NULL    | Optional integer count (e.g., loan count)             |
| `value_json`    | `jsonb`         | YES  | NULL    | Optional structured data (e.g., percentiles)          |
| `source_system` | `text`          | YES  | NULL    | Data origin (e.g., "data_warehouse", "simulation")    |
| `run_id`        | `text`          | YES  | NULL    | ETL run identifier for traceability                   |
| `is_final`      | `boolean`       | NO   | `true`  | Whether this is final/published (vs. preliminary)     |
| `created_at`    | `timestamptz`   | NO   | `now()` | Row creation timestamp                                |
| `updated_at`    | `timestamptz`   | NO   | `now()` | Row last update timestamp                             |

#### Indexes

| Index Name                | Columns                | Purpose                                                 |
| ------------------------- | ---------------------- | ------------------------------------------------------- |
| `idx_hkpi_kpi_date`       | `(kpi_id, date)`       | **Primary access pattern:** Query by KPI and date range |
| `idx_hkpi_portfolio_date` | `(portfolio_id, date)` | Filter by portfolio + date                              |
| `idx_hkpi_product_date`   | `(product_code, date)` | Filter by product + date                                |

#### Optional Uniqueness Constraint

To enforce one value per day per dimension:

```sql
create unique index ux_hkpi_kpi_portfolio_product_segment_date
    on public.historical_kpis (kpi_id, portfolio_id, product_code, segment_code, date);
```

---

## Data Contract (Python)

### Query Response Format

When HistoricalContextProvider loads REAL mode data, each record maps to this structure:

```python
{
    "kpi_id": str,              # e.g., "npl_ratio"
    "date": datetime.date,      # e.g., date(2025, 12, 31)
    "value": float,             # e.g., 0.0345
    "portfolio_id": str | None, # e.g., "retail"
    "product_code": str | None, # e.g., "PLN"
    "segment_code": str | None, # e.g., "mass"
}
```

### Field Mappings

| Python Key     | Supabase Column | Transformation                   |
| -------------- | --------------- | -------------------------------- |
| `kpi_id`       | `kpi_id`        | Direct                           |
| `date`         | `date`          | Direct                           |
| `value`        | `value_numeric` | `float()` conversion; NULL → 0.0 |
| `portfolio_id` | `portfolio_id`  | Direct                           |
| `product_code` | `product_code`  | Direct                           |
| `segment_code` | `segment_code`  | Direct                           |

---

## Setup Instructions

### 1. Create the Table

Apply the migration via Supabase SQL editor or CLI:

```bash
# Using Supabase CLI
supabase db push

# Or manually in Supabase SQL editor:
```

```sql
\i db/migrations/20260201_create_historical_kpis.sql
```

Or copy-paste the DDL from [db/migrations/20260201_create_historical_kpis.sql](../../db/migrations/20260201_create_historical_kpis.sql).

### 2. Enable RLS (Optional)

For multi-tenant isolation:

```sql
alter table public.historical_kpis enable row level security;

-- Create policies as needed (e.g., tenant-based filtering)
```

### 3. Configure Environment Variables

Set these in your environment, `.env`, or GitHub Actions secrets:

```bash
# Supabase connection
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key-here"

# Optional: Table name (defaults to "historical_kpis")
export SUPABASE_HISTORICAL_KPI_TABLE="historical_kpis"

# Mode selection (local dev: MOCK; production: REAL)
export HISTORICAL_CONTEXT_MODE="REAL"
```

**For development/testing:** Leave `HISTORICAL_CONTEXT_MODE` unset or set to `MOCK`. This uses synthetic data and requires no Supabase access.

**For production:** Set `HISTORICAL_CONTEXT_MODE=REAL` and provide valid Supabase credentials.

---

## Data Loading

### Sample Data Loader

```python
import os
from datetime import date, timedelta
import requests

def load_sample_kpis():
    """Load sample KPI data for testing."""
    url = f"{os.getenv('SUPABASE_URL')}/rest/v1/historical_kpis"
    headers = {
        "apikey": os.getenv("SUPABASE_ANON_KEY"),
        "Authorization": f"Bearer {os.getenv('SUPABASE_ANON_KEY')}",
        "Content-Type": "application/json",
    }

    payload = [
        {
            "kpi_id": "npl_ratio",
            "portfolio_id": "retail",
            "product_code": "PLN",
            "segment_code": "mass",
            "date": (date.today() - timedelta(days=i)).isoformat(),
            "value_numeric": 0.025 + (0.001 * i),
            "source_system": "data_warehouse",
            "is_final": True,
        }
        for i in range(90)  # 90 days of data
    ]

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    print(f"Loaded {len(payload)} rows")

if __name__ == "__main__":
    load_sample_kpis()
```

---

## Python Usage

### MOCK Mode (Default, No Supabase)

```python
from python.multi_agent.historical_context import HistoricalContextProvider

# Default MOCK mode: synthetic data, no Supabase needed
provider = HistoricalContextProvider()

# Works exactly as G4.1
history = provider._load_historical_data(
    kpi_id="npl_ratio",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 3, 1),
)
```

### REAL Mode (Supabase Backend)

```python
from python.multi_agent.historical_context import HistoricalContextProvider
from python.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend

# REAL mode: Supabase backend
backend = SupabaseHistoricalBackend()  # Reads SUPABASE_URL, SUPABASE_ANON_KEY
provider = HistoricalContextProvider(mode="REAL", backend=backend)

# Queries historical_kpis table
history = provider._load_historical_data(
    kpi_id="npl_ratio",
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 3, 1),
)
```

### Mode Selection

```python
import os

# Environment-based mode selection
mode = os.getenv("HISTORICAL_CONTEXT_MODE", "MOCK").upper()

if mode == "REAL":
    backend = SupabaseHistoricalBackend()
    provider = HistoricalContextProvider(mode="REAL", backend=backend)
else:
    provider = HistoricalContextProvider()  # MOCK mode (default)
```

---

## Integration Tests

### Run Tests Locally

**Unit tests only (no Supabase):**

```bash
pytest python/multi_agent/test_historical_context.py -q
```

**Integration tests (requires Supabase credentials):**

```bash
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-key"

pytest -m integration_supabase -v
```

### GitHub Actions

A dedicated workflow runs integration tests on-demand or nightly:

```bash
# Manual trigger via GitHub UI
# Or nightly at 03:00 UTC (see .github/workflows/historical_supabase_integration.yml)
```

Tests automatically skip if `SUPABASE_URL` and `SUPABASE_ANON_KEY` secrets are not configured.

---

## Backward Compatibility

✅ **G4.1 is fully preserved:**

- MOCK mode (default) remains the only active mode for unit tests
- All 38 existing multi-agent tests continue to pass unchanged
- No breaking changes to HistoricalContextProvider API
- REAL mode is opt-in via environment variable or constructor parameter

✅ **G4.2 REAL mode is additive:**

- New SupabaseHistoricalBackend class (separate module)
- New integration test file (isolated, opt-in marker)
- No modifications to existing G4.1 code paths

---

## Troubleshooting

### "Unable to find reusable workflow" (VS Code)

This is a VS Code GitHub Actions extension limitation, not a real issue. The workflow will run correctly in GitHub Actions.

### Supabase connection timeout

Check that:

- `SUPABASE_URL` is correct and accessible
- `SUPABASE_ANON_KEY` is valid
- Network/firewall allows outbound HTTPS to Supabase
- Table `historical_kpis` exists and is accessible

### "No rows returned in REAL mode"

This is expected if the table is empty. Load sample data or ensure your ETL pipeline has populated the table.

### Integration tests skip automatically

If you see "skipped" instead of running tests, Supabase credentials are not configured. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` to enable them.

---

## Next Steps

1. **Create the table:** Run `supabase db push` or apply the migration SQL
2. **Load sample data:** Use the data loader script or your ETL pipeline
3. **Set environment variables:** Configure SUPABASE\_\* in your deployment
4. **Run integration tests:** `pytest -m integration_supabase` to validate
5. **Deploy:** Enable `HISTORICAL_CONTEXT_MODE=REAL` in production when ready

---

## References

- [Phase G4.2 Implementation](../../docs/phase-g4.2-real-data-integration.md)
- [Supabase PostgREST API](https://postgrest.org/)
- [Historical Context Provider](../multi_agent/historical_context.py)
- [Supabase Backend Implementation](../multi_agent/historical_backend_supabase.py)
