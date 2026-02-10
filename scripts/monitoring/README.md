# Monitoring Scripts

Scripts for monitoring, metrics collection, and dashboard management.

## Scripts

**Monitoring Stack:**

- `start_monitoring.sh` - Start Prometheus/Grafana stack
- `auto_start_monitoring.sh` - Auto-start monitoring on boot
- `start_grafana.sh` - Start Grafana server
- `health_check_monitoring.sh` - Check monitoring system health

**Metrics:**

- `metrics_exporter.py` - Export metrics to Prometheus format
- `store_metrics.py` - Store metrics in database
- `test_metrics_api.sh` - Test Supabase Metrics API

**Dashboards:**

- `backup_dashboards.sh` - Backup Grafana dashboards
- `restore_dashboards.sh` - Restore Grafana dashboards
- `import_dashboards.sh` - Import dashboard configurations

**Configuration:**

- `generate_alertmanager_config.sh` - Generate Alertmanager config

## Usage Examples

```bash
# Start monitoring stack
./scripts/monitoring/start_monitoring.sh

# Backup dashboards
./scripts/monitoring/backup_dashboards.sh

# Export metrics
python scripts/monitoring/metrics_exporter.py

# Test metrics API
./scripts/monitoring/test_metrics_api.sh
```

## Configuration

See `docker-compose.monitoring.yml` and `config/prometheus.yml` for monitoring configuration.
