# Monitoring Scripts

Scripts for monitoring, metrics collection, and dashboard management.

## Scripts

**Monitoring Stack:**

- `auto_start_monitoring.sh` - Canonical monitoring stack startup
- `health_check_monitoring.sh` - Check monitoring system health
- `harden_rls_sensitive_tables.sh` - Remove permissive read-all policies on sensitive tables and preserve KPI public views

**Metrics:**

- `metrics_exporter.py` - Export metrics to Prometheus format
- `store_metrics.py` - Store metrics in database

**Dashboards:**

- `import_dashboards.sh` - Import dashboard configurations

**Configuration:**

- `generate_alertmanager_config.sh` - Generate Alertmanager config

## Usage Examples

```bash
# Start monitoring stack (canonical)
./scripts/monitoring/auto_start_monitoring.sh

# Export metrics
python scripts/monitoring/metrics_exporter.py

# Health check
./scripts/monitoring/health_check_monitoring.sh

# Harden RLS on sensitive tables (requires DATABASE_URL)
DATABASE_URL=postgres://... ./scripts/monitoring/harden_rls_sensitive_tables.sh
```

## Configuration

See `docker-compose.monitoring.yml` and `config/prometheus.yml` for monitoring configuration.
