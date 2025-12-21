# Streamlit Dashboard Deployment Guide

## Overview

This guide covers deploying a Streamlit dashboard alongside the Next.js application for real-time risk assessment and Google Drive data ingestion.

**Important**: This workspace runs on Debian GNU/Linux 12 (bookworm) with Node.js 20.x and npm as the canonical package manager.

## Local Development

### Prerequisites

- Python 3.11+
- Google Cloud service account with Drive API access
- Supabase project with configured secrets
- Node.js 20.x (for Next.js companion app)
- npm (officially supported package manager)

### Setup

1. **Install Python dependencies**

   ```bash
   pip install -r streamlit_requirements.txt
   ```

2. **Configure Streamlit secrets**

   Create `.streamlit/secrets.toml`:

   ```toml
   # Supabase Configuration
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_SERVICE_KEY = "your-service-role-key"

   # Google Drive Integration
   GDRIVE_FOLDER_ID = "your-google-drive-folder-id"
   GDRIVE_SERVICE_ACCOUNT = '{"type":"service_account","project_id":"...","private_key":"..."}'

   # Optional: API Configuration
   STREAMLIT_SERVER_PORT = 8501
   STREAMLIT_SERVER_ADDRESS = "0.0.0.0"
   ```

   ⚠️ **Security**: Never commit `.streamlit/secrets.toml` to version control. It should be in `.gitignore`.

3. **Run locally**

   ```bash
   streamlit run streamlit_app.py
   ```

   Application will be available at `http://localhost:8501`

## Deployment Options

### Option 1: Streamlit Cloud (Recommended)

**Advantages:**

- Free tier available
- Simple GitHub integration
- Automatic HTTPS
- Built-in monitoring

**Steps:**

1. **Push to GitHub**

   ```bash
   git add streamlit_app.py streamlit_requirements.txt .streamlit/config.toml
   git commit -m "feat: add Streamlit dashboard"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Click "New app"
   - Select your repository
   - Choose main branch
   - Set main file path: `streamlit_app.py`

3. **Configure Secrets**
   - Go to App settings (⋮ menu) → Secrets
   - Paste the contents of `.streamlit/secrets.toml`
   - Secrets are automatically encrypted

### Option 2: Railway Deployment

**Advantages:**

- Supports custom Docker configurations
- Environment variable management
- Persistent storage options
- Production-grade infrastructure

**Steps:**

1. **Create Railway Dockerfile**

   ```dockerfile
   // filepath: Dockerfile.streamlit
   FROM python:3.11-slim

   WORKDIR /app

   # Copy requirements and install dependencies
   COPY streamlit_requirements.txt .
   RUN pip install --no-cache-dir -r streamlit_requirements.txt

   # Copy application files
   COPY streamlit_app.py .
   COPY .streamlit .streamlit

   # Expose Streamlit port
   EXPOSE 8501

   # Health check
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD curl -f http://localhost:8501/_stcore/health || exit 1

   # Start Streamlit
   CMD ["streamlit", "run", "streamlit_app.py", \
        "--server.port=8501", \
        "--server.address=0.0.0.0", \
        "--logger.level=info"]
   ```

2. **Deploy to Railway**

   ```bash
   # Install Railway CLI globally
   npm install -g @railway/cli

   # Login to Railway
   railway login

   # Deploy with project configuration
   railway init
   railway up
   ```

3. **Set Environment Variables in Railway Dashboard**

   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key
   GDRIVE_FOLDER_ID=your-folder-id
   GDRIVE_SERVICE_ACCOUNT={"type":"service_account",...}
   ```

### Option 3: Docker Compose (Local/Self-hosted)

**Advantages:**

- Full control over infrastructure
- Local testing before production
- Easy scaling with multiple services

**Configuration:**

```yaml
// filepath: docker-compose.streamlit.yml
version: "3.8"

services:
  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    container_name: abaco-streamlit
    ports:
      - "8501:8501"
    environment:
      STREAMLIT_SERVER_PORT: 8501
      STREAMLIT_SERVER_ADDRESS: 0.0.0.0
      SUPABASE_URL: ${SUPABASE_URL}
      SUPABASE_SERVICE_KEY: ${SUPABASE_SERVICE_KEY}
      GDRIVE_FOLDER_ID: ${GDRIVE_FOLDER_ID}
      GDRIVE_SERVICE_ACCOUNT: ${GDRIVE_SERVICE_ACCOUNT}
    volumes:
      - ./.streamlit/secrets.toml:/app/.streamlit/secrets.toml:ro
      - ./streamlit_app.py:/app/streamlit_app.py
    restart: unless-stopped
    networks:
      - abaco-network

  # Optional: Next.js companion application
  nextjs:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: abaco-nextjs
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_SUPABASE_URL: ${NEXT_PUBLIC_SUPABASE_URL}
      NEXT_PUBLIC_SUPABASE_ANON_KEY: ${NEXT_PUBLIC_SUPABASE_ANON_KEY}
      SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY}
    depends_on:
      - streamlit
    restart: unless-stopped
    networks:
      - abaco-network

networks:
  abaco-network:
    driver: bridge
```

**Run with:**

```bash
# Create .env.docker file with your environment variables
docker-compose -f docker-compose.streamlit.yml up -d
```

## Features

### Google Drive Ingestion

- **Real-time file processing** from configured Drive folder
- **Format support**: Excel (.xlsx), Google Sheets, CSV
- **Automatic data normalization**:
  - Column name standardization
  - Data type detection and conversion
  - Conflict resolution using deterministic keys

### Risk Assessment Dashboard

**KPI Metrics:**

- High-risk client count
- Days Past Due (DPD) statistics
- Loan-to-Value (LTV) distribution
- Collection rate

**Visualizations:**

- High-risk portfolio table (sortable by severity)
- DPD distribution histogram
- LTV distribution histogram
- Risk matrix scatter plot (DPD vs LTV vs Risk Severity)

### Automated Refresh

- **Daily ML feature refresh** at 6 AM UTC via Supabase cron job
- **Refresh logging** to database for audit trail
- **Error notifications** to Supabase logs

## Monitoring

### Check Cron Job Status

```sql
SELECT * FROM cron.job;
```

### View Refresh Logs

```sql
SELECT
  refresh_date,
  status,
  error_message,
  processed_records
FROM ml_refresh_log
ORDER BY refresh_date DESC
LIMIT 10;
```

### Monitor Streamlit Application

**Local:**

```bash
# Check container logs
docker logs abaco-streamlit -f
```

**Streamlit Cloud:**

- View in deployment dashboard
- Check "Logs" tab for errors

**Railway:**

```bash
railway logs --service streamlit
```

## Troubleshooting

### "No files found in shared folder"

- Verify `GDRIVE_FOLDER_ID` is correct (not a filename)
- Confirm service account has read access to folder
- Ensure files are in the root of the folder (not subfolders)
- Check service account email is added to folder sharing

### "ml_feature_snapshots table not found"

- Run data ingestion first via Streamlit UI
- Verify `refresh_ml_features()` procedure exists in Supabase
- Confirm all database migrations have been applied
- Check Supabase service role has table permissions

### "Supabase connection failed"

```bash
# Test connection locally
python3 -c "import supabase; print('Supabase import successful')"

# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY
```

- Verify `SUPABASE_URL` format (https://xxx.supabase.co)
- Check `SUPABASE_SERVICE_KEY` is not empty
- Ensure Supabase project is active (not paused)
- Verify network connectivity to Supabase

### "Permission denied for Google Drive access"

- Verify service account JSON is valid
- Check that service account email has folder access
- Ensure Google Drive API is enabled in Google Cloud Console
- Verify service account has "Editor" or "Viewer" role

## Security Best Practices

✅ **Secrets Management**

- Use `.streamlit/secrets.toml` for local development (add to `.gitignore`)
- Use deployment platform secrets (Streamlit Cloud, Railway, etc.)
- Never commit secrets to version control
- Use environment variables in all deployment scenarios

✅ **Google Drive Access**

- Use service account (not personal account)
- Grant read-only access to specific folder only
- Rotate service account keys regularly
- Audit service account activity logs

✅ **Supabase Access**

- Use service role key only in backend/Streamlit
- Use public anon key only in Next.js frontend
- Enable Row Level Security (RLS) on all tables
- Audit Supabase access logs regularly

✅ **Code Security**

- No hardcoded credentials in source code
- Use environment variables for all secrets
- Validate all user inputs in Streamlit forms
- Implement proper error handling without exposing internals
- Follow Copilot security guidelines from `.github/copilot-instructions.md`

## Cost Estimation

| Service          | Free Tier | Paid Tier    | Notes                   |
| ---------------- | --------- | ------------ | ----------------------- |
| Streamlit Cloud  | 1 app     | $5/app/month | Verified email required |
| Google Drive API | Free      | Free         | Included with workspace |
| Supabase         | 500MB DB  | $25+/month   | Scales with usage       |
| Railway          | None      | $5+/month    | Pay-as-you-go available |

## Integration with Next.js Application

The Streamlit dashboard complements the Next.js application:

| Feature                 | Next.js App      | Streamlit Dashboard |
| ----------------------- | ---------------- | ------------------- |
| User authentication     | ✅ (Supabase)    | ❌ (Admin only)     |
| Risk dashboard          | ✅ (Real-time)   | ✅ (Analytics)      |
| Data ingestion          | ❌               | ✅ (Google Drive)   |
| Portfolio visualization | ✅ (Interactive) | ✅ (Statistical)    |
| ML predictions          | ✅ (API-based)   | ✅ (Direct)         |

## Environment Notes

- **OS**: Debian GNU/Linux 12 (bookworm)
- **Python**: 3.11+
- **Node.js**: 20.x (for Next.js)
- **Package Manager**: npm (officially supported)
- **Streamlit Version**: Latest stable

## Next Steps

1. **Set up Google Drive integration** following Google Cloud setup guide
2. **Configure Supabase** with required tables and Row Level Security
3. **Deploy Streamlit** using your preferred option
4. **Test data ingestion** with sample files
5. **Monitor** refresh jobs and error logs
6. **Scale** infrastructure as needed

## Additional Resources

- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Cloud Deployment](https://docs.streamlit.io/streamlit-cloud/deploy-your-app)
- [Railway Documentation](https://docs.railway.app)
- [Google Drive API](https://developers.google.com/drive/api)
- [Supabase Documentation](https://supabase.com/docs)
- [GitHub Copilot Instructions](./.github/copilot-instructions.md)

---

**Last Updated**: 2025-01-06  
**Environment**: Debian 12 (bookworm), Node.js 20.x, npm, Python 3.11+  
**Deployment Options**: Streamlit Cloud, Railway, Docker Compose
