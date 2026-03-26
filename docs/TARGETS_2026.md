# 2026 Portfolio Targets Integration Guide

## Overview

The system now tracks **2026 portfolio growth targets** ($8.5M → $12M) against actual performance, enabling monthly variance analysis and automatic risk alerts.

## 2026 Target Plan

| Month | Target | Growth | Status |
|-------|--------|--------|--------|
| Jan | $8,500,000 | — | Foundation |
| Feb | $9,000,000 | +$500K (+5.9%) | Ramp-up |
| Mar | $9,300,000 | +$300K (+3.3%) | Steady |
| Apr | $9,600,000 | +$300K (+3.2%) | Steady |
| May | $9,900,000 | +$300K (+3.1%) | Steady |
| Jun | $10,200,000 | +$300K (+3.0%) | Steady |
| Jul | $10,500,000 | +$300K (+2.9%) | Steady |
| Aug | $10,800,000 | +$300K (+2.9%) | Steady |
| Sep | $11,100,000 | +$300K (+2.8%) | Steady |
| Oct | $11,400,000 | +$300K (+2.7%) | Steady |
| Nov | $11,700,000 | +$300K (+2.6%) | Steady |
| Dec | $12,000,000 | +$300K (+2.6%) | Full Year Target |

**Total Growth:** +$3.5M (+41.2% YoY)  
**Average Monthly Growth:** +$291K

---

## System Components

### 1. Target Loader (`backend/python/kpis/target_loader.py`)

Python class for target management with built-in variance calculation:

```python
from backend.python.kpis.target_loader import TargetLoader, get_2026_targets

# Get hardcoded 2026 targets
targets = get_2026_targets()
print(targets["Dec"])  # 12000000

# Create loader instance
loader = TargetLoader()

# Get specific month target
jan_target = loader.get_target(1)  # or loader.get_target("Jan")
print(jan_target)  # Decimal('8500000')

# Calculate variance
actual = Decimal("8700000")
variance = loader.calculate_variance(actual, jan_target)
# → {
#     "variance_amount": Decimal('200000'),
#     "variance_pct": Decimal('2.35'),
#     "status": "ON_TRACK"
#   }

# Load from Google Sheets DataFrame
df = pd.read_csv("TARGETS_2026.csv")
targets_loaded = loader.load_from_dataframe(df)

# Export targets as table
targets_df = loader.export_targets_table()

# Compare actuals vs targets
actuals = {
    "Jan": Decimal("8700000"),
    "Feb": Decimal("9200000"),
    "Mar": Decimal("9400000"),
}
comparison = loader.compare_actuals_vs_targets(actuals)
print(comparison.to_string())
```

### 2. Database Schema (`db/migrations/20260324094000_create_kpi_targets_table.sql`)

**Table:** `kpi_targets_2026`

| Column | Type | Purpose |
|--------|------|---------|
| `id` | BIGSERIAL | Primary key |
| `month_number` | INT | 1-12 |
| `month_name` | VARCHAR(3) | Jan-Dec |
| `portfolio_target` | NUMERIC(15,2) | USD target |
| `npl_target_pct` | NUMERIC(5,2) | NPL ratio target |
| `default_rate_target_pct` | NUMERIC(5,2) | Default rate target |
| `created_at` | TIMESTAMP | Record creation |
| `updated_at` | TIMESTAMP | Last update |

**View:** `kpi_targets_with_variance`
- Joins actual KPI values with targets
- Calculates variance_amount and variance_pct
- Assigns status: ON_TRACK | AT_RISK | MONITOR

**Pre-seeded data:** All 12 months (Jan-Dec) with $8.5M-$12M targets

---

## Using Targets in the Pipeline

### 1. Load Targets from Google Sheets

Create TARGETS_2026 tab in your spreadsheet with:
```
Month              | Portfolio_Target | NPL_Target | Default_Rate_Target
Jan                | 8500000          | 2.5        | 1.2
Feb                | 9000000          | 2.4        | 1.1
...
Dec                | 12000000         | 1.8        | 0.5
```

### 2. Configure Pipeline

Already enabled in `config/pipeline.yml`:
```yaml
targets:
  enabled: true
  source: "google_sheets"
  worksheet: "TARGETS_2026"
  persist_to_database: true
```

### 3. Run Pipeline with Targets

See **[Canonical Script Map - Data Pipeline](./operations/SCRIPT_CANONICAL_MAP.md#data-pipeline)** for all pipeline execution commands.

**Quick start:**
```bash
python scripts/data/run_data_pipeline.py --input data/raw/loan_data.csv
python scripts/data/run_data_pipeline.py --input gsheets://DESEMBOLSOS
```

### 4. Query Variance in Python

```python
import psycopg
from backend.python.kpis.target_loader import TargetLoader

# Load targets
loader = TargetLoader()

# Get actual from database
with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT kpi_name, value FROM kpi_timeseries_daily WHERE date = %s AND kpi_name = %s",
            ("2026-01-31", "total_aum")
        )
        actual_aum = cur.fetchone()[1]

# Calculate variance
jan_target = loader.get_target(1)
variance = loader.calculate_variance(Decimal(actual_aum), jan_target)

print(f"January actual: ${actual_aum:,.2f}")
print(f"January target: ${jan_target:,.2f}")
print(f"Variance: ${variance['variance_amount']:,.2f} ({variance['variance_pct']}%)")
print(f"Status: {variance['status']}")
```

### 5. Query Variance in SQL

```sql
-- View all months with latest actual values
SELECT 
  month_name,
  portfolio_target,
  actual_portfolio,
  variance_amount,
  variance_pct,
  status
FROM kpi_targets_with_variance
ORDER BY month_number;

-- Filter for at-risk months
SELECT * FROM kpi_targets_with_variance WHERE status = 'AT_RISK';

-- Get variance trend
SELECT 
  month_name,
  variance_pct,
  CASE WHEN variance_pct >= 0 THEN '✓ Exceeding' ELSE '✗ Behind' END AS trend
FROM kpi_targets_with_variance
ORDER BY month_number;
```

---

## Variance Status Definitions

| Status | Condition | Action |
|--------|-----------|--------|
| **ON_TRACK** | Actual ≥ 95% of target | ✅ Continue normal operations |
| **MONITOR** | Actual 90-95% of target | ⚠️ Review growth drivers |
| **AT_RISK** | Actual < 90% of target | 🚨 Escalate to leadership |
| **EXCEEDED** | Actual > target | 🎯 Track excess capacity |
| **NO_DATA** | No actuals recorded | ❓ Waiting for data |

---

## Integration with Existing KPIs

Targets automatically integrate with:

1. **KPI Engine** (`backend/python/kpis/engine.py`)
   - `portfolio_vs_target` = actual / target * 100
   - `portfolio_variance_pct` = (actual - target) / target * 100

2. **Monitoring Service** (`backend/python/apps/analytics/api/monitoring_service.py`)
   - Auto-generate alerts if variance < -5%
   - Track monthly achievement rates

3. **Grafana Dashboards**
   - Dual-line chart: Actual vs. Target
   - Gauge: % of monthly objective
   - Variance trend line with alerts

---

## Testing

Run unit tests to verify target calculations:

```bash
# Test target loader
python -m pytest tests/unit/kpis/test_target_loader.py -v

# Example test
def test_variance_calculation():
    loader = TargetLoader()
    actual = Decimal("8700000")
    target = Decimal("8500000")
    result = loader.calculate_variance(actual, target)
    
    assert result["status"] == "ON_TRACK"
    assert result["variance_pct"] == Decimal("2.35")
```

---

## Migration Steps (When Ready)

1. ✅ Run SQL migration:
   ```bash
   DATABASE_URL=... psql < db/migrations/20260324094000_create_kpi_targets_table.sql
   ```

2. ✅ Verify targets loaded:
   ```bash
   psql -c "SELECT * FROM kpi_targets_2026 ORDER BY month_number;"
   ```

3. ✅ Test variance view:
   ```bash
   psql -c "SELECT * FROM kpi_targets_with_variance ORDER BY month_number;"
   ```

4. ✅ Enable in pipeline:
   - Already enabled in `config/pipeline.yml`
   - No additional configuration needed

---

## Next Steps

1. **Add to Google Sheets:** Create TARGETS_2026 tab with your complete target data
2. **Verify Database:** Run migration and check `kpi_targets_2026` is seeded
3. **Monitor Dashboard:** Add target comparison charts to Grafana
4. **Set Alerts:** Configure threshold alerts for AT_RISK status
5. **Monthly Reviews:** Query variance view for reporting

---

## Files Modified

- ✅ `backend/python/kpis/target_loader.py` — Target loader class
- ✅ `db/migrations/20260324094000_create_kpi_targets_table.sql` — Database schema + seeded targets
- ✅ `config/pipeline.yml` — Target ingestion config
- ✅ `docs/TARGETS_2026.md` — This guide
