# Monitoring Scripts

Scripts for monitoring, metrics collection, and dashboard management.

## Scripts

**Monitoring Stack:**

- `auto_start_monitoring.sh` - Canonical monitoring stack startup
- `health_check_monitoring.sh` - Check monitoring system health

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
```

## Configuration

See `docker-compose.monitoring.yml` and `config/prometheus.yml` for monitoring configuration.
