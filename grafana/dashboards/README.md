# Grafana Dashboards

> **⚠️ Note (2026-01):** Slack notification channels referenced below are deprecated.
> Use Grafana native alerting with email or Azure integration.

Pre-configured dashboards for ABACO Loans Analytics observability.

## Available Dashboards

### 1. **ABACO KPI Overview** (`kpi-overview.json`)

**Purpose:** Real-time monitoring of 19 KPIs across 6 categories

**Data Sources:**

- Supabase PostgreSQL (primary)
- Tables: `monitoring.kpi_definitions`, `monitoring.kpi_values`, `public.historical_kpis`

**Panels:**

1. **Gauge Panel:** Current KPI values with threshold indicators (green/yellow/red)
2. **Time Series Panel:** 90-day historical trends for all KPIs
3. **Table Panel:** Real-time KPI status with category grouping

**Refresh Rate:** 30 seconds (auto-refresh)

**Variables:**

- Time range selector (top-right)
- KPI category filter (coming soon)

### 2. **Supabase PostgreSQL** (`supabase-postgresql.json`)

**Purpose:** Monitor Supabase database performance and health

### 3. **Data Quality Dashboard** (Coming Soon)

**Metrics:**

- Data freshness (hours since last update)
- Schema drift detection
- Null/completeness percentage
- Ingestion pipeline health

---

## Importing to Grafana Cloud

### Prerequisites

1. Grafana Cloud account with admin access
2. Supabase PostgreSQL datasource configured in Grafana Cloud

### Option 1: Manual Import (Recommended for Grafana Cloud)

1. **Open Grafana Cloud**: Navigate to your Grafana Cloud instance
2. **Go to Dashboards**: Click "Dashboards" in the left sidebar
3. **Import Dashboard**:
   - Click **New** → **Import**
   - Click **Upload JSON file**
   - Select `kpi-overview.json` from this directory
4. **Configure Datasource**:
   - Map `Supabase PostgreSQL` to your configured datasource
   - Click **Import**
5. **Repeat** for `supabase-postgresql.json`

### Option 2: Grafana API Import

```bash
# Set your Grafana Cloud credentials
export GRAFANA_URL="https://your-stack.grafana.net"
export GRAFANA_API_KEY="your-api-key"

# Import KPI Overview dashboard
curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "dashboard": $(cat grafana/dashboards/kpi-overview.json),
  "overwrite": false,
  "folderId": 0
}
EOF
```

### Option 3: Grafana Cloud CLI (grizzly)

```bash
# Install grizzly
go install github.com/grafana/grizzly/cmd/grr@latest

# Configure Grafana Cloud
export GRAFANA_URL="https://your-stack.grafana.net"
export GRAFANA_TOKEN="your-api-key"

# Import dashboards
grr apply grafana/dashboards/kpi-overview.json
grr apply grafana/dashboards/supabase-postgresql.json
```

---

## Setting Up Datasource in Grafana Cloud

Before importing dashboards, configure the Supabase PostgreSQL datasource:

### 1. Add PostgreSQL Datasource

1. Go to **Configuration** → **Data sources** → **Add data source**
2. Select **PostgreSQL**
3. Configure connection:

```yaml
Name: Supabase PostgreSQL
Host: db.<YOUR_PROJECT_REF>.supabase.co:5432
Database: postgres
User: postgres
Password: <your-supabase-db-password>
SSL Mode: require
```

4. Click **Save & Test**

### 2. Alternative: Supabase Connection Pooler

For Grafana Cloud, you may need to use the Supabase connection pooler:

```yaml
Host: aws-0-<REGION>.pooler.supabase.com:6543
Database: postgres
User: postgres.<YOUR_PROJECT_REF>
Password: <your-supabase-db-password>
SSL Mode: require
```

> **Note:** Get your project reference from Supabase Dashboard → Settings → General

---

## Importing Dashboards (Local Docker)

### Option 1: Auto-Provisioning (Recommended)

Dashboards are automatically loaded from this directory when Grafana starts.

Configuration: `/grafana/provisioning/dashboards/default.yml`

```yaml
providers:
  - name: "ABACO KPI Dashboards"
    folder: "KPI Monitoring"
    options:
      path: /var/lib/grafana/dashboards
```

### Option 2: Manual Import

1. Open Grafana: http://localhost:3001
2. Navigate to: Dashboards → Import
3. Upload JSON file from this directory
4. Select "Supabase PostgreSQL" as datasource
5. Click "Import"

## Creating Custom Dashboards

### Example: Portfolio Health Panel

```json
{
  "datasource": "Supabase PostgreSQL",
  "targets": [
    {
      "rawSql": "SELECT as_of_date as time, value_num FROM monitoring.kpi_values WHERE kpi_key = 'total_outstanding_balance' ORDER BY as_of_date",
      "format": "time_series"
    }
  ],
  "type": "graph"
}
```

### Useful Queries

#### Get latest KPI values

```sql
SELECT
  kd.name as kpi_name,
  kv.value_num,
  kv.status,
  kv.as_of_date
FROM monitoring.kpi_definitions kd
LEFT JOIN LATERAL (
  SELECT * FROM monitoring.kpi_values
  WHERE kpi_key = kd.kpi_key
  ORDER BY as_of_date DESC
  LIMIT 1
) kv ON true
ORDER BY kd.category, kd.name;
```

#### Get 90-day trend

```sql
SELECT
  date as time,
  kpi_id as metric,
  value_numeric as value
FROM public.historical_kpis
WHERE date >= NOW() - INTERVAL '90 days'
AND is_final = true
ORDER BY date;
```

#### Get KPIs by status

```sql
SELECT
  status,
  COUNT(*) as count
FROM monitoring.kpi_values
WHERE as_of_date = (SELECT MAX(as_of_date) FROM monitoring.kpi_values)
GROUP BY status;
```

## Threshold Configuration

Thresholds are defined in `monitoring.kpi_definitions`:

```sql
SELECT
  kpi_key,
  green_threshold,
  yellow_threshold,
  red_threshold,
  direction  -- 'higher' or 'lower'
FROM monitoring.kpi_definitions;
```

**Example:**

- `par_30` KPI: direction='lower', green=0-3%, yellow=3-5%, red=>5%
- `collections_rate` KPI: direction='higher', green=>95%, yellow=85-95%, red=<85%

## Alerting

### Configure Alert Rules

1. Open dashboard panel
2. Click panel title → Edit
3. Go to "Alert" tab
4. Configure:
   - **Evaluate every:** 1m
   - **For:** 5m
   - **Condition:** `WHEN avg() OF query(A, 5m, now) IS ABOVE 5`

5. Add notification channel (Slack/Email/PagerDuty)

### Example: PAR-30 Alert

```
Alert: PAR-30 Exceeds Critical Threshold

Condition: avg(par_30) > 5% for 5 minutes
Notification: Slack #risk-alerts
Message: "🚨 PAR-30 is ${value}%, exceeds critical threshold of 5%"
```

## Troubleshooting

### Dashboard shows "No data"

1. Check datasource connection: Configuration → Data Sources → Test
2. Verify tables have data:
   ```sql
   SELECT COUNT(*) FROM monitoring.kpi_values;
   ```
3. Check time range (top-right corner)
4. View panel query: Panel → Edit → Query Inspector

### "pq: permission denied for table" error

**Cause:** RLS policies in Supabase blocking access

**Solution:** Use `SUPABASE_SERVICE_ROLE_KEY` instead of `SUPABASE_ANON_KEY` in datasource config

### Panels not updating

1. Check auto-refresh setting (top-right corner)
2. Verify webhook is triggering (n8n workflow)
3. Clear browser cache
4. Restart Grafana: `docker-compose restart grafana`

## Best Practices

1. **Use variables** for dynamic filtering (portfolio_id, product_code)
2. **Add annotations** for deployment events (via Grafana API)
3. **Create alerts** for critical KPIs (PAR-90, default rate)
4. **Export dashboards** regularly (backup in git)
5. **Document panel queries** with SQL comments
6. **Test queries** in Supabase SQL Editor before adding to panel

## Documentation

- Full setup guide: `/docs/OBSERVABILITY.md`
- Grafana docs: https://grafana.com/docs/grafana/latest/dashboards/
- PostgreSQL datasource: https://grafana.com/docs/grafana/latest/datasources/postgres/
