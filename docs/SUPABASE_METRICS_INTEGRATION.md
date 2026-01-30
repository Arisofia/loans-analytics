# Supabase Metrics API Integration

## Overview

Supabase exposes a **Prometheus-compatible Metrics API** that surfaces ~200 Postgres performance and health metrics. This complements our custom connection pool metrics and provides deep database observability.

**Status**: Beta (metric names/labels may evolve)  
**Availability**: SaaS only (not available in self-hosted Supabase)

## What We Can Monitor

### Database Performance

- CPU, memory, and I/O utilization
- WAL (Write-Ahead Log) metrics
- Connection pool statistics (Supabase-side)
- Query performance and slow query detection
- Index usage and efficiency
- Replication lag (if applicable)

### Application-Level (Our Custom Metrics)

- Connection pool health (`python/supabase_pool.py`)
- KPI calculation success/failure rates (`src/pipeline/calculation.py`)
- Pipeline idempotency cache hits (`src/pipeline/orchestrator.py`)
- Load test results (`scripts/load_test_supabase.py`)

## Recommended Monitoring Stack

### Option 1: Grafana Cloud (Recommended for Quick Start)

**Pros**: Managed, free tier available, no infrastructure to maintain  
**Setup Time**: ~15 minutes

```bash
# 1. Sign up for Grafana Cloud (free tier)
# 2. Create Prometheus data source
# 3. Add scrape job for Supabase Metrics API
# 4. Import Supabase dashboard JSON
```

**Scrape Config** (`grafana-cloud-prometheus.yml`):

```yaml
scrape_configs:
  - job_name: 'supabase-metrics'
    scrape_interval: 60s
    static_configs:
      - targets:
          - 'api.supabase.com'
    metrics_path: '/v1/projects/<PROJECT_REF>/metrics'
    bearer_token: '<SERVICE_ROLE_KEY>'
    scheme: https
```

### Option 2: Self-Hosted Prometheus + Grafana (Production)

**Pros**: Full control, long-term retention, co-located with application  
**Setup Time**: ~1-2 hours

```bash
# 1. Deploy Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/config/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 2. Deploy Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

**Scrape Config** (`config/prometheus.yml`):

```yaml
global:
  scrape_interval: 60s
  evaluation_interval: 60s

scrape_configs:
  # Supabase database metrics
  - job_name: 'supabase-db'
    scrape_interval: 60s
    metrics_path: /customer/v1/privileged/metrics
    scheme: https
    basic_auth:
      username: service_role
      password: '<SECRET_API_KEY>' # sb_secret_... from Supabase Dashboard
    static_configs:
      - targets:
          - '<PROJECT_REF>.supabase.co:443'
        labels:
          project: '<PROJECT_REF>'
          env: 'production'

  # Application metrics (future: expose from Python)
  - job_name: 'abaco-pipeline'
    scrape_interval: 30s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Option 3: Datadog (Enterprise)

**Pros**: Unified observability (metrics + logs + traces), excellent UI  
**Setup Time**: ~30 minutes

```yaml
# datadog-agent.yaml
instances:
  - prometheus_url: https://api.supabase.com/v1/projects/<PROJECT_REF>/metrics
    namespace: supabase
    metrics:
      - '*'
    bearer_token: <SERVICE_ROLE_KEY>
```

## Key Metrics to Monitor

### Critical Alerts (Page on Failure)

```yaml
# Prometheus alerting rules (config/alerts.yml)
groups:
  - name: supabase-critical
    interval: 60s
    rules:
      # Database connection saturation
      - alert: SupabaseConnectionPoolExhausted
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.9
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: 'Supabase connection pool at {{ $value }}% capacity'

      # High database CPU
      - alert: SupabaseCPUHigh
        expr: pg_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: 'Database CPU usage: {{ $value }}%'

      # Slow queries
      - alert: SlowQueriesDetected
        expr: rate(pg_stat_statements_mean_time_seconds[5m]) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Average query time > 1s'
```

### Warning Alerts (Investigate Soon)

```yaml
- name: supabase-warnings
  interval: 60s
  rules:
    # Table bloat
    - alert: TableBloatHigh
      expr: pg_stat_table_bloat_ratio > 0.3
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: 'Table {{ $labels.table }} has {{ $value }}% bloat'

    # Cache hit ratio low
    - alert: CacheHitRatioLow
      expr: pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) < 0.95
      for: 30m
      labels:
        severity: warning
      annotations:
        summary: 'Cache hit ratio: {{ $value }}%'
```

### Capacity Planning (Weekly Review)

- `pg_database_size_bytes` - Database growth trend
- `pg_stat_database_xact_commit` - Transaction rate
- `pg_stat_database_tup_inserted` - Insert rate (loan volume proxy)
- `pg_replication_lag_seconds` - Replication health

## Integration with Existing Monitoring

### Current Setup

- **OpenTelemetry**: Multi-agent system (`python/multi_agent/tracing.py`)
- **Azure Application Insights**: Pipeline execution traces
- **Custom Metrics**: Connection pool, KPI calculations

### Unified Dashboard Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   Grafana Dashboard                      │
├─────────────────────────────────────────────────────────┤
│  Row 1: Business KPIs                                   │
│  - Loans processed/hour                                 │
│  - KPI calculation success rate                         │
│  - Pipeline run duration (P50/P95/P99)                  │
├─────────────────────────────────────────────────────────┤
│  Row 2: Database Performance (Supabase Metrics API)     │
│  - Connection pool utilization                          │
│  - Query latency (P50/P95/P99)                         │
│  - Cache hit ratio                                      │
│  - WAL generation rate                                  │
├─────────────────────────────────────────────────────────┤
│  Row 3: Application Health (Custom Metrics)             │
│  - Idempotency cache hits                              │
│  - Structured logging volume                            │
│  - Multi-agent LLM costs                                │
└─────────────────────────────────────────────────────────┘
```

## Getting Started (5-Minute Quick Win)

### Step 1: Get Your Metrics API Endpoint

```bash
# Your Supabase project metrics endpoint
METRICS_URL="https://api.supabase.com/v1/projects/<PROJECT_REF>/metrics"
SERVICE_ROLE_KEY="<YOUR_SERVICE_ROLE_KEY>"

# Test it works
curl -H "Authorization: Bearer $SERVICE_ROLE_KEY" $METRICS_URL
```

### Step 2: Sign Up for Grafana Cloud

1. Go to https://grafana.com/auth/sign-up/create-user
2. Free tier includes: 10K series, 50GB logs, 50GB traces
3. Create workspace

### Step 3: Add Supabase Data Source

1. In Grafana Cloud → Connections → Add data source → Prometheus
2. Add scrape job with your Supabase endpoint
3. Test connection

### Step 4: Import Dashboard

1. Download Supabase dashboard: https://github.com/supabase/supabase-grafana
2. Import JSON into Grafana
3. Select your Prometheus data source

### Step 5: Set Up Alerts (Optional)

```bash
# Add to Grafana alert rules
CONNECTION_POOL_ALERT="pg_stat_database_numbackends / pg_settings_max_connections > 0.9"
CPU_ALERT="pg_cpu_usage_percent > 80"
```

## Cost Considerations

### Grafana Cloud Free Tier Limits

- **Metrics**: 10,000 active series (Supabase exposes ~200, plenty of headroom)
- **Logs**: 50GB/month (enough for structured logs from pipeline)
- **Traces**: 50GB/month (OpenTelemetry traces from multi-agent)
- **Retention**: 14 days (acceptable for operational monitoring)

**Estimated Usage**:

- Supabase metrics: ~200 series × 60s scrape = 200 series
- Custom app metrics: ~50 series × 30s scrape = 50 series
- **Total**: ~250 series (well within free tier)

### Self-Hosted Costs

- **Prometheus**: ~2GB RAM, 50GB storage (1 year retention)
- **Grafana**: ~512MB RAM
- **Total**: ~$20/month on DigitalOcean/AWS ($10 Prometheus + $5 Grafana + $5 storage)

## Roadmap

### Phase 1: Database Observability (Now)

- ✅ Implement connection pooling (`python/supabase_pool.py`)
- ✅ Create load test framework (`scripts/load_test_supabase.py`)
- 🔲 Set up Prometheus scraping of Supabase Metrics API
- 🔲 Import Supabase Grafana dashboard
- 🔲 Configure critical alerts (connection pool, CPU)

### Phase 2: Application Metrics (Next 2 weeks)

- 🔲 Expose Prometheus `/metrics` endpoint from pipeline
- 🔲 Add custom metrics: idempotency cache hits, KPI failures
- 🔲 Create unified Grafana dashboard (DB + app)
- 🔲 Set up alerting for SLA violations

### Phase 3: Cost Attribution (Month 2)

- 🔲 Track LLM costs per agent using OpenTelemetry
- 🔲 Correlate database query costs with pipeline runs
- 🔲 Build FinOps dashboard (cost per loan processed)

### Phase 4: Predictive Monitoring (Month 3)

- 🔲 Capacity forecasting (database growth → AUM scale)
- 🔲 Anomaly detection (sudden query latency spikes)
- 🔲 SLO tracking (99.9% uptime, P95 latency < 100ms)

## Reference Links

- **Supabase Metrics API Docs**: https://supabase.com/docs/guides/platform/metrics
- **Supabase Grafana Dashboard**: https://github.com/supabase/supabase-grafana
- **Prometheus Scrape Config**: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- **Grafana Cloud Free Tier**: https://grafana.com/pricing/

## Support

For questions or issues:

1. Check Supabase Discord: https://discord.supabase.com
2. Review Grafana community forums: https://community.grafana.com
3. Internal docs: `docs/CRITICAL_DEBT_FIXES_2026.md` (connection pooling)
