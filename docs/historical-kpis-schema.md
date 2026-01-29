# Historical KPIs Schema Documentation

**Version:** G4.2  
**Status:** Production-Ready  
**Last Updated:** 2026-01-28

---

## Overview

The `historical_kpis` table stores historical Key Performance Indicator (KPI) observations for the multi-agent analytics system. It supports time-series analysis, trend detection, and forecasting capabilities.

## Table Schema

### Table Definition

```sql
CREATE TABLE historical_kpis (
    id BIGSERIAL PRIMARY KEY,
    kpi_id VARCHAR(255) NOT NULL,
    value DECIMAL(18,6) NOT NULL,
    date DATE NOT NULL,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB
);
```

### Column Descriptions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | BIGSERIAL | NO | Auto-incrementing primary key |
| `kpi_id` | VARCHAR(255) | NO | KPI identifier (e.g., "default_rate", "disbursements") |
| `value` | DECIMAL(18,6) | NO | Calculated KPI value with 6 decimal precision |
| `date` | DATE | NO | Date of KPI calculation or observation |
| `timestamp` | TIMESTAMPTZ | NO | Timestamp for the observation (UTC) |
| `created_at` | TIMESTAMPTZ | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMPTZ | NO | Last update timestamp (UTC, auto-updated) |
| `metadata` | JSONB | YES | Optional metadata (versioning, lineage, sources, etc.) |

### Constraints

1. **Primary Key:** `id` (BIGSERIAL)
2. **No Unique Constraints:** Schema allows multiple observations per KPI/date for flexibility

---

## Indices

Performance-optimized indices for common query patterns:

### 1. KPI + Date Range Queries
```sql
CREATE INDEX idx_historical_kpis_kpi_date 
    ON historical_kpis(kpi_id, date DESC);
```
**Use Case:** Primary lookup by KPI and date range  
**Query Pattern:** `WHERE kpi_id = ? AND date BETWEEN ? AND ?`

### 2. Composite Lookup Index
```sql
CREATE INDEX idx_historical_kpis_lookup 
    ON historical_kpis(kpi_id, date DESC, "timestamp" DESC);
```
**Use Case:** KPI queries with timestamp ordering  
**Query Pattern:** `WHERE kpi_id = ? AND date BETWEEN ? AND ? ORDER BY timestamp`


---

## KPI Grain Definitions (Optional via Metadata)

The simplified schema stores grain information in the `metadata` JSONB column. This provides flexibility for temporal aggregation patterns:

### Daily (metadata: `{"grain": "daily"}`)
- **Use Case:** Real-time operational metrics
- **Examples:** Daily disbursements, daily collections, daily active loans
- **Retention:** Recommended 90 days (archive older to monthly)

### Weekly (metadata: `{"grain": "weekly"}`)
- **Use Case:** Short-term trends and operational reviews
- **Examples:** Weekly default rate, weekly portfolio growth
- **Retention:** Recommended 52 weeks (1 year)

### Monthly (metadata: `{"grain": "monthly"}`)
- **Use Case:** Strategic planning and board reporting
- **Examples:** Monthly portfolio balance, monthly NPL ratio
- **Retention:** Recommended 60 months (5 years)

### Quarterly (metadata: `{"grain": "quarterly"}`)
- **Use Case:** Executive reporting and regulatory compliance
- **Examples:** Quarterly risk metrics, quarterly profitability
- **Retention:** Recommended 20 quarters (5 years)

### Yearly (metadata: `{"grain": "yearly"}`)
- **Use Case:** Long-term strategic analysis and benchmarking
- **Examples:** Annual portfolio performance, annual growth rate
- **Retention:** Permanent

---

## Data Retention Policy

| Grain | Retention Period | Archival Strategy |
|-------|-----------------|-------------------|
| Daily | 90 days | Aggregate to weekly/monthly |
| Weekly | 1 year | Aggregate to monthly |
| Monthly | 5 years | Keep indefinitely |
| Quarterly | 5 years | Keep indefinitely |
| Yearly | Permanent | Keep indefinitely |

---

## Partitioning Strategy

For large-scale deployments (millions of rows), consider partitioning by `date` (year-based):

```sql
-- Convert to partitioned table (requires migration)
ALTER TABLE historical_kpis 
    PARTITION BY RANGE (EXTRACT(YEAR FROM date));

-- Create partitions for each year
CREATE TABLE historical_kpis_2024 
    PARTITION OF historical_kpis 
    FOR VALUES FROM (2024) TO (2025);

CREATE TABLE historical_kpis_2025 
    PARTITION OF historical_kpis 
    FOR VALUES FROM (2025) TO (2026);

CREATE TABLE historical_kpis_2026 
    PARTITION OF historical_kpis 
    FOR VALUES FROM (2026) TO (2027);

-- Create future partitions as needed
```

**Benefits:**
- Faster queries on recent data (most common access pattern)
- Easier archival and backup (drop/archive old partitions)
- Improved maintenance operations (VACUUM, ANALYZE on smaller partitions)

---

## Row-Level Security (RLS)

To enable multi-tenant security:

```sql
-- Enable RLS
ALTER TABLE historical_kpis ENABLE ROW LEVEL SECURITY;

-- Add additional tenant-scoped policies here based on your schema
-- (for example, using kpi_id or metadata), ensuring they reference
-- only columns that exist in the historical_kpis table.

-- Policy: Service role can manage all KPIs
CREATE POLICY "Service role can manage KPIs"
    ON historical_kpis FOR ALL
    USING (auth.role() = 'service_role');
```

**Note:** Customize policies based on your authentication and authorization model.

---

## Usage Examples

### Insert Daily KPI
```sql
INSERT INTO historical_kpis (kpi_id, value, date, timestamp, metadata)
VALUES (
    'default_rate',
    0.0245,
    CURRENT_DATE,  -- Today's date
    NOW(),
    '{"grain": "daily"}'::jsonb
);
```

### Query KPI History (Last 30 Days)
```sql
SELECT 
    date,
    value
FROM historical_kpis
WHERE 
    kpi_id = 'default_rate'
    AND date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;
```

### Calculate 30-Day Moving Average
```sql
SELECT 
    date,
    value,
    AVG(value) OVER (
        ORDER BY date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS moving_avg_30d
FROM historical_kpis
WHERE 
    kpi_id = 'default_rate'
ORDER BY date DESC;
```

### Aggregate to Monthly (if using grain in metadata)
```sql
SELECT 
    kpi_id,
    AVG(value) AS avg_value,
    DATE_TRUNC('month', date)::DATE AS month_date,
    COUNT(*) AS data_points
FROM historical_kpis
WHERE 
    date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
    AND date < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY kpi_id, DATE_TRUNC('month', date);
```

---

## Integration with HistoricalContextProvider

The `HistoricalContextProvider` class uses this table in REAL mode:

```python
from datetime import date, timedelta

import psycopg2

# Example: fetch 30 days of historical KPI values
conn = psycopg2.connect(
    dbname="analytics",
    user="app_user",
    password="***",
    host="localhost",
    port=5432,
)

kpi_id = "default_rate"
start_date = date.today() - timedelta(days=30)
end_date = date.today()

with conn, conn.cursor() as cur:
    cur.execute(
        """
        SELECT date, value
        FROM historical_kpis
        WHERE kpi_id = %s
          AND date BETWEEN %s AND %s
        ORDER BY date
        """,
        (kpi_id, start_date, end_date),
    )
    history = cur.fetchall()

# history is a list of (date, value) tuples
for kpi_date, kpi_value in history:
    print(kpi_date, kpi_value)
```

---

## Performance Considerations

### Query Optimization
- **Always filter by `kpi_id`** to leverage indices
- **Use date range filters** to limit result sets
- **Avoid SELECT \*** - specify needed columns explicitly
- **Use EXPLAIN ANALYZE** to verify index usage

### SLOs (Service Level Objectives)
- Single KPI lookup: < 50ms (p95)
- Multi-KPI query (30 days): < 200ms (p95)
- Trend calculation (90 days): < 500ms (p99)
- Bulk insert (1000 rows): < 2s

### Monitoring Queries

#### Check Table Size
```sql
SELECT 
    pg_size_pretty(pg_total_relation_size('historical_kpis')) AS total_size,
    pg_size_pretty(pg_relation_size('historical_kpis')) AS table_size,
    pg_size_pretty(pg_indexes_size('historical_kpis')) AS index_size;
```

#### Check Index Usage
```sql
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'historical_kpis'
ORDER BY idx_scan DESC;
```

#### Check Query Performance
```sql
SELECT 
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE query LIKE '%historical_kpis%'
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Backup and Recovery

### Backup Strategy
- **Daily:** Full backup of historical_kpis table
- **Hourly:** Incremental backup of recent changes (last 24 hours)
- **Retention:** 30 days of daily backups, 1 year of monthly backups

### Recovery Procedures
```bash
# Backup
pg_dump -U postgres -t historical_kpis abaco_loans > historical_kpis_backup.sql

# Restore
psql -U postgres abaco_loans < historical_kpis_backup.sql
```

---

## Migration Checklist

Before deploying to production:

- [ ] Run migration script: `20260128_create_historical_kpis_table.sql`
- [ ] Verify table creation: `SELECT * FROM historical_kpis LIMIT 1;`
- [ ] Verify indices: `SELECT * FROM pg_indexes WHERE tablename = 'historical_kpis';`
- [ ] Test RLS policies (if enabled)
- [ ] Configure backup schedule
- [ ] Set up monitoring alerts
- [ ] Run integration tests: `RUN_REAL_SUPABASE_TESTS=1 pytest tests/integration/`
- [ ] Document table in internal wiki
- [ ] Train team on KPI grain definitions

---

## Troubleshooting

### Issue: Slow Query Performance
**Symptoms:** Queries taking > 500ms  
**Diagnosis:**
```sql
EXPLAIN ANALYZE
SELECT * FROM historical_kpis
WHERE kpi_id = 'xxx'
AND date BETWEEN '2026-01-01' AND '2026-01-31';
```
**Solutions:**
- Verify indices exist: `SELECT * FROM pg_indexes WHERE tablename = 'historical_kpis';`
- Run VACUUM ANALYZE: `VACUUM ANALYZE historical_kpis;`
- Consider partitioning for large tables

### Issue: Duplicate Key Violations
**Symptoms:** `ERROR: duplicate key value violates unique constraint`  
**Diagnosis:** Check for existing records with same kpi_id + date  
**Solutions:**
- Use `ON CONFLICT (kpi_id, date) DO UPDATE` for upsert behavior
- Verify date is correct
- Check if KPI calculation is running multiple times

### Issue: Out of Disk Space
**Symptoms:** `ERROR: could not extend file ... No space left on device`  
**Diagnosis:** Table or indices too large  
**Solutions:**
- Archive old data (e.g., daily > 90 days → delete or move)
- Implement partitioning strategy
- Increase disk space allocation

---

## References

- [PostgreSQL Partitioning Documentation](https://www.postgresql.org/docs/current/ddl-partitioning.html)
- [Supabase Row-Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Index Types](https://www.postgresql.org/docs/current/indexes-types.html)

---

**Document Owner:** Data Engineering Team  
**Review Cycle:** Quarterly  
**Next Review:** 2026-04-28
