# Supabase Setup Guide - Data Pipeline Integration

**Status**: ✅ Code implemented, awaiting Supabase credentials configuration  
**Last Updated**: 2026-01-31  
**Owner**: Data Engineering Team

---

## Overview

This guide walks you through configuring Supabase to receive automated KPI data from the pipeline, enabling the dashboard to display real-time metrics.

### Architecture Flow

```
Local/Scheduled Pipeline → Supabase PostgreSQL → Streamlit Dashboard (Azure) → Real-time KPI Visibility
```

---

## Prerequisites

- ✅ Supabase project created (Project ID: `goxdevkqozomyhsyxhte`)
- ✅ Pipeline code with database write functionality (implemented)
- ⏳ Supabase API keys (need to be configured)

---

## Step 1: Obtain Supabase API Keys

### 1.1 Navigate to Supabase Dashboard

1. Go to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
2. Login with your Supabase account

### 1.2 Copy Required Keys

You need **three keys** from the API settings page:

| Key Name                          | Environment Variable                           | Purpose                      | Security Level              |
| --------------------------------- | ---------------------------------------------- | ---------------------------- | --------------------------- |
| **Project URL**                   | `NEXT_PUBLIC_SUPABASE_URL`                     | Database connection endpoint | Public (safe)               |
| **anon public** (publishable key) | `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY` | Client-side queries          | Public (safe)               |
| **service_role** (secret)         | `SUPABASE_SERVICE_ROLE_KEY`                    | Server-side operations       | **CRITICAL - NEVER EXPOSE** |

---

## Step 2: Configure Local Environment

### 2.1 Update `.env.local` File

Open `/Users/jenineferderas/Documents/Documentos - MacBook Pro (6)/abaco-loans-analytics/.env.local`

Replace the placeholder values:

```dotenv
# PUBLIC KEYS (safe to expose)
NEXT_PUBLIC_SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY=<paste-your-anon-public-key-here>

# SECRET KEYS (server-side only - NEVER commit to git)
SUPABASE_SERVICE_ROLE_KEY=<paste-your-service-role-key-here>

# Compatibility mappings (auto-configured via ${} syntax)
SUPABASE_URL=${NEXT_PUBLIC_SUPABASE_URL}
SUPABASE_ANON_KEY=${NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY}
```

### 2.2 Verify Configuration

Run the verification script:

```bash
python scripts/data/setup_supabase_tables.py --verify-only
```

**Expected output:**

```
✓ Loaded environment from .env.local
✓ Supabase URL: https://goxdevkqozomyhsyxhte.supabase.co
✓ Connected to Supabase
✓ Table kpi_timeseries_daily exists and is accessible
```

---

## Step 3: Create Database Table

### 3.1 Apply SQL Migration

The migration file is located at: `db/migrations/002_create_kpi_timeseries_daily.sql`

**Option A: Via Supabase Dashboard (Recommended)**

1. Open: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/editor
2. Click **SQL Editor** in the sidebar
3. Click **New Query**
4. Copy the entire contents of `db/migrations/002_create_kpi_timeseries_daily.sql`
5. Paste into the SQL Editor
6. Click **Run** button

**Option B: Via Supabase CLI**

```bash
# Install Supabase CLI (if not installed)
brew install supabase/tap/supabase

# Login
supabase login

# Link to project
supabase link --project-ref goxdevkqozomyhsyxhte

# Apply migration
supabase db execute -f db/migrations/002_create_kpi_timeseries_daily.sql
```

### 3.2 Verify Table Creation

Run the verification script again:

```bash
python scripts/data/setup_supabase_tables.py --verify-only
```

---

## Step 4: Test Pipeline with Database Writes

### 4.1 Enable Database Writes

Database writes are **already enabled** in `config/pipeline.yml`:

```yaml
database:
  enabled: true
  type: supabase
  table: kpi_timeseries_daily
  url: "${SUPABASE_URL}"
  key: "${SUPABASE_ANON_KEY}"
```

### 4.2 Run Test Pipeline

```bash
python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv
```

**Expected output:**

```
[Phase 4/4] Output Phase
  ✓ Exported Parquet: data/outputs/20260131_XXXXXX/kpi_results.parquet
  ✓ Exported CSV: data/outputs/20260131_XXXXXX/kpi_results.csv
  ✓ Writing 19 KPI records to Supabase table: kpi_timeseries_daily
  ✓ Inserted batch 0-19
  ✓ Successfully wrote 19 KPI records to database

Pipeline execution completed successfully!
```

### 4.3 Verify Data in Supabase

1. Open: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/editor
2. Click **Table Editor** → select `kpi_timeseries_daily`
3. You should see 19 rows with KPIs like:
   - `par_30`, `par_90`, `npl_rate`
   - `portfolio_rotation`, `collection_rate_6m`
   - `average_loan_size`, `total_aum`

---

## Step 5: Update Azure Container with Credentials

### 5.1 Why This Step?

The Azure container running the dashboard needs Supabase credentials to query KPI data.

### 5.2 Add Credentials to Azure Container

```bash
# Navigate to project directory
cd /Users/jenineferderas/Documents/Documentos\ -\ MacBook\ Pro\ \(6\)/abaco-loans-analytics

# Update container environment variables
az container create \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --name abaco-analytics-streamlit \
  --image ghcr.io/arisofia/abaco-loans-analytics:latest \
  --dns-name-label abaco-analytics \
  --ports 8501 \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co \
    SUPABASE_ANON_KEY=<your-anon-key> \
    STREAMLIT_SERVER_PORT=8501
```

**⚠️ Security Note**: Never commit the anon key to git! Use Azure Key Vault for production.

### 5.3 Verify Dashboard Data

1. Navigate to: http://4.248.240.207:8501
2. The dashboard should now display KPIs instead of "Logs directory not found"
3. Check for metrics like:
   - **Portfolio Metrics**: PAR-30, PAR-90, NPL Rate
   - **Operational Metrics**: Collection Rate, Portfolio Rotation
   - **Financial Metrics**: Total AUM, Average Loan Size

---

## Step 6: Automate Pipeline Execution

### Option A: Manual Execution (Canonical)

```bash
python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv
```

### Option B: Local Cron Job

Edit crontab:

```bash
crontab -e
```

Add:

```cron
# Run pipeline daily at 6 AM
0 6 * * * cd /Users/jenineferderas/Documents/Documentos\ -\ MacBook\ Pro\ \(6\)/abaco-loans-analytics && .venv/bin/python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv >> logs/pipeline_cron.log 2>&1
```

---

## Troubleshooting

### Issue 1: "Supabase credentials not configured in environment"

**Cause**: Pipeline can't find `SUPABASE_URL` or `SUPABASE_ANON_KEY`

**Solution**:

1. Verify `.env.local` has the correct keys (see Step 2.1)
2. Check that `.env` references `.env.local` variables correctly
3. Run: `source .venv/bin/activate && python -c "import os; print(os.getenv('SUPABASE_URL'))"`

### Issue 2: "Invalid API key"

**Cause**: Wrong key type or expired key

**Solution**:

1. Verify you're using the **anon public** key (not service_role) in pipeline
2. Regenerate keys: Supabase Dashboard → Settings → API → Regenerate
3. Update `.env.local` with new key

### Issue 3: "Table kpi_timeseries_daily does not exist"

**Cause**: Migration not applied

**Solution**:

1. Follow Step 3.1 to create the table
2. Verify with: `python scripts/data/setup_supabase_tables.py --verify-only`

### Issue 4: Dashboard shows old data

**Cause**: Pipeline not running or not writing to Supabase

**Solution**:

1. Check pipeline logs: `tail -f logs/pipeline.log`
2. Verify database writes: Check `run_date` column in Supabase table
3. Force dashboard refresh: Add `?nocache=1` to URL

---

## Security Best Practices

### ✅ DO

- Store `service_role` key in `.env.local` (gitignored)
- Use `anon` key for pipeline writes (RLS policies protect data)
- Rotate keys every 90 days
- Enable Row Level Security (RLS) on Supabase tables
- Use Azure Key Vault for container environment variables

### ❌ DON'T

- Never commit `.env.local` to git
- Never expose `service_role` key in client-side code
- Never hardcode credentials in scripts
- Never share keys in chat/email (use encrypted vault)

---

## Next Steps

After completing setup:

1. **Data Quality Monitoring**: Set up alerts for missing pipeline runs
2. **Performance Optimization**: Add database indexes for dashboard queries
3. **Historical Analysis**: Import past KPI data to Supabase
4. **Multi-environment Setup**: Create separate Supabase projects for dev/staging/prod

---

## Support

**Questions?** Contact:

- **Data Engineering**: Review `docs/OPERATIONS.md`
- **Supabase Issues**: https://supabase.com/docs
- **Dashboard Issues**: Review `README.md`

**Related Documentation**:

- [DEPLOYMENT_OPERATIONS_GUIDE.md](./PRODUCTION_DEPLOYMENT_GUIDE.md) - Azure container management
- [DATA_GOVERNANCE.md](./DATA_GOVERNANCE.md) - Data quality standards
- [MONITORING_QUICK_START.md](./OBSERVABILITY.md) - Observability setup
