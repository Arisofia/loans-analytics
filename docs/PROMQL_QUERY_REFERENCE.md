# PromQL Query Reference for Abaco Monitoring

> **Practical PromQL examples for Supabase PostgreSQL, PgBouncer, and pipeline monitoring**

## Table of Contents

1. [Basic PromQL Syntax](#basic-promql-syntax)
2. [Database Performance Queries](#database-performance-queries)
3. [Resource Monitoring](#resource-monitoring)
4. [PgBouncer Connection Pool](#pgbouncer-connection-pool)
5. [Alert Rule Examples](#alert-rule-examples)
6. [Dashboard Panel Queries](#dashboard-panel-queries)
7. [Troubleshooting Queries](#troubleshooting-queries)

---

## Basic PromQL Syntax

### Instant Vectors

```promql
# Current database connections
pg_stat_database_numbackends{datname="postgres"}

# All PgBouncer metrics
pgbouncer_stats_queries_total
```

### Range Vectors

```promql
# Query rate over last 5 minutes
rate(pg_stat_database_xact_commit[5m])

# Connection changes in last hour
delta(pg_stat_database_numbackends[1h])
```

### Aggregation Operators

```promql
# Sum connections across all databases
sum(pg_stat_database_numbackends)

# Average cache hit ratio
avg(rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m])))

# Maximum connection count
max(pg_stat_database_numbackends)
```

---

## Database Performance Queries

### Transactions Per Second (TPS)

**Copy-paste ready:**

```promql
# Commits per second
rate(pg_stat_database_xact_commit{datname="postgres"}[5m])

# Rollbacks per second
rate(pg_stat_database_xact_rollback{datname="postgres"}[5m])

# Total TPS (commits + rollbacks)
sum(rate(pg_stat_database_xact_commit{datname="postgres"}[5m])) + sum(rate(pg_stat_database_xact_rollback{datname="postgres"}[5m]))
```

**Explanation**: Uses `rate()` to calculate per-second rates from cumulative counters. The `[5m]` window provides smooth results.

### Active Connections

**Copy-paste ready:**

```promql
# Current connections
pg_stat_database_numbackends{datname="postgres"}

# Connection growth rate
deriv(pg_stat_database_numbackends{datname="postgres"}[10m])

# Max connections reached
pg_settings_max_connections
```

**Explanation**: `numbackends` shows active connections. `deriv()` calculates rate of change. Compare with `max_connections` to avoid hitting limits.

### Cache Hit Ratio

**Copy-paste ready:**

```promql
# Cache hit ratio (percentage)
100 * (
  rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) /
  (rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) + rate(pg_stat_database_blks_read{datname="postgres"}[5m]))
)
```

**Explanation**: Ratio of blocks read from cache vs disk. Target: >95%. Low ratio indicates insufficient shared_buffers or working set too large.

### Query Operations

**Copy-paste ready:**

```promql
# Rows fetched per second
rate(pg_stat_database_tup_fetched{datname="postgres"}[5m])

# Rows inserted per second
rate(pg_stat_database_tup_inserted{datname="postgres"}[5m])

# Rows updated per second
rate(pg_stat_database_tup_updated{datname="postgres"}[5m])

# Rows deleted per second
rate(pg_stat_database_tup_deleted{datname="postgres"}[5m])
```

**Explanation**: Tracks data modification patterns. High update/delete rates may indicate maintenance needs (VACUUM, ANALYZE).

---

## Resource Monitoring

### CPU Usage

**Copy-paste ready:**

```promql
# CPU usage percentage (inverse of idle)
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# User + system CPU
sum(rate(node_cpu_seconds_total{mode=~"user|system"}[5m])) * 100
```

**Explanation**: node_exporter provides CPU metrics. Idle mode inverted gives utilization. Combine user+system for application CPU.

### Memory Usage

**Copy-paste ready:**

```promql
# Memory usage percentage
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))

# Memory available in GB
node_memory_MemAvailable_bytes / 1024 / 1024 / 1024

# Swap usage
node_memory_SwapTotal_bytes - node_memory_SwapFree_bytes
```

**Explanation**: MemAvailable accounts for cache/buffers that can be freed. Swap usage indicates memory pressure.

### Disk Usage

**Copy-paste ready:**

```promql
# Disk usage percentage
100 * (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}))

# Disk available in GB
node_filesystem_avail_bytes{mountpoint="/"} / 1024 / 1024 / 1024

# Disk I/O read bytes per second
rate(node_disk_read_bytes_total[5m])

# Disk I/O write bytes per second
rate(node_disk_written_bytes_total[5m])
```

**Explanation**: Tracks filesystem capacity and I/O throughput. High I/O rates correlate with database load.

---

## PgBouncer Connection Pool

### Pool Metrics

**Copy-paste ready:**

```promql
# Active connections
pgbouncer_pools_cl_active{database="postgres"}

# Idle connections
pgbouncer_pools_cl_idle{database="postgres"}

# Waiting clients
pgbouncer_pools_cl_waiting{database="postgres"}

# Server connections
pgbouncer_pools_sv_active{database="postgres"}
```

**Explanation**: Monitors connection pool health. High `cl_waiting` indicates pool exhaustion. Adjust pool_size/max_client_conn.

### Pool Utilization

**Copy-paste ready:**

```promql
# Pool utilization percentage
100 * (pgbouncer_pools_cl_active{database="postgres"} / pgbouncer_config_max_client_conn)

# Average wait time
rate(pgbouncer_stats_total_wait_time[5m]) / rate(pgbouncer_stats_total_requests[5m])
```

**Explanation**: Utilization >80% suggests increasing pool size. Wait time >10ms indicates contention.

---

## Alert Rule Examples

### High Connection Count

**Copy-paste ready:**

```promql
# Alert when connections exceed 80% of max
(pg_stat_database_numbackends / pg_settings_max_connections) > 0.8
```

**Threshold**: 80% for warning, 90% for critical. Prevents connection limit exhaustion.

### Low Cache Hit Ratio

**Copy-paste ready:**

```promql
# Alert when cache hit ratio drops below 95%
(
  rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) /
  (rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) + rate(pg_stat_database_blks_read{datname="postgres"}[5m]))
) < 0.95
```

**Threshold**: <95% indicates excessive disk reads. Consider increasing shared_buffers.

### High Disk Usage

**Copy-paste ready:**

```promql
# Alert when disk usage exceeds 90%
(1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"})) > 0.9
```

**Threshold**: 90% warning, 95% critical. Triggers before disk full errors.

### PgBouncer Pool Exhaustion

**Copy-paste ready:**

```promql
# Alert when waiting clients > 10
pgbouncer_pools_cl_waiting{database="postgres"} > 10
```

**Threshold**: >10 waiting clients indicates pool saturation. Scale pool or investigate slow queries.

---

## Dashboard Panel Queries

These are the exact queries used in [grafana/dashboards/supabase-postgresql.json](../grafana/dashboards/supabase-postgresql.json):

### Panel 1: Database Connections

```promql
pg_stat_database_numbackends{datname="postgres"}
```

**Visualization**: Time series graph  
**Purpose**: Monitor active connections over time

### Panel 2: Transactions Per Second

```promql
# Commits
rate(pg_stat_database_xact_commit{datname="postgres"}[5m])

# Rollbacks
rate(pg_stat_database_xact_rollback{datname="postgres"}[5m])
```

**Visualization**: Time series graph with 2 series  
**Purpose**: Track database transaction throughput

### Panel 3: Query Operations

```promql
# Fetched rows/s
rate(pg_stat_database_tup_fetched{datname="postgres"}[5m])

# Inserted rows/s
rate(pg_stat_database_tup_inserted{datname="postgres"}[5m])

# Updated rows/s
rate(pg_stat_database_tup_updated{datname="postgres"}[5m])

# Deleted rows/s
rate(pg_stat_database_tup_deleted{datname="postgres"}[5m])
```

**Visualization**: Stacked area graph  
**Purpose**: Visualize data modification patterns

### Panel 4: PgBouncer Connection Pool

```promql
# Active
pgbouncer_pools_cl_active{database="postgres"}

# Idle
pgbouncer_pools_cl_idle{database="postgres"}
```

**Visualization**: Time series graph  
**Purpose**: Monitor pool efficiency

### Panel 5: Cache Hit Ratio

```promql
100 * (
  rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) /
  (rate(pg_stat_database_blks_hit{datname="postgres"}[5m]) + rate(pg_stat_database_blks_read{datname="postgres"}[5m]))
)
```

**Visualization**: Gauge (red <90%, yellow <95%, green ≥95%)  
**Purpose**: Quick view of cache efficiency

### Panel 6: Disk Usage

```promql
100 * (1 - (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}))
```

**Visualization**: Gauge (green <70%, yellow <90%, red ≥90%)  
**Purpose**: Disk capacity monitoring

### Panel 7: Memory Usage

```promql
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
```

**Visualization**: Time series graph  
**Purpose**: Track memory consumption trends

### Panel 8: CPU Usage

```promql
100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

**Visualization**: Time series graph  
**Purpose**: Monitor CPU utilization

### Panel 9: Disk I/O

```promql
# Read bytes/s
rate(node_disk_read_bytes_total[5m])

# Write bytes/s
rate(node_disk_written_bytes_total[5m])
```

**Visualization**: Time series graph  
**Purpose**: Correlate I/O with database load

---

## Troubleshooting Queries

### Identify Slow Queries

```promql
# Queries taking >1 second
pg_stat_statements_mean_exec_time_seconds > 1

# Total query execution time
sum(rate(pg_stat_statements_total_exec_time_seconds[5m])) by (queryid)
```

**Use Case**: Find queries consuming most database time.

### Connection Leaks

```promql
# Connections per application
pg_stat_activity_count by (application_name)

# Idle in transaction duration
pg_stat_activity_max_tx_duration{state="idle in transaction"}
```

**Use Case**: Detect applications not closing connections or long-running transactions.

### Replication Lag

```promql
# Lag in bytes
pg_replication_lag

# Lag in seconds
pg_stat_replication_replay_lag
```

**Use Case**: Monitor replica health in HA setup.

### Deadlocks

```promql
# Deadlocks per second
rate(pg_stat_database_deadlocks{datname="postgres"}[5m])
```

**Use Case**: Identify transaction conflicts requiring code fixes.

### Index Usage

```promql
# Sequential scans (potential missing index)
rate(pg_stat_user_tables_seq_scan[5m])

# Index scans
rate(pg_stat_user_tables_idx_scan[5m])
```

**Use Case**: High seq_scan indicates missing indexes or inefficient queries.

---

## Best Practices

### Rate vs irate

- **Use `rate()`**: For alerts and dashboards (smooth, averages over time window)
- **Use `irate()`**: For spikes/instant rate (only last 2 samples, volatile)

### Time Window Selection

- **[1m]**: Real-time, noisy
- **[5m]**: Standard for dashboards (smooth, responsive)
- **[15m]**: Trends, less noise
- **[1h]**: Long-term patterns

### Label Filtering

```promql
# Specific database
pg_stat_database_numbackends{datname="postgres"}

# Exclude template databases
pg_stat_database_numbackends{datname!~"template.*"}

# Regex match
pg_stat_database_numbackends{datname=~"prod_.*"}
```

### Aggregation

```promql
# Sum across all databases
sum(pg_stat_database_numbackends)

# Average by instance
avg by (instance) (pg_stat_database_numbackends)

# Max per database
max by (datname) (pg_stat_database_numbackends)
```

---

## Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Supabase Metrics API**: https://supabase.com/docs/guides/platform/metrics
- **PgBouncer Monitoring**: https://www.pgbouncer.org/usage.html#admin-console
- **Alert Rules**: See [config/rules/supabase_alerts.yml](../config/rules/supabase_alerts.yml)

---

## Quick Reference Card

| Metric Type     | PromQL Function             | Use Case                       |
| --------------- | --------------------------- | ------------------------------ |
| Counter         | `rate()`                    | Transactions/sec, query rates  |
| Gauge           | Direct query                | Connections, memory usage      |
| Percentage      | `(metric1 / metric2) * 100` | Cache hit ratio, disk usage    |
| Growth rate     | `deriv()`                   | Connection growth trends       |
| Spike detection | `irate()`                   | Sudden load changes            |
| Aggregation     | `sum()`, `avg()`, `max()`   | Total connections, average CPU |

---

**Last Updated**: 2026-01-30  
**Maintainer**: Abaco Monitoring Team  
**Dashboard**: http://localhost:3001/dashboards
