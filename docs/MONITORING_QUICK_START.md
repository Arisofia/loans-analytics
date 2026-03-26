# Monitoring Quick Start

**Document Status**: P8 Documentation Remediation (stub, 2026-03-20)  
**Owner**: DevOps & SRE Team  
**Full Guide**: See `OBSERVABILITY.md`

## 5-Minute Setup

### 1. Start Monitoring Stack

```bash
make monitoring-start
# Starts Prometheus, Grafana, AlertManager
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: Check `.env` file

- **Prometheus**: http://localhost:9090

### 3. Verify Health

```bash
make monitoring-health
# Shows status of all monitoring services
```

### 4. View KPI Metrics

In Grafana dashboard "Loans KPI Overview":
- PAR30, PAR90 trends
- NPL ratio monitoring
- Pipeline execution metrics

## Common Alerts

| Alert | Threshold | Action |
|-------|-----------|--------|
| `PipelineExecutionFailed` | Any failure | Check logs in `docker logs pipeline-container` |
| `HighNullRate` | > 30% nulls in critical column | Data quality issue, validate source |
| `KPIOutOfBounds` | PAR30 > 15% | Escalate to Head of Risk |

## Troubleshooting

**Grafana won't start?**
```bash
docker-compose up -d grafana
docker logs grafana
```

**Missing metrics?**
```bash
docker logs prometheus
# Check prometheus.yml syntax
```

## See Also

- `OBSERVABILITY.md` — Full monitoring architecture
- `docs/PROMQL_QUERY_REFERENCE.md` — Advanced metric queries
- `docs/runbook.md` — Incident response procedures

---

*For complete monitoring guide, see OBSERVABILITY.md.*
