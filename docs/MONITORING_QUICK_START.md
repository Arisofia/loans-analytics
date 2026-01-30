# Monitoring Quick Start Guide

## 🎯 5-Minute Setup (Grafana Cloud)

### Step 1: Get Your Credentials

```bash
# From Supabase Dashboard → Settings → API
PROJECT_REF="<your_project_ref>"  # e.g., pljjgdtczxmrxydfuaep
SERVICE_ROLE_KEY="<your_service_role_key>"

# Test endpoint
curl -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
  "https://api.supabase.com/v1/projects/$PROJECT_REF/metrics"
```

### Step 2: Sign Up for Grafana Cloud

1. Go to https://grafana.com/auth/sign-up/create-user
2. Free tier: 10K metrics, 50GB logs, 14-day retention
3. Create workspace

### Step 3: Add Prometheus Data Source

In Grafana Cloud:

1. **Connections** → **Add data source** → **Prometheus**
2. **HTTP** → **URL**: (use Grafana Cloud Prometheus endpoint)
3. **Custom HTTP Headers**:
   - Header: `Authorization`
   - Value: `Bearer $SERVICE_ROLE_KEY`

### Step 4: Configure Scrape Job

Add to Grafana Cloud Agent config:

```yaml
prometheus:
  configs:
    - name: supabase
      scrape_configs:
        - job_name: 'supabase-metrics'
          scrape_interval: 60s
          static_configs:
            - targets: ['api.supabase.com']
          metrics_path: '/v1/projects/<PROJECT_REF>/metrics'
          scheme: https
          bearer_token: '<SERVICE_ROLE_KEY>'
```

### Step 5: Import Dashboard

1. Download: https://github.com/supabase/supabase-grafana
2. **Dashboards** → **Import** → Upload JSON
3. Select Prometheus data source

**✅ Done! You now have 200+ database metrics in Grafana.**

---

## 🔍 Key Metrics to Watch

### Critical (Alert Immediately)

```promql
# Connection pool exhaustion
pg_stat_database_numbackends / pg_settings_max_connections > 0.9

# High CPU usage
pg_cpu_usage_percent > 80

# Slow queries
rate(pg_stat_statements_mean_time_seconds[5m]) > 1
```

### Warning (Investigate Soon)

```promql
# Low cache hit ratio
pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) < 0.95

# Table bloat
pg_stat_table_bloat_ratio > 0.3
```

### Capacity Planning (Weekly Review)

```promql
# Database growth rate
rate(pg_database_size_bytes[7d])

# Transaction throughput
rate(pg_stat_database_xact_commit[5m])
```

---

## 📊 Custom Application Metrics

### Connection Pool Health

From `python/supabase_pool.py`:

```python
pool.get_metrics()
# Returns:
# {
#   "total_connections": 10,
#   "active_connections": 3,
#   "failed_connections": 0,
#   "queries_executed": 1234,
#   "queries_failed": 0
# }
```

### Load Test Results

```bash
python scripts/load_test_supabase.py
# Saves to: data/metrics/load_test_YYYYMMDD_HHMMSS.json

# Key metrics:
# - queries_per_second: 145.2
# - p95_latency_ms: 23.5
# - success_rate: 99.8%
```

### Pipeline Execution

From `src/pipeline/orchestrator.py`:

```json
{
  "run_id": "20260130_a1b2c3d4",
  "status": "success",
  "duration_seconds": 12.3,
  "phases": {
    "ingestion": { "status": "success", "rows": 50000 },
    "transformation": { "status": "success", "rows": 50000 },
    "calculation": { "status": "success", "kpis": 19 },
    "output": { "status": "success", "formats": ["parquet", "csv"] }
  }
}
```

---

## 🚨 Alerting Rules

### Prometheus Alert Configuration

Create `config/prometheus_alerts.yml`:

```yaml
groups:
  - name: abaco-critical
    interval: 60s
    rules:
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
        for: 5m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: 'Supabase connections at {{ $value | humanizePercentage }}'
          runbook: 'https://github.com/Arisofia/abaco-loans-analytics/wiki/Runbook-DB-Connections'

      - alert: DatabaseCPUHigh
        expr: pg_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: 'Database CPU: {{ $value }}%'

      - alert: SlowQueriesDetected
        expr: rate(pg_stat_statements_mean_time_seconds[5m]) > 1
        for: 5m
        labels:
          severity: warning
          team: engineering
        annotations:
          summary: 'Average query time > 1s ({{ $value }}s)'
```

### Notification Channels

Configure in Grafana:

- **Slack**: #eng-alerts (critical), #eng-notifications (warning)
- **PagerDuty**: On-call rotation for critical alerts
- **Email**: tech-leads@abaco.com (daily digest)

---

## 🔧 Troubleshooting

### Metrics Not Appearing

```bash
# 1. Verify endpoint works
curl -H "Authorization: Bearer $SERVICE_ROLE_KEY" \
  "https://api.supabase.com/v1/projects/$PROJECT_REF/metrics"

# Expected output: Prometheus text format with ~200 metrics

# 2. Check Prometheus scrape status
# In Grafana: Explore → Prometheus → up{job="supabase-metrics"}
# Should return: 1 (up) or 0 (down)

# 3. Verify bearer token is correct
# Supabase Dashboard → Settings → API → service_role key (secret)
```

### High Cardinality Warning

If Grafana shows "high cardinality" warning:

```yaml
# Reduce scrape frequency
scrape_interval: 120s # Was 60s

# Or filter specific metrics
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'pg_stat_statements_.*' # Drop detailed statement stats
    action: drop
```

### Dashboard Not Loading

1. Check Prometheus data source is connected
2. Verify time range (default: Last 6 hours)
3. Ensure project has metrics (wait 1-2 minutes after first scrape)

---

## 📖 Reference

### Documentation

- **Full guide**: `docs/SUPABASE_METRICS_INTEGRATION.md`
- **Connection pool**: `docs/CRITICAL_DEBT_FIXES_2026.md`
- **Load testing**: `scripts/load_test_supabase.py --help`

### Useful Links

- Supabase Metrics API: https://supabase.com/docs/guides/platform/metrics
- Supabase Grafana Dashboard: https://github.com/supabase/supabase-grafana
- Prometheus Query Examples: https://prometheus.io/docs/prometheus/latest/querying/examples/

### Support

- Internal: #eng-platform Slack channel
- Supabase: Discord https://discord.supabase.com
- Grafana: Community forums https://community.grafana.com
