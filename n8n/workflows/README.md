# n8n Workflows Directory

> **⚠️ Slack Integration Retired (2026-01)**
>
> Slack notifications referenced below have been deprecated. Use Grafana alerting or email notifications instead.

This directory contains automation workflows for the ABACO Loans Analytics platform.

## Available Workflows

### 1. KPI Data Ingestion (`kpi-ingestion.json`)

**Schedule:** Every 6 hours  
**Trigger:** Cron (0 _/6 _ \* \*)

**Steps:**

1. Check for new CSV files in data/raw/
2. Execute Python pipeline: `scripts/run_data_pipeline.py`
3. Verify Supabase writes
4. Log completion status (Grafana alerts for failures)

### 2. KPI Alert Monitor (`kpi-alerts.json`)

**Schedule:** Every 15 minutes  
**Trigger:** Cron (_/15 _ \* \* \*)

**Steps:**

1. Query `monitoring.kpi_values` for status='red'
2. Fetch threshold config from `monitoring.kpi_definitions`
3. Send alerts to:
   - Grafana Alerting
   - Email (owner_agent address)
   - PagerDuty (critical only)

### 3. Dashboard Refresh (`dashboard-refresh.json`)

**Schedule:** Every 30 minutes  
**Trigger:** Cron (_/30 _ \* \* \*)

**Steps:**

1. Trigger Grafana API refresh
2. Clear cache
3. Log refresh status to Supabase

## Creating New Workflows

1. Access n8n: http://localhost:5678
2. Click "New Workflow"
3. Add nodes and configure
4. Export as JSON: Menu → Export → JSON
5. Save to this directory: `workflows/your-workflow-name.json`

## Importing Workflows

```bash
# Copy workflow JSON to n8n data volume
docker cp workflows/kpi-ingestion.json abaco-loans-analytics-n8n-1:/home/node/.n8n/workflows/

# Or mount this directory in docker-compose.yml
```

## Environment Variables

Required in `n8n/.env`:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `PAGERDUTY_API_KEY` (optional)

## Testing Workflows

1. Open workflow in n8n UI
2. Click "Execute Workflow" button
3. Check execution log for errors
4. Verify data in Supabase tables

## Documentation

Full setup guide: `/docs/OBSERVABILITY.md`
