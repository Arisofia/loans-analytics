# Automation Scripts

This directory contains automation scripts for the Abaco Loans Analytics platform.

## 🚀 Quick Start

### Start Monitoring Stack (Fully Automated)

```bash
# Option 1: Using make (recommended)
make monitoring-start

# Option 2: Direct script execution
bash scripts/auto_start_monitoring.sh
```

This will automatically:

1. ✅ Check Docker is running (start if needed)
2. ✅ Load environment variables from `.env.local`
3. ✅ Validate Supabase credentials
4. ✅ Stop conflicting containers
5. ✅ Start Prometheus + Grafana + Alertmanager
6. ✅ Configure Grafana datasource
7. ✅ Open Grafana in your browser (optional)

### Stop Monitoring Stack

```bash
make monitoring-stop
```

### View Logs

```bash
make monitoring-logs
```

## 📊 Monitoring Scripts

| Script                       | Description                                | Usage                                   |
| ---------------------------- | ------------------------------------------ | --------------------------------------- |
| **auto_start_monitoring.sh** | Complete automation for monitoring stack   | `bash scripts/auto_start_monitoring.sh` |
| **start_monitoring.sh**      | Basic monitoring startup (legacy)          | `bash scripts/start_monitoring.sh`      |
| **load_env.sh**              | Load environment variables from .env.local | `source scripts/load_env.sh`            |
| **test_metrics_api.sh**      | Test Supabase Metrics API connection       | `bash scripts/test_metrics_api.sh`      |

## 🧪 Testing Scripts

| Script                          | Description                            | Usage                                                  |
| ------------------------------- | -------------------------------------- | ------------------------------------------------------ |
| **test_supabase_connection.py** | Test Supabase connection pooling       | `python scripts/test_supabase_connection.py`           |
| **load_test_supabase.py**       | Load testing framework for Supabase    | `python scripts/load_test_supabase.py --concurrent 10` |
| **metrics_exporter.py**         | Export pipeline metrics for Prometheus | `python scripts/metrics_exporter.py`                   |

## 📦 Pipeline Scripts

| Script                    | Description                   | Usage                                                            |
| ------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| **run_data_pipeline.py**  | Execute data pipeline ETL     | `python scripts/run_data_pipeline.py --input data/raw/loans.csv` |
| **validate_structure.py** | Validate repository structure | `python scripts/validate_structure.py`                           |

## 🔧 Utility Scripts

| Script           | Description            | Usage                         |
| ---------------- | ---------------------- | ----------------------------- |
| **pr_status.py** | Check GitHub PR status | `python scripts/pr_status.py` |

## ⚙️ Environment Setup

All scripts expect environment variables to be configured in `.env.local`:

```bash
# Required for monitoring
SUPABASE_PROJECT_REF=your_project_ref
SUPABASE_SECRET_API_KEY=sb_secret_your_key
NEXT_PUBLIC_SUPABASE_URL=https://your_project.supabase.co
GRAFANA_ADMIN_PASSWORD=admin123

# Required for pipeline
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_ANON_KEY=your_anon_key
```

See `.env.local.INSTRUCTIONS` for detailed setup.

## 📚 Documentation

- **Monitoring Setup**: [docs/PROMETHEUS_GRAFANA_QUICKSTART.md](../docs/PROMETHEUS_GRAFANA_QUICKSTART.md)
- **Metrics API**: [docs/SUPABASE_METRICS_INTEGRATION.md](../docs/SUPABASE_METRICS_INTEGRATION.md)
- **Quick Start**: [docs/MONITORING_QUICK_START.md](../docs/MONITORING_QUICK_START.md)

## 🎯 Common Tasks

### First Time Setup

```bash
# 1. Create .env.local with credentials
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# 2. Start monitoring stack
make monitoring-start

# 3. Access services
# Prometheus: http://localhost:9090
# Grafana:    http://localhost:3001 (admin/admin123)
```

### Daily Development

```bash
# Check monitoring is running
docker ps | grep -E "(prometheus|grafana|alertmanager)"

# View real-time logs
make monitoring-logs

# Restart stack if needed
make monitoring-stop
make monitoring-start
```

### Troubleshooting

```bash
# Check Docker is running
docker ps

# View specific service logs
docker logs prometheus
docker logs grafana
docker logs alertmanager

# Restart a specific service
docker-compose -f docker-compose.monitoring.yml restart grafana

# Full cleanup and restart
docker-compose -f docker-compose.monitoring.yml down -v
make monitoring-start
```

## 🔐 Security Notes

- Never commit `.env.local` - it contains real credentials
- Use `.env.example` for documentation only (safe placeholders)
- Rotate API keys if accidentally exposed
- Monitor access logs in Grafana

## 🤝 Contributing

When adding new scripts:

1. Add executable permissions: `chmod +x scripts/your_script.sh`
2. Document in this README
3. Add to appropriate Makefile target if needed
4. Include inline help: `your_script.sh --help`
