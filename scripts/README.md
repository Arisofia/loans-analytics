# Automation Scripts

This directory contains automation scripts for the Abaco Loans Analytics platform, organized by purpose.

## 📁 Directory Structure

```
scripts/
├── data/          # Data generation, processing, and database operations
├── deployment/    # Deployment and production management
├── monitoring/    # Monitoring stack and metrics collection
├── maintenance/   # Repository maintenance and validation
└── evaluation/    # Model evaluation and performance testing
```

See individual README.md files in each subdirectory for detailed documentation.

## 🚀 Quick Start

### Data Operations

```bash
# Generate sample data
python scripts/data/generate_sample_data.py

# Run ETL pipeline
python scripts/data/run_data_pipeline.py --input data/raw/loans.csv

# Setup database
python scripts/data/setup_supabase_tables.py
```

### Deployment

```bash
# Deploy to Azure
./scripts/deployment/deploy_to_azure.sh

# Health check
python scripts/deployment/health_check.py

# Rollback if needed
./scripts/deployment/rollback_deployment.sh
```

### Start Monitoring Stack (Fully Automated)

```bash
# Option 1: Using make (recommended)
make monitoring-start

# Option 2: Direct script execution
bash scripts/monitoring/auto_start_monitoring.sh
```

This will automatically:

1. ✅ Check Docker is running (start if needed)
2. ✅ Load environment variables from `.env.local`
3. ✅ Validate Supabase credentials
4. ✅ Stop conflicting containers
5. ✅ Start Prometheus + Grafana + Alertmanager
6. ✅ Configure Grafana datasource
7. ✅ Open Grafana in your browser (optional)

### Repository Maintenance

```bash
# Run health check
./scripts/maintenance/repo-doctor.sh

# Validate structure
python scripts/maintenance/validate_structure.py

# Cleanup old workflows
./scripts/maintenance/cleanup_workflow_runs_by_count.sh
```

## 📊 Script Categories

### Data Scripts (`data/`)

Data generation, ETL pipeline, database operations. See [data/README.md](data/README.md)

### Deployment Scripts (`deployment/`)

Azure deployment, health checks, rollback procedures. See [deployment/README.md](deployment/README.md)

### Monitoring Scripts (`monitoring/`)

Prometheus/Grafana stack, metrics, dashboards. See [monitoring/README.md](monitoring/README.md)

### Maintenance Scripts (`maintenance/`)

Repository health, validation, housekeeping. See [maintenance/README.md](maintenance/README.md)

## 📋 Common Tasks

### Stop Monitoring Stack

```bash
make monitoring-stop
```

### View Logs

```bash
make monitoring-logs
```

## Legacy Documentation

The following sections contain detailed documentation for individual scripts. For new development, prefer the organized structure above.

---

## 📊 Monitoring Scripts (Legacy)

| Script                         | Description                                                  | Usage                                             |
| ------------------------------ | ------------------------------------------------------------ | ------------------------------------------------- |
| **auto_start_monitoring.sh**   | Complete automation for monitoring stack                     | `bash scripts/auto_start_monitoring.sh`           |
| **health_check_monitoring.sh** | Smart health verification with critical/optional distinction | `bash scripts/health_check_monitoring.sh`         |
| **import_dashboards.sh**       | Automated Grafana dashboard import                           | `bash scripts/import_dashboards.sh`               |
| **backup_dashboards.sh**       | Export all Grafana dashboards to JSON                        | `bash scripts/backup_dashboards.sh [output-dir]`  |
| **restore_dashboards.sh**      | Import dashboards from backup                                | `bash scripts/restore_dashboards.sh [backup-dir]` |
| **start_monitoring.sh**        | Basic monitoring startup (legacy)                            | `bash scripts/start_monitoring.sh`                |
| **load_env.sh**                | Load environment variables from .env.local                   | `source scripts/load_env.sh`                      |
| **test_metrics_api.sh**        | Test Supabase Metrics API connection                         | `bash scripts/test_metrics_api.sh`                |

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

| Script                | Description                                        | Usage                                    |
| --------------------- | -------------------------------------------------- | ---------------------------------------- |
| **master_cleanup.sh** | 🧹 Master cleanup (local + cloud cleanup guidance) | `./scripts/master_cleanup.sh --dry-run`  |
| **cleanup_repo.sh**   | Code quality cleanup                               | `./scripts/cleanup_repo.sh`              |
| **repo-cleanup.sh**   | Git repository cleanup                             | `./scripts/repo-cleanup.sh --aggressive` |
| **repo-doctor.sh**    | Repository health checks                           | `./scripts/repo-doctor.sh`               |
| **pr_status.py**      | Check GitHub PR status                             | `python scripts/pr_status.py`            |

### 🧹 Master Cleanup Script (Recommended)

**Purpose**: Complete cleanup of the local repository plus guided cloud cleanup — removes ALL local backups, copies, caches, and temporary files, and provides manual checklists/instructions for safely cleaning Supabase/Azure resources (no automatic cloud deletion).

**Quick Start**:

```bash
# Preview cleanup (safe)
./scripts/master_cleanup.sh --dry-run

# Execute cleanup
./scripts/master_cleanup.sh --execute

# Nuclear option (maximum cleanup)
./scripts/master_cleanup.sh --nuclear
```

**What It Cleans**:

- Python caches (`__pycache__/`, `.pytest_cache/`, `.mypy_cache/`)
- Node modules and build artifacts (`node_modules/`, `dist/`, `.next/`)
- Backup files (`*.backup`, `*.bak`, `*.old`, `*.copy`, numbered copies)
- Temporary files (`tmp/`, `*.tmp`, `*.temp`, `*.swp`)
- Logs and reports (`logs/`, `*.log`, `test-results/`)
- Data run artifacts (`data/metrics/run_*`, `logs/runs/run_*`)
- Docker resources (stopped containers, dangling images)
- Git cleanup (merged branches, garbage collection)

**Documentation**: [docs/MASTER_CLEANUP_GUIDE.md](../docs/MASTER_CLEANUP_GUIDE.md) | [Quick Reference](../docs/MASTER_CLEANUP_QUICK_REF.md) | [Examples](../docs/MASTER_CLEANUP_EXAMPLES.md)

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

# Check health status
make monitoring-health

# Backup dashboards
make dashboard-backup

# Restore dashboards from latest backup
make dashboard-restore

# Restart stack if needed
make monitoring-stop
make monitoring-start
```

### Dashboard Management

```bash
# Export all dashboards to timestamped backup
bash scripts/backup_dashboards.sh
# Output: grafana/dashboards/backups/YYYY-MM-DD_HH-MM-SS/

# Export to specific directory
bash scripts/backup_dashboards.sh /path/to/backup

# Restore from latest backup
bash scripts/restore_dashboards.sh
# Default: grafana/dashboards/backups/latest/

# Restore from specific backup
bash scripts/restore_dashboards.sh grafana/dashboards/backups/2026-01-30_15-30-00/

# Quick dashboard workflow
make dashboard-backup  # Export current state
# Make changes in Grafana UI
make dashboard-backup  # New versioned backup
# Rollback if needed: bash scripts/restore_dashboards.sh [previous-backup-dir]
```

### Troubleshooting

```bash
# Check monitoring stack health (critical targets must be UP)
make monitoring-health

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

## 📖 Query Reference

See [docs/PROMQL_QUERY_REFERENCE.md](../docs/PROMQL_QUERY_REFERENCE.md) for:

- PromQL syntax examples
- Database performance queries (TPS, connections, cache hit ratio)
- Resource monitoring (CPU, memory, disk)
- PgBouncer connection pool queries
- Alert rule examples
- Dashboard panel query breakdown
- Troubleshooting queries

Quick examples:

```promql
# Transactions per second
rate(pg_stat_database_xact_commit{datname="postgres"}[5m])

# Cache hit ratio (target >95%)
100 * (rate(pg_stat_database_blks_hit[5m]) / (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m])))

# Active connections
pg_stat_database_numbackends{datname="postgres"}
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
