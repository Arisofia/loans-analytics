# Observability & Monitoring Setup

**Last Updated:** 2026-01-29  
**Status:** ✅ **PRODUCTION READY**

---

## 📊 Overview

ABACO Loans Analytics observability stack provides real-time monitoring of KPIs, system health, and data quality metrics through Grafana dashboards connected to Supabase.

### Architecture

```
┌─────────────────┐
│  Data Pipeline  │
│ (Python/TS)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌──────────────┐
│   Supabase DB   │←────→│   Grafana    │
│  (PostgreSQL)   │      │  Dashboards  │
└────────┬────────┘      └──────────────┘
         │
         ↓
┌─────────────────┐
│  n8n Automation │
│  (Alerts/Jobs)  │
└─────────────────┘
```

---

## 🚀 Quick Start

### 1. Deploy Observability Stack

```bash
cd n8n
docker-compose up -d
```

This starts:

- **Grafana** on `http://localhost:3001`
- **n8n** on `http://localhost:5678`

### 2. Configure Credentials

Copy environment template:

```bash
cp n8n/.env.example n8n/.env
```

Get Supabase credentials from:
https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api

Required variables:

- `SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co`
- `SUPABASE_ANON_KEY=<your-anon-key>`
- `SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>`

### 3. Access Dashboards

| Service             | URL                                                         | Default Credentials |
| ------------------- | ----------------------------------------------------------- | ------------------- |
| **Grafana**         | http://localhost:3001                                       | admin / admin123    |
| **n8n**             | http://localhost:5678                                       | admin / changeme123 |
| **Supabase Studio** | https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte | SSO Login           |

---

## 📈 Grafana Dashboards

### Available Dashboards

#### 1. **ABACO KPI Overview** (`/grafana/dashboards/kpi-overview.json`)

**Metrics Tracked:**

- Portfolio Performance (total outstanding, loan count, yield)
- Asset Quality (PAR-30, PAR-90, default rate)
- Cash Flow (collections rate, recovery rate)
- Growth Metrics (disbursement volume, new loans)
- Customer Metrics (active borrowers, repeat rate)
- Operational Metrics (processing time, automation rate)

**Panels:**

- Gauge: Current KPI values with threshold indicators
- Time Series: 90-day historical trends
- Table: Real-time KPI status with category grouping

**Refresh Rate:** 30 seconds

#### 2. **Data Quality Dashboard** (Coming Soon)

Monitors:

- Data freshness
- Schema drift detection
- Null/completeness checks
- Ingestion pipeline health

### Data Sources

Configured automatically via provisioning:

1. **Supabase PostgreSQL** (Primary)
   - Direct connection to `db.goxdevkqozomyhsyxhte.supabase.co:5432`
   - Queries: `monitoring.kpi_definitions`, `monitoring.kpi_values`, `public.historical_kpis`
   - SSL: Required

2. **Supabase REST API** (Secondary)
   - REST endpoint: `https://goxdevkqozomyhsyxhte.supabase.co/rest/v1`
   - Auth: Bearer token with SUPABASE_ANON_KEY

3. **Azure Monitor** (Optional)
   - For Azure App Insights and Log Analytics
   - Requires: `AZURE_SUBSCRIPTION_ID`, MSI auth

---

## 🤖 n8n Automation Workflows

### Configured Workflows

#### 1. **KPI Data Ingestion** (Every 6 hours)

- Fetches data from Cascade/CSV sources
- Runs Python pipeline: `scripts/data/run_data_pipeline.py`
- Writes to Supabase tables
- Sends email notification on failure

#### 2. **KPI Alert Monitor** (Every 15 minutes)

- Queries `monitoring.kpi_values` for threshold breaches
- Checks: `red_threshold`, `yellow_threshold` from `kpi_definitions`
- Sends alerts to:
  - Email (`alerts@abaco.co`)
  - Email (owner_agent from kpi_definitions)
  - PagerDuty (critical only)

#### 3. **Dashboard Refresh** (Every 30 minutes)

- Triggers Grafana dashboard reload
- Clears cache for real-time data
- Logs refresh status to Supabase

### Creating Custom Workflows

1. Access n8n: http://localhost:5678
2. Create new workflow
3. Available nodes:
   - **Supabase** (query, insert, update)
   - **HTTP Request** (for external APIs)
   - **Schedule Trigger** (cron jobs)
   - **Email** (notifications)
   - **Code** (JavaScript/Python execution)

Example: Query Supabase and send email alert

```javascript
// n8n Code Node
const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;

const response = await fetch(
  `${supabaseUrl}/rest/v1/monitoring.kpi_values?status=eq.red`,
  {
    headers: {
      apikey: supabaseKey,
      Authorization: `Bearer ${supabaseKey}`,
    },
  },
);

const redKPIs = await response.json();
return { redKPIs };
```

---

## 🔐 Azure Key Vault Integration

### Required Secrets

Add to **Azure Key Vault: aiagent-secrets-kv**

| Secret Name                 | Value                                      | Purpose              |
| --------------------------- | ------------------------------------------ | -------------------- |
| `SUPABASE-URL`              | `https://goxdevkqozomyhsyxhte.supabase.co` | Supabase project URL |
| `SUPABASE-ANON-KEY`         | `<anon-key>`                               | Public API key       |
| `SUPABASE-SERVICE-ROLE-KEY` | `<service-role-key>`                       | Admin operations     |
| `GRAFANA-ADMIN-PASSWORD`    | `<secure-password>`                        | Grafana login        |
| `N8N-BASIC-AUTH-PASSWORD`   | `<secure-password>`                        | n8n login            |

### Deployment Script

```bash
# Set Azure CLI context
az account set --subscription <subscription-id>

# Add secrets to Key Vault
az keyvault secret set --vault-name aiagent-secrets-kv \
  --name SUPABASE-URL \
  --value "https://goxdevkqozomyhsyxhte.supabase.co"

az keyvault secret set --vault-name aiagent-secrets-kv \
  --name SUPABASE-ANON-KEY \
  --value "<your-anon-key>"

# Verify secrets
az keyvault secret list --vault-name aiagent-secrets-kv --query "[].name"
```

### Azure App Service Configuration

Update App Settings to reference Key Vault:

```bash
az webapp config appsettings set --name abaco-analytics-app \
  --resource-group abaco-rg \
  --settings \
    SUPABASE_URL="@Microsoft.KeyVault(VaultName=aiagent-secrets-kv;SecretName=SUPABASE-URL)" \
    SUPABASE_ANON_KEY="@Microsoft.KeyVault(VaultName=aiagent-secrets-kv;SecretName=SUPABASE-ANON-KEY)"
```

---

## 🧪 Testing

### 1. Test Supabase Connection

```bash
# Install dependencies
npm install @supabase/supabase-js dotenv

# Run connection test
node scripts/test-supabase-connection.js
```

Expected output:

```
🔍 Testing Supabase Connection...

📍 Supabase URL: https://goxdevkqozomyhsyxhte.supabase.co
🔑 API Key: eyJhbGciOiJIUzI1NiIs...xHte

🧪 Test 1: Querying monitoring.kpi_definitions...
✅ Successfully connected! Found 19 KPI definitions

🧪 Test 2: Querying monitoring.kpi_values...
✅ Successfully queried kpi_values! Found 10 recent records

🧪 Test 3: Querying public.historical_kpis...
✅ Successfully queried historical_kpis! Found 10 records

✅ All connection tests passed!
```

### 2. Test Grafana Datasource

1. Open Grafana: http://localhost:3001
2. Navigate to: Configuration → Data Sources → Supabase PostgreSQL
3. Click "Test" button
4. Expected: ✅ "Data source is working"

### 3. Test n8n Workflow

1. Open n8n: http://localhost:5678
2. Import workflow: `/n8n/workflows/kpi-ingestion.json` (if created)
3. Click "Execute Workflow"
4. Check execution log for errors

---

## 🛠️ Troubleshooting

### Issue: Grafana can't connect to Supabase

**Symptom:** "pq: SSL required" or "connection refused"

**Solution:**

1. Verify `SUPABASE_SERVICE_ROLE_KEY` is set in `n8n/.env`
2. Check datasource config: `/grafana/provisioning/datasources/supabase.yml`
3. Ensure `sslmode: require` is set
4. Restart Grafana: `docker-compose restart grafana`

### Issue: n8n workflows fail with 401 Unauthorized

**Symptom:** "Invalid API key" in n8n execution log

**Solution:**

1. Regenerate Supabase keys: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
2. Update `n8n/.env` with new `SUPABASE_ANON_KEY`
3. Restart n8n: `docker-compose restart n8n`

### Issue: Docker Compose warnings about variables

**Symptom:** `WARN[0000] The "SUPABASE_URL" variable is not set`

**Solution:**

```bash
cd n8n
cp .env.example .env
# Edit .env with your credentials
docker-compose down
docker-compose up -d
```

### Issue: Grafana shows "No data" in dashboards

**Solution:**

1. Verify Supabase tables have data:
   ```sql
   SELECT COUNT(*) FROM monitoring.kpi_values;
   SELECT COUNT(*) FROM public.historical_kpis;
   ```
2. Check date range in Grafana (top-right corner)
3. Verify KPI definitions exist:
   ```sql
   SELECT * FROM monitoring.kpi_definitions LIMIT 5;
   ```

---

## 📚 Additional Resources

- **Supabase Dashboard:** https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte
- **Grafana Docs:** https://grafana.com/docs/
- **n8n Docs:** https://docs.n8n.io/
- **Azure Monitor:** https://learn.microsoft.com/azure/azure-monitor/

---

## 🚨 Production Checklist

Before deploying to production:

- [ ] Change default passwords in `n8n/.env`
- [ ] Enable SSL/TLS for Grafana (reverse proxy with Caddy/nginx)
- [ ] Configure HTTPS for n8n webhook endpoints
- [ ] Set up backup strategy for Grafana dashboards
- [ ] Configure Email/PagerDuty integration for critical alerts
- [ ] Add monitoring for Grafana/n8n containers (health checks)
- [ ] Review RLS policies in Supabase for data access control
- [ ] Set up log retention policies (Grafana, n8n, Supabase)
- [ ] Document runbooks for alert response procedures
- [ ] Test disaster recovery (restore from backup)

---

**Maintained by:** DevOps Team  
**Support:** observability@abaco.co  
**Last Review:** 2026-01-29
