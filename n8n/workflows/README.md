# n8n Workflows Directory

> **⚠️ Slack Integration Retired (2026-01)**
>
> Slack notifications referenced below have been deprecated. Use Grafana alerting or email notifications instead.

This directory contains automation workflows for the ABACO Loans Analytics platform.

## Available Workflows

### 1. KPI Data Ingestion (`kpi-ingestion.json`)

**Schedule:** Every 6 hours  
**Trigger:** Cron (`0 */6 * * *`)

**Steps:**

1. Check for new CSV files in data/raw/
2. Execute Python pipeline: `scripts/run_data_pipeline.py`
3. Verify Supabase writes
4. Log completion status (Grafana alerts for failures)

### 2. KPI Alert Monitor (`kpi-alerts.json`)

**Schedule:** Every 15 minutes  
**Trigger:** Cron (`*/15 * * * *`)

**Steps:**

1. Query `monitoring.kpi_values` for status='red'
2. Fetch threshold config from `monitoring.kpi_definitions`
3. Send alerts to:
   - Grafana Alerting
   - Email (owner_agent address)
   - PagerDuty (critical only)

### 3. Dashboard Refresh (`dashboard-refresh.json`)

**Schedule:** Every 30 minutes
**Trigger:** Cron (`*/30 * * * *`)

**Steps:**

1. Trigger Grafana API refresh
2. Clear cache
3. Log refresh status to Supabase

---

## Self-Healing Monitoring Workflows

The following workflows integrate with the Monitoring & Command API (`/monitoring/*` endpoints) to create a self-healing feedback loop.

### 4. Critical Event Listener

**Purpose:** Poll for critical operational events and notify operators.
**Schedule:** Every 60 seconds
**Build in n8n UI:**

1. **Schedule Trigger** node - Cron every 1 minute
2. **HTTP Request** node - `GET http://localhost:8000/monitoring/events?severity=critical&limit=10`
3. **IF** node - Check if `count > 0`
4. **HTTP Request** node (true branch) - Create a command:

   ```text
   POST http://localhost:8000/monitoring/commands
   Body: {
     "command_type": "notify_team",
     "requested_by": "n8n",
     "event_id": "{{ $json.events[0].id }}",
     "parameters": { "channel": "ops", "message": "Critical event detected" }
   }
   ```

5. **Email** or **Webhook** node - Send notification to ops team

### 5. Command Executor

**Purpose:** Poll for pending commands and execute them.
**Schedule:** Every 30 seconds
**Build in n8n UI:**

1. **Schedule Trigger** node - Cron every 30 seconds
2. **HTTP Request** node - `GET http://localhost:8000/monitoring/commands?status=pending&limit=5`
3. **IF** node - Check if `count > 0`
4. **Loop Over Items** node - For each pending command:
   a. **PATCH** - Mark as running:

   ```text
   PATCH http://localhost:8000/monitoring/commands/{{ $json.id }}
   Body: { "status": "running" }
   ```

   b. **Switch** node on `command_type`:
   - `rerun_pipeline` → **Execute Command** node: `python scripts/run_data_pipeline.py`
   - `notify_team` → **Email** or **Webhook** node
   - `scale_up` → Custom HTTP call to cloud provider
     c. **PATCH** - Mark as completed/failed:

   ```text
   PATCH http://localhost:8000/monitoring/commands/{{ $json.id }}
   Body: { "status": "completed", "result": { "output": "..." } }
   ```

### 6. Sentry Webhook Receiver

**Purpose:** Receive Sentry issue webhooks and log them as operational events.
**Trigger:** Webhook (n8n webhook URL)
**Build in n8n UI:**

1. **Webhook** node - Listen on `/webhook/sentry-events` (POST)
2. **Set** node - Extract fields from Sentry payload:

   ```json
   {
     "event_type": "sentry_issue",
     "severity": "{{ $json.level === 'fatal' ? 'critical' : ($json.level === 'error' ? 'warning' : 'info') }}",
     "source": "sentry",
     "payload": {
       "issue_id": "{{ $json.id }}",
       "title": "{{ $json.title }}",
       "url": "{{ $json.url }}"
     }
   }
   ```

3. **HTTP Request** node - `POST http://localhost:8000/monitoring/events` with the mapped body
4. **IF** node - If severity is critical, auto-create a command to notify team

**Sentry Setup:** Configure a webhook integration in Sentry project settings pointing to `http://<n8n-host>:5678/webhook/sentry-events`.

## Creating New Workflows

1. Access n8n: <http://localhost:5678>
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
