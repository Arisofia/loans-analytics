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
    portfolio_id UUID NOT NULL,
    kpi_name VARCHAR(255) NOT NULL,
    kpi_value DECIMAL(18,6) NOT NULL,
    calculation_date DATE NOT NULL,
    grain VARCHAR(50) NOT NULL CHECK (grain IN ('daily', 'weekly', 'monthly', 'quarterly', 'yearly')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB,
    CONSTRAINT uq_historical_kpis_portfolio_kpi_date 
        UNIQUE(portfolio_id, kpi_name, calculation_date, grain)
);
```

### Column Descriptions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | BIGSERIAL | NO | Auto-incrementing primary key |
| `portfolio_id` | UUID | NO | Reference to portfolio (foreign key if portfolios table exists) |
| `kpi_name` | VARCHAR(255) | NO | KPI identifier (e.g., "default_rate", "disbursements") |
| `kpi_value` | DECIMAL(18,6) | NO | Calculated KPI value with 6 decimal precision |
| `calculation_date` | DATE | NO | Date of KPI calculation or observation |
| `grain` | VARCHAR(50) | NO | Temporal grain: daily, weekly, monthly, quarterly, yearly |
| `created_at` | TIMESTAMPTZ | NO | Record creation timestamp (UTC) |
| `updated_at` | TIMESTAMPTZ | NO | Last update timestamp (UTC, auto-updated) |
| `metadata` | JSONB | YES | Optional metadata (versioning, lineage, sources, etc.) |

### Constraints

1. **Primary Key:** `id` (BIGSERIAL)
2. **Unique Constraint:** `(portfolio_id, kpi_name, calculation_date, grain)`
   - Ensures no duplicate KPI observations for same portfolio/date/grain
3. **Check Constraint:** `grain` must be one of: daily, weekly, monthly, quarterly, yearly

---

## Indices

Performance-optimized indices for common query patterns:

### 1. Portfolio + Date Range Queries
```sql
CREATE INDEX idx_historical_kpis_portfolio_date 
    ON historical_kpis(portfolio_id, calculation_date DESC);
```
**Use Case:** Fetch all KPIs for a portfolio within a date range  
**Query Pattern:** `WHERE portfolio_id = ? AND calculation_date BETWEEN ? AND ?`

### 2. KPI + Date Range Queries
```sql
CREATE INDEX idx_historical_kpis_kpi_date 
    ON historical_kpis(kpi_name, calculation_date DESC);
```
**Use Case:** Cross-portfolio KPI analysis and trend detection  
**Query Pattern:** `WHERE kpi_name = ? AND calculation_date BETWEEN ? AND ?`

### 3. Composite Lookup Index
```sql
CREATE INDEX idx_historical_kpis_lookup 
    ON historical_kpis(portfolio_id, kpi_name, calculation_date DESC);
```
**Use Case:** Specific KPI for a portfolio over time (most common pattern)  
**Query Pattern:** `WHERE portfolio_id = ? AND kpi_name = ? AND calculation_date BETWEEN ? AND ?`

### 4. Grain-Specific Queries
```sql
CREATE INDEX idx_historical_kpis_grain 
    ON historical_kpis(grain, calculation_date DESC);
```
**Use Case:** Aggregate queries by temporal grain (e.g., all monthly KPIs)  
**Query Pattern:** `WHERE grain = 'monthly' AND calculation_date BETWEEN ? AND ?`

---

## KPI Grain Definitions

### Daily (`grain = 'daily'`)
- **Use Case:** Real-time operational metrics
- **Examples:** Daily disbursements, daily collections, daily active loans
- **Retention:** Recommended 90 days (archive older to monthly)

### Weekly (`grain = 'weekly'`)
- **Use Case:** Short-term trends and operational reviews
- **Examples:** Weekly default rate, weekly portfolio growth
- **Retention:** Recommended 52 weeks (1 year)

### Monthly (`grain = 'monthly'`)
- **Use Case:** Strategic planning and board reporting
- **Examples:** Monthly portfolio balance, monthly NPL ratio
- **Retention:** Recommended 60 months (5 years)

### Quarterly (`grain = 'quarterly'`)
- **Use Case:** Executive reporting and regulatory compliance
- **Examples:** Quarterly risk metrics, quarterly profitability
- **Retention:** Recommended 20 quarters (5 years)

### Yearly (`grain = 'yearly'`)
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

For large-scale deployments (millions of rows), consider partitioning by `calculation_date` (year-based):

```sql
-- Convert to partitioned table (requires migration)
ALTER TABLE historical_kpis 
    PARTITION BY RANGE (EXTRACT(YEAR FROM calculation_date));

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

-- Policy: Users can only view their portfolio KPIs
CREATE POLICY "Users can view their portfolio KPIs"
    ON historical_kpis FOR SELECT
    USING (
        auth.uid() IN (
            SELECT user_id FROM portfolios WHERE id = historical_kpis.portfolio_id
        )
    );

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
INSERT INTO historical_kpis (portfolio_id, kpi_name, kpi_value, calculation_date, grain)
VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890',  -- Replace with actual portfolio_id
    'default_rate',
    0.0245,
    CURRENT_DATE,  -- Today's date
    'daily'
);
```

### Query KPI History (Last 30 Days)
```sql
SELECT 
    calculation_date,
    kpi_value
FROM historical_kpis
WHERE 
    portfolio_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'  -- Replace with actual portfolio_id
    AND kpi_name = 'default_rate'
    AND calculation_date >= CURRENT_DATE - INTERVAL '30 days'
    AND grain = 'daily'
ORDER BY calculation_date DESC;
```

### Calculate 30-Day Moving Average
```sql
SELECT 
    calculation_date,
    kpi_value,
    AVG(kpi_value) OVER (
        ORDER BY calculation_date 
        ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
    ) AS moving_avg_30d
FROM historical_kpis
WHERE 
    portfolio_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'  -- Replace with actual portfolio_id
    AND kpi_name = 'default_rate'
    AND grain = 'daily'
ORDER BY calculation_date DESC;
```

### Aggregate Daily to Monthly
```sql
INSERT INTO historical_kpis (portfolio_id, kpi_name, kpi_value, calculation_date, grain)
SELECT 
    portfolio_id,
    kpi_name,
    AVG(kpi_value) AS kpi_value,
    DATE_TRUNC('month', calculation_date)::DATE AS calculation_date,
    'monthly' AS grain
FROM historical_kpis
WHERE 
    grain = 'daily'
    AND calculation_date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month')
    AND calculation_date < DATE_TRUNC('month', CURRENT_DATE)
GROUP BY portfolio_id, kpi_name, DATE_TRUNC('month', calculation_date);
```

---

## Integration with HistoricalContextProvider

The `HistoricalContextProvider` class uses this table in REAL mode:

```python
from datetime import date, timedelta

import psycopg2

# Example: fetch 30 days of historical KPI values for a portfolio
conn = psycopg2.connect(
    dbname="analytics",
    user="app_user",
    password="***",
    host="localhost",
    port=5432,
)

portfolio_id = "00000000-0000-0000-0000-000000000000"
kpi_name = "default_rate"
start_date = date.today() - timedelta(days=30)
end_date = date.today()

with conn, conn.cursor() as cur:
    cur.execute(
        """
        SELECT calculation_date, kpi_value
        FROM historical_kpis
        WHERE portfolio_id = %s
          AND kpi_name = %s
          AND calculation_date BETWEEN %s AND %s
        ORDER BY calculation_date
        """,
        (portfolio_id, kpi_name, start_date, end_date),
    )
    history = cur.fetchall()

# history is a list of (calculation_date, kpi_value) tuples
for calculation_date, kpi_value in history:
    print(calculation_date, kpi_value)
```

---

## Performance Considerations

### Query Optimization
- **Always filter by `portfolio_id` or `kpi_name`** to leverage indices
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
WHERE portfolio_id = 'xxx' AND kpi_name = 'xxx'
AND calculation_date BETWEEN '2026-01-01' AND '2026-01-31';
```
**Solutions:**
- Verify indices exist: `SELECT * FROM pg_indexes WHERE tablename = 'historical_kpis';`
- Run VACUUM ANALYZE: `VACUUM ANALYZE historical_kpis;`
- Consider partitioning for large tables

### Issue: Duplicate Key Violations
**Symptoms:** `ERROR: duplicate key value violates unique constraint`  
**Diagnosis:** Check for existing records with same portfolio_id + kpi_name + date + grain  
**Solutions:**
- Use `ON CONFLICT ... DO UPDATE` for upsert behavior
- Verify grain is correct (e.g., daily vs monthly)
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
