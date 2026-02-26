# Grafana Connection Setup Guide

**Status:** ✅ Configuration Complete  
**Last Updated:** 2026-02-21  
**Supabase Project:** goxdevkqozomyhsyxhte

---

## Overview

This guide walks through completing the Grafana-Supabase connection for ABACO Loans Analytics observability stack.

### What's Been Updated

- ✅ Datasource configuration corrected to use `goxdevkqozomyhsyxhte` project ID
- ✅ PostgreSQL connection configured with `SUPABASE_SERVICE_ROLE_KEY`
- ✅ Docker Compose environment variables updated
- ✅ Connection pool settings added for optimal performance
- ✅ Setup script created for automated initialization

---

## Quick Start

### 1. Create Environment Configuration

Create `.env.monitoring` file with Supabase credentials:

```bash
cd /path/to/abaco-loans-analytics
```

Run the setup script (recommended):

```bash
./scripts/monitoring/setup-grafana.sh
```

Or manually create `.env.monitoring`:

```bash
cat > .env.monitoring << 'EOF'
GRAFANA_ADMIN_PASSWORD=admin123
SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
AZURE_SUBSCRIPTION_ID=optional-azure-subscription-id
EOF
```

### 2. Get Supabase Credentials

1. Go to **Supabase Dashboard:** https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte
2. Navigate to **Settings → API**
3. Copy the following values:
   - **`SUPABASE_URL`** (Project URL)
   - **`SUPABASE_ANON_KEY`** (anon/public key)
   - **`SUPABASE_SERVICE_ROLE_KEY`** (service_role key)

> ⚠️ **Important:** Service Role Key has admin access. Store securely. Never commit to version control.

### 3. Start Grafana and Monitoring Stack

```bash
# Using setup script (recommended)
./scripts/monitoring/setup-grafana.sh

# OR manually with Docker Compose
docker-compose --env-file .env.monitoring -f docker-compose.monitoring.yml up -d
```

### 4. Access Grafana

Open browser and navigate to:

- **URL:** http://localhost:3001
- **Username:** admin
- **Password:** admin123 (or `GRAFANA_ADMIN_PASSWORD` from `.env.monitoring`)

---

## Verify Connection

### Test Supabase PostgreSQL Datasource

1. In Grafana, go to **Configuration → Data Sources**
2. Select **"Supabase PostgreSQL"**
3. Click **"Test"** button
4. Expected result: ✅ **"Data source is working"**

If failed:
- Check `.env.monitoring` has correct `SUPABASE_SERVICE_ROLE_KEY`
- Verify PostgreSQL password is set: `docker exec grafana echo $SUPABASE_SERVICE_ROLE_KEY`
- Ensure network connectivity: `docker exec grafana curl -v db.goxdevkqozomyhsyxhte.supabase.co`

### Test Supabase REST API Datasource

1. In Grafana, go to **Configuration → Data Sources**
2. Select **"Supabase REST API"**
3. Click **"Test"** button
4. Expected result: ✅ **"Data source is working"**

If failed:
- Verify `SUPABASE_ANON_KEY` is correct
- Check API key has permissions for monitoring tables

### View KPI Dashboards

1. Go to **Dashboards → Browse**
2. Select folder **"KPI Monitoring"**
3. Available dashboards:
   - **ABACO KPI Overview** - Real-time KPI metrics
   - **Supabase PostgreSQL** - Database metrics and health

---

## Data Sources Configuration

All datasources are auto-provisioned. Details:

### 1. Supabase PostgreSQL
- **Endpoint:** `db.goxdevkqozomyhsyxhte.supabase.co:5432`
- **Database:** postgres
- **Authentication:** Service Role Key
- **SSL Mode:** Required
- **Queries Target:**
  - `monitoring.kpi_definitions` - KPI definitions
  - `monitoring.kpi_values` - Real-time KPI values
  - `public.historical_kpis` - Historical data

### 2. Supabase REST API
- **Endpoint:** `https://goxdevkqozomyhsyxhte.supabase.co/rest/v1`
- **Authentication:** Bearer token (Anon Key)
- **Headers:**
  - `apikey: SUPABASE_ANON_KEY`
  - `Authorization: Bearer SUPABASE_ANON_KEY`

### 3. Prometheus Local
- **Endpoint:** `http://prometheus:9090`
- **Scrape Target:** Application metrics
- **Retention:** 30 days

### 4. Azure Monitor (Optional)
- **Type:** Azure Monitor Datasource
- **Auth:** Managed Service Identity
- **Requires:** `AZURE_SUBSCRIPTION_ID`

---

## Creating Custom Dashboards

### Using PostgreSQL Datasource

Example query to fetch KPI values:

```sql
SELECT 
  kpd.name,
  kpv.value,
  kpv.timestamp,
  kpd.category
FROM monitoring.kpi_values kpv
JOIN monitoring.kpi_definitions kpd ON kpv.kpi_id = kpd.id
WHERE kpv.timestamp > NOW() - INTERVAL '7 days'
ORDER BY kpv.timestamp DESC
```

### Using REST API Datasource

Example to query KPI definitions:

```
GET /kpi_definitions?select=*
Headers:
  apikey: ${SUPABASE_ANON_KEY}
```

---

## Troubleshooting

### Issue: "pq: SSL required" error

**Solution:**
1. Verify `sslmode: require` is set in datasource config
2. Check cert availability: 
   ```bash
   echo | openssl s_client -connect db.goxdevkqozomyhsyxhte.supabase.co:5432
   ```
3. Restart Grafana: `docker-compose -f docker-compose.monitoring.yml restart grafana`

### Issue: 401 Unauthorized on REST API

**Solution:**
1. Regenerate keys: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
2. Update `.env.monitoring` with new keys
3. Restart stack: 
   ```bash
   docker-compose --env-file .env.monitoring -f docker-compose.monitoring.yml restart
   ```

### Issue: "No data" in dashboards

**Solution:**
1. Check data exists in Supabase:
   ```sql
   SELECT COUNT(*) FROM monitoring.kpi_values;
   SELECT COUNT(*) FROM public.historical_kpis;
   ```
2. Verify dashboard time range (top-right corner)
3. Check datasource query in dashboard edit mode
4. Review Grafana logs: `docker logs grafana`

### Issue: Grafana won't start

**Solution:**
```bash
# Check logs
docker logs grafana

# Clean and restart
docker-compose -f docker-compose.monitoring.yml down -v
docker-compose --env-file .env.monitoring -f docker-compose.monitoring.yml up -d
```

---

## Production Deployment

Before deploying to production:

- [ ] Change `GRAFANA_ADMIN_PASSWORD` to secure password
- [ ] Enable HTTPS (reverse proxy with Caddy/nginx)
- [ ] Configure SMTP for alert notifications
- [ ] Set up backup strategy for dashboards
- [ ] Configure RLS policies in Supabase
- [ ] Enable audit logging
- [ ] Set resource limits on containers
- [ ] Document runbooks for alert response

---

## Files Changed

- `grafana/provisioning/datasources/supabase.yml` - Updated project IDs and auth
- `docker-compose.monitoring.yml` - Added environment variables
- `scripts/monitoring/setup-grafana.sh` - New setup automation script

---

## Support

For issues or questions:
- **Supabase Dashboard:** https://supabase.com/dashboard
- **Grafana Documentation:** https://grafana.com/docs/
- **Project Team:** observability@abaco.co

