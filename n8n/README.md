# n8n + Grafana Observability Stack

> **⚠️ Slack Integration Retired (2026-01)**
>
> Slack webhook notifications referenced in this document have been deprecated.
> Alerting is now handled via Grafana alerts and Azure diagnostics.

Deployment configuration for ABACO Loans Analytics observability and automation services.

## 🚀 Quick Start

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required variables:

- `SUPABASE_URL` - Get from https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
- `SUPABASE_ANON_KEY` - Public API key
- `SUPABASE_SERVICE_ROLE_KEY` - Admin key (for Grafana datasource)

### 2. Deploy Services

```bash
# Start all services (Grafana + n8n)
docker-compose up -d

# Start only Grafana
docker-compose up -d grafana

# Start only n8n
docker-compose up -d n8n

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access Services

| Service     | URL                   | Credentials         |
| ----------- | --------------------- | ------------------- |
| **Grafana** | http://localhost:3001 | admin / admin123    |
| **n8n**     | http://localhost:5678 | admin / changeme123 |

**⚠️ IMPORTANT:** Change default passwords in `.env` before production deployment!

## 📊 Grafana Setup

### First Login

1. Navigate to http://localhost:3001
2. Login with default credentials (admin / admin123)
3. **Change your password** (prompted on first login)
4. Verify datasource: Configuration → Data Sources → Supabase PostgreSQL
5. Click "Test" - should show ✅ "Data source is working"

### Import Dashboards

Dashboards are auto-provisioned from `/grafana/dashboards/`:

- **ABACO KPI Overview** - Main KPI monitoring dashboard

To manually import:

1. Go to: Dashboards → Import
2. Upload JSON file from `/grafana/dashboards/`
3. Select "Supabase PostgreSQL" as datasource
4. Click "Import"

### Create Custom Dashboard

1. Click "+" → Dashboard
2. Add Panel
3. Select "Supabase PostgreSQL" datasource
4. Write SQL query:
   ```sql
   SELECT
     as_of_date as time,
     kpi_key as metric,
     value_num as value
   FROM monitoring.kpi_values
   WHERE $__timeFilter(as_of_date)
   ORDER BY as_of_date
   ```
5. Configure visualization (Graph, Gauge, Table, etc.)
6. Save dashboard

## 🤖 n8n Automation

### First Login

1. Navigate to http://localhost:5678
2. Login with credentials from `.env` (default: admin / changeme123)
3. Complete setup wizard

### Import Workflows

1. Go to: Workflows → Import from File
2. Select workflow JSON from `/n8n/workflows/`
3. Configure credentials:
   - Supabase API key
   - Slack webhook (optional)
   - Email SMTP (optional)

### Example Workflow: KPI Alert Monitor

```javascript
// Trigger: Schedule (every 15 minutes)
// Step 1: HTTP Request to Supabase
const response = await fetch(
  '***REMOVED***/rest/v1/monitoring.kpi_values?status=eq.red',
  {
    headers: {
      apikey: '{{ $env.SUPABASE_ANON_KEY }}',
      Authorization: 'Bearer {{ $env.SUPABASE_ANON_KEY }}',
    },
  }
)

const redKPIs = await response.json()

// Step 2: Send Slack notification if any red KPIs found
if (redKPIs.length > 0) {
  // Trigger Slack webhook
}
```

## 🔧 Configuration Files

### `docker-compose.yml`

Main deployment configuration:

- Service definitions (Grafana, n8n)
- Port mappings
- Volume mounts
- Environment variables
- Health checks

### `/grafana/provisioning/datasources/supabase.yml`

Auto-configures Grafana datasources:

- **Supabase PostgreSQL** - Direct database connection
- **Supabase REST API** - REST endpoint
- **Azure Monitor** - Azure metrics (optional)

### `/grafana/provisioning/dashboards/default.yml`

Dashboard provisioning configuration:

- Auto-loads dashboards from `/grafana/dashboards/`
- Organizes into "KPI Monitoring" folder
- Enables UI updates

### `.env`

Environment variables (copy from `.env.example`):

- Supabase credentials
- Grafana admin password
- n8n auth credentials
- Azure tokens (optional)

## 📦 Data Persistence

Services use Docker volumes for data persistence:

```bash
# List volumes
docker volume ls | grep abaco

# Expected volumes:
# - abaco_grafana_data (Grafana dashboards, settings)
# - abaco_n8n_data (n8n workflows, credentials)
```

### Backup Volumes

```bash
# Backup Grafana data
docker run --rm \
  -v abaco_grafana_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/grafana-backup-$(date +%Y%m%d).tar.gz /data

# Backup n8n data
docker run --rm \
  -v abaco_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/n8n-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Volumes

```bash
# Restore Grafana data
docker run --rm \
  -v abaco_grafana_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/grafana-backup-20260129.tar.gz -C /

# Restore n8n data
docker run --rm \
  -v abaco_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/n8n-backup-20260129.tar.gz -C /
```

## 🧪 Testing

### Test Supabase Connection

```bash
# From project root
node scripts/test-supabase-connection.js
```

Expected output:

```
✅ Successfully connected! Found 19 KPI definitions
✅ Successfully queried kpi_values! Found 10 recent records
✅ All connection tests passed!
```

### Test Grafana API

```bash
# Check health
curl http://localhost:3001/api/health

# List datasources
curl -u admin:admin123 http://localhost:3001/api/datasources

# List dashboards
curl -u admin:admin123 http://localhost:3001/api/search
```

### Test n8n API

```bash
# Check health (requires auth)
curl -u admin:changeme123 http://localhost:5678/healthz

# List workflows
curl -u admin:changeme123 http://localhost:5678/api/v1/workflows
```

## 🚨 Troubleshooting

### Service won't start

**Symptom:** `docker-compose up -d` fails

**Solutions:**

1. Check logs: `docker-compose logs grafana` or `docker-compose logs n8n`
2. Verify port availability: `lsof -i :3001` (Grafana) or `lsof -i :5678` (n8n)
3. Check `.env` file exists and has valid values
4. Restart Docker daemon

### Grafana shows "No data"

**Symptom:** Dashboard panels are empty

**Solutions:**

1. Verify Supabase tables have data:
   ```sql
   SELECT COUNT(*) FROM monitoring.kpi_values;
   ```
2. Test datasource: Configuration → Data Sources → Test
3. Check time range (top-right corner)
4. Inspect panel query: Panel → Edit → Query Inspector

### n8n workflows fail with 401

**Symptom:** Workflow execution error: "Unauthorized"

**Solutions:**

1. Verify `SUPABASE_ANON_KEY` in `.env`
2. Check key validity in Supabase dashboard
3. Restart n8n: `docker-compose restart n8n`
4. Re-enter credentials in n8n UI: Credentials → Supabase

### Docker volume permission issues

**Symptom:** "Permission denied" errors in logs

**Solutions:**

```bash
# Fix Grafana permissions
docker run --rm \
  -v abaco_grafana_data:/data \
  alpine chown -R 472:472 /data

# Fix n8n permissions
docker run --rm \
  -v abaco_n8n_data:/data \
  alpine chown -R 1000:1000 /data
```

## 📚 Additional Resources

- **Full Documentation:** `/docs/OBSERVABILITY.md`
- **Grafana Docs:** https://grafana.com/docs/
- **n8n Docs:** https://docs.n8n.io/
- **Supabase Docs:** https://supabase.com/docs

## 🔒 Security Checklist

Before production deployment:

- [ ] Change all default passwords in `.env`
- [ ] Use strong passwords (16+ characters, mixed case, symbols)
- [ ] Enable HTTPS (reverse proxy with Caddy/nginx/Traefik)
- [ ] Configure firewall rules (allow only necessary ports)
- [ ] Set up SSL certificates (Let's Encrypt)
- [ ] Enable Grafana HTTPS: Set `GF_SERVER_PROTOCOL=https`
- [ ] Enable n8n HTTPS: Set `N8N_PROTOCOL=https`
- [ ] Restrict network access (use VPN or IP whitelist)
- [ ] Enable MFA for Grafana (if available in your version)
- [ ] Review Supabase RLS policies
- [ ] Set up automated backups (daily volume backups)
- [ ] Configure log rotation (Docker logging driver)
- [ ] Enable audit logging for n8n workflows

## 🔄 Updates

### Update Services

```bash
# Pull latest images
docker-compose pull

# Restart with new images
docker-compose up -d

# Verify versions
docker-compose exec grafana grafana-cli --version
docker-compose exec n8n n8n --version
```

### Update Dashboards

1. Edit JSON in `/grafana/dashboards/`
2. Restart Grafana: `docker-compose restart grafana`
3. Dashboards auto-reload within 10 seconds

### Update Workflows

1. Export workflow from n8n UI: Workflow → Download
2. Save to `/n8n/workflows/` (versioned in git)
3. Import updated workflow in n8n UI

---

**Maintained by:** DevOps Team  
**Support:** #observability Slack channel  
**Last Updated:** 2026-01-29
