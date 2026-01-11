# Local Development Setup Guide

Get the Abaco Analytics Dashboard running on your local machine in under 10 minutes with full tracing support for debugging.

## Prerequisites

- **Python 3.11+** (check with `python --version`)
- **Git** (clone repository)
- **Docker** (optional, for local tracing via Jaeger)
- **10 GB free disk space** (for venv, dependencies, data)

## 1. Clone Repository

```bash
git clone https://github.com/Abaco-Technol/abaco-loans-analytics.git
cd abaco-loans-analytics
```

## 2. Create Python Virtual Environment

### 2.1 Create venv

```bash
python3.11 -m venv .venv
```

### 2.2 Activate venv

**macOS/Linux**:

```bash
source .venv/bin/activate
```

**Windows**:

```bash
.venv\Scripts\activate
```

**Verify activation** (should show `.venv` in prompt):

```bash
which python  # or: where python (Windows)
```

## 3. Install Dependencies

### 3.1 Install from requirements.txt

The root `requirements.txt` delegates to dashboard-specific dependencies:

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**What this installs**:

- Streamlit (dashboard framework)
- Pandas, Numpy, Altair (data processing & visualization)
- Azure SDK (credentials, storage, Key Vault)
- OpenTelemetry (tracing & observability)
- Anthropic, OpenAI, Google (LLM clients)
- Supabase (PostgREST client)

### 3.2 Verify Installation

```bash
python -c "import streamlit; import pandas; import opentelemetry; print('✓ All core packages installed')"
```

## 4. Configure Environment

### 4.1 Copy .env.example → .env

```bash
cp .env.example .env
```

### 4.2 Edit .env with Your Credentials

Open `.env` in your editor:

```bash
nano .env
# or: code .env (VS Code)
# or: vim .env
```

**Required variables** (development):

```ini
# Supabase (data source)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Optional: LLM keys (for AI features)
# Set ANTHROPIC_API_KEY and OPENAI_API_KEY in your environment or GitHub Secrets. Do not commit them to source control.

# Optional: Azure (for cloud tracing)
```

**Getting Supabase credentials**:

1. Go to [supabase.com](https://supabase.com)
2. Project Settings → API
3. Copy `URL` → `SUPABASE_URL`
4. Copy `anon public` key → `SUPABASE_ANON_KEY`
5. Copy `service_role secret` → `SUPABASE_SERVICE_ROLE_KEY`

**Optional: Getting LLM keys**:

- **Anthropic**: [https://console.anthropic.com](https://console.anthropic.com) → API Keys
- **OpenAI**: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- **Google**: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

### 4.3 Verify Configuration

Test Supabase connection:

```bash
python -c "
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_ANON_KEY')

if url and key:
    print(f'✓ Supabase configured: {url[:30]}...')
else:
    print('✗ Missing SUPABASE_URL or SUPABASE_ANON_KEY')
"
```

## 5. Start Dashboard

### 5.1 Launch Streamlit

```bash
streamlit run dashboard/app.py
```

**Expected output**:

```text
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### 5.2 Open Dashboard

- Open browser: `http://localhost:8501`
- Dashboard loads with tracing enabled (logs printed to terminal)
- Check terminal for any warnings/errors

### 5.3 Verify Tracing Initialization

Terminal should show:

```text
[INFO] Tracing initialized: /traces
[INFO] Auto-instrumentation enabled for: httpx, requests, urllib3, sqlite3, psycopg2
```

If tracing errors appear, this is expected in local dev (Azure/Jaeger endpoints not available—see Optional: Local Tracing below).

## 6. Explore Features

### 6.1 Navigate Dashboard

- **Home** — KPI overview and summary metrics
- **Cascade Analysis** — Loan cascade predictions
- **Portfolio Analytics** — KPI trends and analysis
- **Settings** — Configure Supabase connection

### 6.2 Test Data Fetch

Click "Settings" → "Test Supabase Connection":

```text
✓ Supabase connection successful
✓ Found X KPI records
```

### 6.3 View Health Endpoint

```bash
curl "http://localhost:8501/?page=health"
# Expected: 200 OK with "ok"
```

## 7. Optional: Local Tracing Setup

Full observability with local Jaeger instance. Requires Docker.

### 7.1 Start Jaeger Container

```bash
docker run -d \
  --name jaeger \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14250:14250 \
  -p 14268:14268 \
  -p 14269:14269 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest
```

**Verify Jaeger is running**:

```bash
curl http://localhost:16686/api/services
# Expected: {"services":["jaeger-query"]}
```

### 7.2 Configure Tracing Environment

Add to `.env`:

```ini
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
LOG_LEVEL=DEBUG
```

### 7.3 Restart Dashboard

Stop dashboard (Ctrl+C) and restart:

```bash
streamlit run dashboard/app.py
```

Terminal should show:

```text
[INFO] Tracing initialized: http://localhost:4318
[INFO] Auto-instrumentation enabled
```

### 7.4 View Traces in Jaeger UI

1. Open browser: `http://localhost:16686`
2. **Service** dropdown → select `abaco-dashboard`
3. Click **Find Traces**
4. View distributed traces for HTTP requests, database queries

**Example traces**:

- HTTP calls to Supabase API (with query details)
- Streamlit page renders
- Custom spans from dashboard code

### 7.5 Stop Jaeger (when done)

```bash
docker stop jaeger
docker rm jaeger
```

## 8. Common Issues & Solutions

### Issue: "Module not found: streamlit"

**Solution**: Verify venv is activated:

```bash
which python  # Should show .venv path
python -m pip list | grep streamlit
```

If not found, reinstall:

```bash
pip install -r requirements.txt
```

### Issue: "SUPABASE_URL not set"

**Solution**: Ensure `.env` file exists with correct values:

```bash
ls -la .env
grep SUPABASE_URL .env
```

If missing, copy and edit:

```bash
cp .env.example .env
nano .env  # Add your credentials
```

### Issue: "Connection refused: Supabase"

**Causes**:

1. Invalid SUPABASE_URL (typo or project deleted)
2. Network/firewall blocking HTTPS
3. Supabase project is paused

**Solution**:

```bash
# Test connectivity
curl -H "apikey: $SUPABASE_ANON_KEY" \
  "$SUPABASE_URL/rest/v1/kpi_values?limit=1"
# Should return JSON array (may be empty)
```

### Issue: "Streamlit port 8501 already in use"

**Solution**: Use alternate port:

```bash
streamlit run dashboard/app.py --server.port 8502
```

Or kill existing process:

```bash
pkill -f "streamlit run"
sleep 2
streamlit run dashboard/app.py
```

### Issue: Tracing shows "Failed to export spans"

**This is expected** if OTEL_EXPORTER_OTLP_ENDPOINT is not set or Jaeger isn't running:

1. **For local dev without Jaeger**: Ignore this warning (tracing initialized but not exported)
2. **For local tracing**: Follow step 7 to start Jaeger
3. **For Azure**: Set `APPLICATIONINSIGHTS_CONNECTION_STRING` when deployed

## 9. Useful Commands

### 9.1 Development Workflow

```bash
# Activate venv
source .venv/bin/activate

# Install new package
pip install numpy==1.26.0

# Freeze dependencies
pip freeze > requirements-updated.txt

# Run tests
pytest -q

# Check linting
pylint dashboard/app.py
```

### 9.2 Data Inspection

```bash
# Query Supabase from command line
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
response = supabase.table('kpi_values').select('*').limit(5).execute()
print(f'Found {len(response.data)} records')
"
```

### 9.3 Debugging

```bash
# Run dashboard with debug logging
LOG_LEVEL=DEBUG streamlit run dashboard/app.py

# Watch logs from another terminal
tail -f debug.log

# Inspect Python version/paths
python -c "import sys; print(sys.version); print(sys.executable)"
```

## 10. Next Steps

1. **Read TRACING.md** — Detailed tracing setup and observability patterns
2. **Explore data** — Check Supabase schema and sample data in Settings
3. **Extend dashboard** — Add new Streamlit pages in `dashboard/pages/`
4. **Test changes** — Run `pytest -q` before committing
5. **Deploy to Azure** — Follow [DEPLOYMENT.md](./DEPLOYMENT.md) for cloud deployment

## 11. Repository Structure

```text
abaco-loans-analytics/
├── dashboard/               # Streamlit app
│   ├── app.py              # Main entry point
│   ├── pages/              # Multi-page UI
│   └── requirements.txt     # Dashboard deps
├── src/                 # Shared modules
│   ├── tracing_setup.py    # OpenTelemetry config
│   ├── validation.py       # Data validation
│   └── compliance.py       # PII masking
├── scripts/                # Utility scripts
│   └── validate_azure_connection.py
├── .github/workflows/      # CI/CD automation
│   ├── deploy-dashboard.yml
│   └── validate-deployment.yml
├── docs/                   # Documentation
│   ├── DEPLOYMENT.md       # Azure setup guide
│   ├── TRACING.md          # Observability guide
│   └── LOCAL_SETUP.md      # This file
├── requirements.txt        # Root dependencies
└── .env.example            # Configuration template
```

## 12. Getting Help

- **Dashboard issues**: Check `http://localhost:8501/?page=health`
- **Tracing issues**: Enable `LOG_LEVEL=DEBUG` and check terminal
- **Supabase issues**: Test connection in Settings tab
- **Azure deployment**: Refer to [DEPLOYMENT.md](./DEPLOYMENT.md)
- **Team chat**: Reach out to @data-engineering or @analytics-ops
