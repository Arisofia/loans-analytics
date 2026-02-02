# 🎯 User Operations Guide - Abaco Loans Analytics

**Complete guide to accessing all system features: Grafana, Agents, File Uploads, ML Predictions, and Authentication**

---

## 📊 1. WHERE IS GRAFANA? - Monitoring & Metrics Dashboard

### Quick Start Grafana

Grafana is configured and ready to deploy via Docker Compose:

```bash
# Navigate to project root
cd /home/runner/work/abaco-loans-analytics/abaco-loans-analytics

# Load environment variables (contains Supabase credentials)
source scripts/load_env.sh

# Set Grafana admin password
export GRAFANA_ADMIN_PASSWORD="your_secure_password_here"

# Start Grafana + Prometheus + Alertmanager stack
docker-compose -f docker-compose.monitoring.yml up -d

# View logs
docker-compose -f docker-compose.monitoring.yml logs -f grafana
```

### Access Grafana Dashboard

```
URL: http://localhost:3001
Username: admin
Password: (whatever you set in GRAFANA_ADMIN_PASSWORD)
```

### What You Get

- **Prometheus Metrics**: 520+ Supabase database metrics
- **Pre-configured Dashboards**: Import dashboard ID 19822 (Supabase Overview)
- **Custom Dashboards**: Located in `grafana/dashboards/`
- **Alerting**: Configured in `config/rules/supabase_alerts.yml`

### Detailed Documentation

- Setup Guide: `docs/PROMETHEUS_GRAFANA_QUICKSTART.md`
- Configuration: `docker-compose.monitoring.yml`
- Dashboards: `grafana/dashboards/`
- Alert Rules: `config/rules/`

---

## 🤖 2. WHERE CAN I SEE AGENT FEEDBACK?

### Multi-Agent System Overview

The platform includes **9 specialized AI agents**:

1. **Risk Analyst** - Portfolio risk assessment
2. **Growth Strategist** - Expansion opportunities
3. **Operations Optimizer** - Process efficiency
4. **Compliance Officer** - Regulatory adherence
5. **Collections Specialist** - Recovery strategies
6. **Fraud Detection** - Anomaly identification
7. **Pricing Strategist** - Rate optimization
8. **Retention Specialist** - Customer lifecycle
9. **Database Designer** - Schema optimization

### Using Agents via CLI

```bash
# Activate virtual environment
source .venv/bin/activate

# Run single agent query
python -m python.multi_agent.cli \
  --agent risk \
  --query "Analyze portfolio risk for loans with DPD > 30 days"

# Run pre-built scenario
python -m python.multi_agent.cli \
  --scenario "monthly_portfolio_health" \
  --data data/raw/sample_loans.csv

# List all available scenarios
python -m python.multi_agent.cli --list-scenarios
```

### Viewing Agent Feedback in Streamlit Dashboard

**COMING SOON: Agent History Viewer**

The Streamlit dashboard will include an "Agent Insights" page showing:
- Past agent conversations
- Query history with timestamps
- Agent recommendations and actions taken
- Export capability for reports

**Current Access Method:**
Agent outputs are saved to:
```
data/agent_outputs/<timestamp>_<agent_name>_response.json
```

### Agent Configuration

- Agent Definitions: `python/multi_agent/agents.py`
- Scenarios: `python/multi_agent/orchestrator.py`
- Documentation: `python/multi_agent/README.md`

---

## 📤 3. WHERE CAN I UPLOAD FILES FOR DAILY PROCESSING?

### Option 1: Streamlit Dashboard (Recommended for Users)

```bash
# Start Streamlit dashboard
streamlit run streamlit_app.py
```

**Access**: `http://localhost:8501`

**Features**:
- Drag-and-drop CSV upload
- Automatic column mapping
- Real-time data validation
- KPI calculation preview
- Export processed data

**Supported File Types**:
- CSV files with loan data
- CSV files with customer data
- Multiple files can be uploaded simultaneously

### Option 2: Command Line (For Automation)

```bash
# Run full pipeline with your data file
python scripts/run_data_pipeline.py \
  --input /path/to/your/daily_loans.csv \
  --output data/processed/

# Dry-run (validation only)
python scripts/run_data_pipeline.py \
  --input /path/to/your/daily_loans.csv \
  --mode dry-run
```

### Option 3: FastAPI Endpoint (For Integration)

**COMING SOON: Enhanced API Endpoints**

```bash
# Start FastAPI server
cd python/apps/analytics/api
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoint**:
```bash
# Upload file via API
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/loans.csv"
```

### Automated Daily Processing Setup

**Option A: Scheduled Script (Linux/Mac)**

Create a cron job:
```bash
# Edit crontab
crontab -e

# Add daily processing at 2 AM
0 2 * * * cd /path/to/abaco-loans-analytics && source .venv/bin/activate && python scripts/run_data_pipeline.py --input /data/daily/loans_$(date +\%Y\%m\%d).csv >> logs/pipeline.log 2>&1
```

**Option B: GitHub Actions (Cloud)**

See: `.github/workflows/scheduled_pipeline.yml` (to be created)

**Option C: Azure Functions**

Configuration exists in:
- `host.json`
- `azure.yaml`
- Deploy guide: `docs/runbooks/deployment-blocked.md`

### Data Requirements

Your daily upload files must include these columns:
- See: `config/validation/required_columns.yaml`
- Validation: Automatic during ingestion phase

---

## 🔮 4. WHERE ARE CONTINUOUS LEARNING AND PREDICTIONS?

### Current Status: Rule-Based + AI Hybrid

**Active Capabilities**:
1. **Multi-Agent AI System**: Uses LLMs (OpenAI/Anthropic/Gemini) for insights
2. **KPI Calculation Engine**: 19 financial metrics with trend analysis
3. **Anomaly Detection**: Statistical thresholds and guardrails

**What's NOT Yet Implemented**:
- Traditional ML models (scikit-learn, XGBoost)
- Model retraining pipelines
- Prediction APIs (default risk, churn, etc.)

### Roadmap for ML/Predictions

**Phase 1: Data Foundation (Current)**
- ✅ Historical data storage (Supabase)
- ✅ KPI time series tracking
- ✅ Data quality monitoring

**Phase 2: Model Development (Next 3-6 months)**
- [ ] Default risk prediction model
- [ ] Customer churn prediction
- [ ] Dynamic pricing optimization
- [ ] Fraud detection scoring

**Phase 3: Continuous Learning (Future)**
- [ ] Automated model retraining
- [ ] A/B testing framework
- [ ] Model performance monitoring
- [ ] Drift detection

### Using Current AI Capabilities

```bash
# Risk prediction using AI agents
python -m python.multi_agent.cli \
  --agent risk \
  --query "Predict default probability for loans with DPD > 60"

# Growth forecasting
python -m python.multi_agent.cli \
  --agent growth \
  --query "Forecast TPV for next quarter based on current trends"

# Fraud detection
python -m python.multi_agent.cli \
  --agent fraud \
  --query "Identify suspicious patterns in recent loan applications"
```

### Setting Up Predictions (Developer Guide)

**Directory Structure for ML Models**:
```
models/
├── risk/
│   ├── default_predictor.pkl
│   ├── training_data.parquet
│   └── config.yaml
├── churn/
└── pricing/
```

**Recommended Stack**:
- Training: scikit-learn, XGBoost, LightGBM
- Deployment: MLflow, FastAPI
- Monitoring: Evidently AI, Prometheus

**Documentation to Create**:
- `docs/ML_DEVELOPMENT_GUIDE.md` (to be written)
- `docs/MODEL_DEPLOYMENT.md` (to be written)

---

## 🔐 5. USER AUTHENTICATION & CREDENTIAL MANAGEMENT

### Current Status: No Built-in Auth

The current implementation does NOT include authentication because:
1. Designed for internal team use initially
2. Running locally (localhost access only)
3. Focused on data pipeline and analytics first

### Adding Authentication - Options

#### Option A: Streamlit Built-in Auth (Simplest)

Create `.streamlit/secrets.toml`:
```toml
[passwords]
# Use bcrypt hashed passwords
admin = "$2b$12$KIXhs7D0zV5j9v7fXvUOxe7YR7Jx6B9Z1k2L3M4N5O6P7Q8R9S0T1"
analyst = "$2b$12$differenthashhere..."

[roles]
admin = ["admin", "analyst", "upload"]
analyst = ["analyst"]
```

Add to `streamlit_app.py`:
```python
import streamlit_authenticator as stauth

authenticator = stauth.Authenticate(
    st.secrets["passwords"],
    "abaco_app",
    "abaco_secret_key",
    cookie_expiry_days=30
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.write(f'Welcome *{name}*')
    # Your dashboard code here
elif authentication_status == False:
    st.error('Username/Password is incorrect')
```

#### Option B: FastAPI OAuth2 (Production-Grade)

```python
# python/apps/analytics/api/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Add endpoints for:
# - POST /token - Login
# - POST /users - Create user (admin only)
# - GET /users/me - Get current user
# - PUT /users/me/password - Change password
```

#### Option C: Supabase Auth (Cloud-Ready)

Already configured Supabase connection - can use Supabase Auth:

```python
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

# Sign up
user = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure_password"
})

# Sign in
session = supabase.auth.sign_in_with_password({
    "email": "user@example.com", 
    "password": "secure_password"
})
```

### Creating User Credentials

**Step 1: Choose Method**
- For local use: Option A (Streamlit)
- For API integrations: Option B (FastAPI OAuth2)
- For cloud deployment: Option C (Supabase Auth)

**Step 2: Generate Passwords**
```bash
# Install bcrypt
pip install bcrypt

# Generate hashed password
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"
```

**Step 3: Define Roles**
Common roles for fintech analytics:
- `admin`: Full system access
- `analyst`: View dashboards, run reports
- `uploader`: Upload data files only
- `viewer`: Read-only access

### Security Best Practices

✅ **DO**:
- Use environment variables for secrets (`.env.local`)
- Hash all passwords (bcrypt, argon2)
- Implement role-based access control (RBAC)
- Use HTTPS in production
- Rotate credentials every 90 days
- Enable 2FA for admin accounts

❌ **DON'T**:
- Store passwords in plain text
- Commit credentials to Git
- Use the same password for multiple accounts
- Share service account credentials
- Expose admin interfaces publicly without auth

---

## 🚀 Quick Start Checklist

### First-Time Setup (15 minutes)

```bash
# 1. Clone and setup
cd /path/to/abaco-loans-analytics
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env.local
# Edit .env.local with your credentials

# 3. Start Grafana monitoring
export GRAFANA_ADMIN_PASSWORD="secure_password"
docker-compose -f docker-compose.monitoring.yml up -d

# 4. Start Streamlit dashboard
streamlit run streamlit_app.py

# 5. Test agent system
python -m python.multi_agent.cli --list-scenarios
```

### Daily Operations

```bash
# Upload new data via Streamlit
# → Open http://localhost:8501
# → Use "Upload CSV Exports" in sidebar

# Run automated pipeline
python scripts/run_data_pipeline.py --input data/raw/today.csv

# Query AI agents
python -m python.multi_agent.cli --agent risk --query "Your question here"

# View metrics in Grafana
# → Open http://localhost:3001
```

---

## 📚 Related Documentation

| Topic | Document |
|-------|----------|
| Grafana Setup | `docs/PROMETHEUS_GRAFANA_QUICKSTART.md` |
| Multi-Agent System | `python/multi_agent/README.md` |
| Pipeline Architecture | `docs/PIPELINE_ARCHITECTURE.md` |
| KPI Definitions | `config/kpis/kpi_definitions.yaml` |
| API Reference | `docs/API_REFERENCE.md` |
| Deployment | `docs/runbooks/deployment-blocked.md` |

---

## ❓ Troubleshooting

### Grafana Not Starting
```bash
# Check Docker logs
docker-compose -f docker-compose.monitoring.yml logs grafana

# Common issues:
# - Port 3001 already in use → Change in docker-compose.monitoring.yml
# - Missing GRAFANA_ADMIN_PASSWORD → Set environment variable
```

### Agent Queries Failing
```bash
# Check API keys are set
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test connectivity
python -m python.multi_agent.cli --agent risk --query "test"
```

### File Upload Not Working
```bash
# Ensure Streamlit is running
ps aux | grep streamlit

# Check file permissions
chmod 755 data/raw/

# Verify file format
python python/validation.py data/raw/your_file.csv
```

---

## 🆘 Getting Help

1. **Documentation**: Check `docs/` directory
2. **Issues**: Create GitHub issue with [QUESTION] tag
3. **Logs**: Check `logs/pipeline.log` and `data/runs/<run_id>/`
4. **Tests**: Run `pytest` to verify system health

---

**Last Updated**: 2026-02-02  
**Maintainer**: Abaco Analytics Team
