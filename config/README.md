# Configuration Files - Monitoring & Observability

This directory contains production-ready configurations for monitoring the Abaco Loans Analytics platform.

## 📁 Files Overview

### Prometheus Configuration

**`prometheus.yml`** - Main Prometheus scrape configuration

- Supabase Metrics API scraping (database performance)
- Pipeline application metrics endpoint
- Multi-agent system metrics
- Self-monitoring (Prometheus + Node Exporter)

### Alert Rules

**`rules/supabase_alerts.yml`** - Database-level alerts (15 rules)

- **Critical**: Connection pool exhaustion, CPU high, disk space
- **Warning**: Cache hit ratio, slow queries, table bloat
- **Info**: Growth trends, capacity planning

**`rules/pipeline_alerts.yml`** - Application-level alerts (12 rules)

- **Critical**: Pipeline failures, KPI calculation errors, PII masking failures
- **Warning**: SLA breaches, agent failures, cost anomalies
- **Info**: Cache efficiency, data volume anomalies

### Other Configurations

**`pipeline.yml`** - Pipeline orchestrator configuration  
**`kpis/`** - KPI calculation formulas and thresholds  
**`business_rules.yaml`** - Loan status mappings, DPD buckets, risk categories

---

## 🚀 Quick Start

### 1. Set Environment Variables

```bash
# Supabase credentials
export SUPABASE_PROJECT_REF="your_project_ref"
export SUPABASE_SECRET_API_KEY="sb_secret_..."

# Database connection
export SUPABASE_DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"

# Optional: Metrics exporter port
export METRICS_PORT="8000"
```

### 2. Option A: Grafana Cloud (Recommended - No Infrastructure)

1. Sign up: https://grafana.com/auth/sign-up/create-user
2. Add Prometheus data source with Grafana Cloud Agent
3. Configure scrape job (use `prometheus.yml` as reference)
4. Import Supabase dashboard: https://github.com/supabase/supabase-grafana

**Grafana Agent Config** (add to your `agent.yaml`):

```yaml
prometheus:
  configs:
    - name: supabase
      scrape_configs:
        - job_name: "supabase-metrics"
          scrape_interval: 60s
          metrics_path: /customer/v1/privileged/metrics
          scheme: https
          basic_auth:
            username: service_role
            password: "${SUPABASE_SECRET_API_KEY}"
          static_configs:
            - targets:
                - "${SUPABASE_PROJECT_REF}.supabase.co:443"
```

### 2. Option B: Self-hosted Prometheus + Grafana

**Using Docker Compose**:

```bash
# Copy prometheus.yml to your Prometheus volume
cp config/prometheus.yml /path/to/prometheus/config/

# Update env vars in docker-compose.yml
# Then start services
docker-compose up -d prometheus grafana
```

**Manual Installation**:

```bash
# 1. Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 2. Copy config
cp /path/to/abaco-loans-analytics/config/prometheus.yml .
cp -r /path/to/abaco-loans-analytics/config/rules .

# 3. Replace env vars
sed -i "s/\${SUPABASE_PROJECT_REF}/$SUPABASE_PROJECT_REF/g" prometheus.yml
sed -i "s/\${SUPABASE_SECRET_API_KEY}/$SUPABASE_SECRET_API_KEY/g" prometheus.yml

# 4. Start Prometheus
./prometheus --config.file=prometheus.yml
```

**Install Grafana**:

```bash
# Ubuntu/Debian
sudo apt-get install -y grafana

# macOS
brew install grafana

# Start
sudo systemctl start grafana-server
# Or: brew services start grafana

# Access: http://localhost:3000 (admin/admin)
```

### 3. Start Pipeline Metrics Exporter

```bash
# From project root
python scripts/monitoring/metrics_exporter.py

# Access metrics
curl http://localhost:8000/metrics

# Health check
curl http://localhost:8000/health
```

### 4. Import Dashboards

**Supabase Database Dashboard**:

1. Download: https://github.com/supabase/supabase-grafana/raw/main/dashboard.json
2. Grafana → Dashboards → Import → Upload JSON
3. Select Prometheus data source

**Custom Pipeline Dashboard** (coming soon):

- Will include: Pipeline runs, KPI success rates, connection pool health
- Location: `grafana/dashboards/pipeline.json` (to be created)

---

## 📊 Key Metrics Reference

### Supabase Database Metrics

```promql
# Connection pool utilization
pg_stat_database_numbackends / pg_settings_max_connections

# CPU usage
pg_cpu_usage_percent

# Cache hit ratio
pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read)

# Database size
pg_database_size_bytes

# Query latency (P95)
histogram_quantile(0.95, rate(pg_stat_statements_duration_bucket[5m]))

# Table bloat
pg_stat_table_bloat_ratio
```

### Pipeline Application Metrics

```promql
# Pipeline success rate
sum(rate(pipeline_runs_total{status="success"}[5m])) /
sum(rate(pipeline_runs_total[5m]))

# KPI calculation failures
sum(rate(kpi_calculation_failures_total[5m])) by (kpi_name)

# Connection pool saturation
connection_pool_size{state="active"} / connection_pool_size{state="total"}

# Idempotency cache hit rate
rate(idempotency_cache_hits_total[1h]) /
(rate(idempotency_cache_hits_total[1h]) + rate(idempotency_cache_misses_total[1h]))
```

---

## 🚨 Alert Configuration

### Notification Channels

**PagerDuty** (For critical alerts):

```yaml
receivers:
  - name: "pagerduty-critical"
    pagerduty_configs:
      - service_key: "YOUR_PAGERDUTY_SERVICE_KEY"
        severity: "critical"
```

**Email**:

```yaml
receivers:
  - name: "email-team"
    email_configs:
      - to: "platform-team@abaco.com"
        from: "alerts@abaco.com"
        smarthost: "smtp.gmail.com:587"
        auth_username: "alerts@abaco.com"
        auth_password: "${SMTP_PASSWORD}"
```

### Routing Rules

```yaml
# alertmanager.yml
route:
  group_by: ["alertname", "severity"]
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: "email-team"
  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: "pagerduty-critical"
      continue: true

    # Warning alerts to email
    - match:
        severity: warning
      receiver: "email-team"

    # Info alerts (daily digest)
    - match:
        severity: info
      receiver: "email-team"
      group_interval: 24h
```

---

## 🔧 Troubleshooting

### Prometheus Can't Scrape Supabase Endpoint

**Symptoms**: `up{job="supabase-db"}` returns 0

**Checks**:

```bash
# 1. Test endpoint manually
curl -u "service_role:$SUPABASE_SECRET_API_KEY" \
  "https://$SUPABASE_PROJECT_REF.supabase.co/customer/v1/privileged/metrics"

# Should return Prometheus text format with ~200 metrics

# 2. Verify credentials
# Supabase Dashboard → Settings → API Keys → "Secret API key" (starts with sb_secret_...)

# 3. Check Prometheus logs
docker logs prometheus
# Or: journalctl -u prometheus

# 4. Test from Prometheus server
kubectl exec -it prometheus-0 -- /bin/sh
wget -O- --user=service_role --password="$SUPABASE_SECRET_API_KEY" \
  "https://$SUPABASE_PROJECT_REF.supabase.co/customer/v1/privileged/metrics"
```

### Pipeline Metrics Not Showing

**Symptoms**: `pipeline_runs_total` has no data

**Checks**:

```bash
# 1. Is metrics exporter running?
curl http://localhost:8000/health

# 2. Start it if not
python scripts/monitoring/metrics_exporter.py

# 3. Check if metrics are exposed
curl http://localhost:8000/metrics | grep pipeline_runs_total

# 4. Verify Prometheus is scraping
# Prometheus UI → Status → Targets → abaco-pipeline
```

### Alerts Not Firing

**Checks**:

```bash
# 1. Are alert rules loaded?
# Prometheus UI → Alerts → Should see rules from supabase_alerts.yml and pipeline_alerts.yml

# 2. Check Prometheus config
./promtool check config prometheus.yml
./promtool check rules config/rules/*.yml

# 3. Reload Prometheus
curl -X POST http://localhost:9090/-/reload

# 4. Check Alertmanager
curl http://localhost:9093/api/v1/alerts
```

---

## 📚 Documentation

- **Full Integration Guide**: `../docs/SUPABASE_METRICS_INTEGRATION.md`
- **5-Min Quick Start**: `../docs/MONITORING_QUICK_START.md`
- **Analysis (ES)**: `../docs/METRICSAPI_ANALYSIS_ES.md`
- **Metrics Exporter**: `../scripts/monitoring/metrics_exporter.py`
- **Connection Pool**: `../python/supabase_pool.py`

---

## 🔗 External Resources

- Supabase Metrics API Docs: https://supabase.com/docs/guides/platform/metrics
- Supabase Grafana Dashboard: https://github.com/supabase/supabase-grafana
- Prometheus Configuration: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- Grafana Cloud Supabase Integration: https://grafana.com/docs/grafana-cloud/monitor-infrastructure/integrations/integration-reference/integration-supabase/

---

**Maintained by**: Platform Team  
**Last Updated**: 2026-01-30  
**Questions**: platform-team@abaco.co
