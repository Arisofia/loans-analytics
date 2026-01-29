# 🚀 DEPLOYMENT QUICKSTART - ABACO Observability Stack

**Status:** ✅ **READY FOR DEPLOYMENT**  
**Last Updated:** 2026-01-29  
**Estimated Time:** 15 minutes

---

## 📋 Prerequisites

- ✅ Docker & Docker Compose installed
- ✅ Supabase project deployed (ID: `goxdevkqozomyhsyxhte`)
- ✅ Azure Key Vault `aiagent-secrets-kv` configured (optional)
- ✅ Port 3001 (Grafana) and 5678 (n8n) available

---

## 🎯 Step-by-Step Deployment

### Step 1: Get Supabase Credentials

1. Navigate to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
2. Copy these values:
   - **Project URL:** `***REMOVED***`
   - **anon/public key:** `eyJhbGciOiJIUzI1NiIs...` (long string)
   - **service_role key:** `eyJhbGciOiJIUzI1NiIs...` (different long string)

### Step 2: Configure Environment

```bash
cd n8n
cp .env.example .env
nano .env  # or use your preferred editor
```

**Edit these lines:**

```bash
SUPABASE_ANON_KEY=<paste-your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<paste-your-service-role-key>
```

**Optional: Change default passwords (RECOMMENDED for production)**

```bash
GF_ADMIN_PASSWORD=<your-secure-password>
N8N_BASIC_AUTH_PASSWORD=<your-secure-password>
```

### Step 3: Deploy Services

```bash
# From n8n directory
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:

```
NAME                          STATUS    PORTS
grafana-observability         Up        0.0.0.0:3001->3000/tcp
n8n-automation                Up        0.0.0.0:5678->5678/tcp
```

### Step 4: Verify Deployment

#### Test Supabase Connection

```bash
# From project root
cd ..
npm install @supabase/supabase-js dotenv  # if not already installed
node scripts/test-supabase-connection.js
```

Expected: ✅ All connection tests passed!

#### Access Grafana

1. Open: http://localhost:3001
2. Login: `admin` / `admin123` (or your custom password)
3. Go to: Configuration → Data Sources → Supabase PostgreSQL
4. Click "Test" → Should show ✅ "Data source is working"
5. Go to: Dashboards → Browse → KPI Monitoring → ABACO KPI Overview

#### Access n8n

1. Open: http://localhost:5678
2. Login: `admin` / `changeme123` (or your custom password)
3. Complete setup wizard if prompted

---

## 🧪 Verify Data Flow

### 1. Upload Test CSV

1. Open Streamlit dashboard:
   ```bash
   # From project root
   streamlit run streamlit_app.py
   ```
2. Navigate to "📤 Upload Data" page
3. Upload `data/raw/sample_loans.csv`
4. Click "🚀 Process" button
5. Verify: ✅ Pipeline completed successfully

### 2. Check Supabase Data

```sql
-- Run in Supabase SQL Editor
SELECT COUNT(*) FROM monitoring.kpi_values;
SELECT COUNT(*) FROM public.historical_kpis;
```

Expected: Rows > 0 for both tables

### 3. View in Grafana

1. Open: http://localhost:3001
2. Go to: Dashboards → ABACO KPI Overview
3. Verify: Charts showing data (not "No data")
4. Check time range (top-right) - set to "Last 30 days"

---

## 🔐 Azure Key Vault Setup (Optional)

### Add Secrets

```bash
# Set Azure context
az account set --subscription <your-subscription-id>

# Add Supabase credentials
az keyvault secret set --vault-name aiagent-secrets-kv \
  --name SUPABASE-URL \
  --value "***REMOVED***"

az keyvault secret set --vault-name aiagent-secrets-kv \
  --name SUPABASE-ANON-KEY \
  --value "<your-anon-key>"

az keyvault secret set --vault-name aiagent-secrets-kv \
  --name SUPABASE-SERVICE-ROLE-KEY \
  --value "<your-service-role-key>"

# Verify
az keyvault secret list --vault-name aiagent-secrets-kv --query "[].name"
```

### Update Azure App Service

```bash
az webapp config appsettings set --name abaco-analytics-app \
  --resource-group abaco-rg \
  --settings \
    SUPABASE_URL="@Microsoft.KeyVault(VaultName=aiagent-secrets-kv;SecretName=SUPABASE-URL)" \
    SUPABASE_ANON_KEY="@Microsoft.KeyVault(VaultName=aiagent-secrets-kv;SecretName=SUPABASE-ANON-KEY)"
```

---

## 📊 Usage Examples

### Create Alert in Grafana

1. Open dashboard panel (e.g., "PAR-30 Gauge")
2. Click panel title → Edit
3. Go to "Alert" tab → "Create Alert"
4. Configure:
   ```
   Name: PAR-30 Critical Alert
   Condition: WHEN avg() OF query(A, 5m, now) IS ABOVE 5
   Evaluate every: 1m
   For: 5m
   ```
5. Add notification channel (Slack/Email)
6. Save

### Create n8n Workflow for KPI Alerts

1. Open n8n: http://localhost:5678
2. Click "New Workflow"
3. Add nodes:
   - **Schedule Trigger** (every 15 minutes)
   - **HTTP Request** → Supabase API (query red KPIs)
   - **IF** → Check if any red KPIs found
   - **Slack** → Send alert message
4. Configure HTTP Request:
   ```
   URL: ***REMOVED***/rest/v1/monitoring.kpi_values?status=eq.red
   Headers:
     apikey: {{ $env.SUPABASE_ANON_KEY }}
     Authorization: Bearer {{ $env.SUPABASE_ANON_KEY }}
   ```
5. Test → Execute Workflow
6. Save

---

## 🛠️ Troubleshooting

### Issue: Can't access Grafana

**Solution:**

```bash
# Check if container is running
docker ps | grep grafana

# Check logs
docker logs grafana-observability

# Restart
docker-compose restart grafana
```

### Issue: "No data" in Grafana dashboards

**Solutions:**

1. Verify Supabase has data:
   ```sql
   SELECT COUNT(*) FROM monitoring.kpi_values;
   ```
2. Check time range (top-right corner)
3. Test datasource: Configuration → Data Sources → Test
4. Verify `.env` has correct `SUPABASE_SERVICE_ROLE_KEY`

### Issue: n8n workflow fails with 401

**Solutions:**

1. Verify `SUPABASE_ANON_KEY` in `n8n/.env`
2. Restart n8n: `docker-compose restart n8n`
3. Re-enter credentials in n8n UI

### Issue: Docker warnings about variables

**Solution:**

```bash
# Ensure .env file exists in n8n directory
cd n8n
ls -la .env  # Should exist

# If not, copy template
cp .env.example .env

# Edit with your credentials
nano .env

# Restart services
docker-compose down
docker-compose up -d
```

---

## 📚 Next Steps

1. **Customize Dashboards**
   - Edit `/grafana/dashboards/kpi-overview.json`
   - Add new panels for custom KPIs
   - See: `/grafana/dashboards/README.md`

2. **Create Automation Workflows**
   - Build n8n workflows for data ingestion
   - Set up alerting rules
   - See: `/n8n/workflows/README.md`

3. **Production Hardening**
   - Change default passwords
   - Enable HTTPS (use reverse proxy)
   - Configure backups
   - See: `/docs/OBSERVABILITY.md` → Security Checklist

4. **Power BI Integration**
   - Connect Power BI to Supabase (or export to Azure SQL)
   - Configure scheduled refresh
   - See: Power BI trial expires in 27 days

---

## 🔗 Quick Links

| Resource               | URL                                                         |
| ---------------------- | ----------------------------------------------------------- |
| **Grafana**            | http://localhost:3001                                       |
| **n8n**                | http://localhost:5678                                       |
| **Supabase Dashboard** | https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte |
| **Full Documentation** | `/docs/OBSERVABILITY.md`                                    |
| **n8n Setup Guide**    | `/n8n/README.md`                                            |
| **Grafana Dashboards** | `/grafana/dashboards/README.md`                             |

---

## ✅ Deployment Checklist

- [ ] Supabase credentials copied to `n8n/.env`
- [ ] Services deployed: `docker-compose up -d`
- [ ] Grafana accessible at http://localhost:3001
- [ ] n8n accessible at http://localhost:5678
- [ ] Supabase connection test passed
- [ ] Grafana datasource test ✅
- [ ] Sample CSV uploaded and processed
- [ ] KPI data visible in Grafana dashboard
- [ ] Azure Key Vault secrets added (optional)
- [ ] Default passwords changed (production)
- [ ] Alert rules configured (optional)
- [ ] n8n automation workflows created (optional)

---

**Support:** #observability Slack channel  
**Maintained by:** DevOps Team  
**Last Review:** 2026-01-29
