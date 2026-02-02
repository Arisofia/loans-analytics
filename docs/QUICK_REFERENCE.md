# 🎯 Quick Reference - Platform Features Location

**Fast lookup for common questions and tasks**

---

## ❓ Quick Answers

### Q1: Where is Grafana process?

**Location**: `docker-compose.monitoring.yml`

**Start Command**:
```bash
bash scripts/start_grafana.sh
# OR
docker-compose -f docker-compose.monitoring.yml up -d
```

**Access**: http://localhost:3001  
**Default User**: admin  
**Password**: Set via `GRAFANA_ADMIN_PASSWORD` env var  
**Documentation**: [docs/PROMETHEUS_GRAFANA_QUICKSTART.md](PROMETHEUS_GRAFANA_QUICKSTART.md)

---

### Q2: Where can I see agent feedback (risk, growth, marketing, investor, etc.)?

**3 Ways to View Agent Feedback**:

#### Option 1: Streamlit Dashboard (NEW! ⭐)
```bash
streamlit run streamlit_app.py
```
- Open http://localhost:8501
- Navigate to **"Agent Insights"** page
- View conversation history, analytics, costs
- Export to CSV

#### Option 2: Command Line
```bash
python -m python.multi_agent.cli run-agent risk_analyst --query "Your question"
```

#### Option 3: Raw Files
- Location: `data/agent_outputs/`
- Format: `<timestamp>_<agent_name>_response.json`

**Available Agents**:
- Risk Analyst
- Growth Strategist
- Operations Optimizer
- Compliance Officer
- Collections Specialist
- Fraud Detection
- Pricing Strategist
- Retention Specialist
- Database Designer

**Documentation**: [python/multi_agent/README.md](../python/multi_agent/README.md)

---

### Q3: Where can I upload files to process real data every day?

**4 Upload Options**:

#### Option 1: Streamlit Dashboard (User-Friendly)
```bash
streamlit run streamlit_app.py
```
- Use sidebar "Upload CSV Exports"
- Drag & drop files
- Automatic validation

#### Option 2: Command Line (Automation)
```bash
python scripts/run_data_pipeline.py --input /path/to/loans.csv
```

#### Option 3: Scheduled Daily Processing
```bash
# Linux/Mac: Add to crontab
0 2 * * * cd /path/to/repo && source .venv/bin/activate && python scripts/run_data_pipeline.py --input /data/daily/loans.csv >> logs/pipeline.log 2>&1
```

#### Option 4: API Endpoint (Future)
```bash
# Coming soon
curl -X POST http://localhost:8000/upload -F file=@loans.csv
```

**Documentation**: [docs/USER_OPERATIONS_GUIDE.md](USER_OPERATIONS_GUIDE.md#3-where-can-i-upload-files-for-daily-processing)

---

### Q4: Where are continuous learning and predictions?

**Current Status**:
- ✅ **AI Agents**: 9 specialized LLM agents for insights
- ✅ **KPI Engine**: 19 financial metrics with thresholds
- ✅ **Anomaly Detection**: Statistical monitoring
- ⏳ **Traditional ML**: Roadmap in progress (see below)

**Use AI for Predictions NOW**:
```bash
# Default risk prediction
python -m python.multi_agent.cli --agent risk \
  --query "Predict default probability for loan: $50K, 12 months, DPD history 2 times"

# Churn prediction
python -m python.multi_agent.cli --agent retention \
  --query "Which customers are likely to churn based on 90 days inactive?"

# Pricing recommendation
python -m python.multi_agent.cli --agent pricing \
  --query "Recommend APR for $75K loan, customer risk score 0.15"
```

**ML Development Roadmap**:

| Phase | Timeline | Status |
|-------|----------|--------|
| Phase 1: Data Foundation | Complete | ✅ |
| Phase 2: Model Development | 3-6 months | 📋 Planning |
| - Default Risk Model | Month 1-2 | 📋 |
| - Churn Prediction | Month 2-3 | 📋 |
| - Dynamic Pricing | Month 3-4 | 📋 |
| - Fraud Detection | Month 4-6 | 📋 |
| Phase 3: Continuous Learning | 6-9 months | 📋 |
| - Automated Retraining | TBD | 📋 |
| - Model Monitoring | TBD | 📋 |
| - A/B Testing | TBD | 📋 |

**Documentation**: [docs/ML_CONTINUOUS_LEARNING_ROADMAP.md](ML_CONTINUOUS_LEARNING_ROADMAP.md)

---

### Q5: Why not use all tools to create users and passwords?

**Answer**: Authentication is available! Choose your approach:

#### Option A: Streamlit Built-in Auth (15 min)
**Best for**: Internal teams, quick setup

```bash
# 1. Install
pip install streamlit-authenticator

# 2. Generate password hash
python -c "import bcrypt; print(bcrypt.hashpw(b'your_password', bcrypt.gensalt()).decode())"

# 3. Add to .streamlit/secrets.toml
[passwords]
admin = "$2b$12$hash_here"
analyst = "$2b$12$another_hash"

# 4. See code example in docs/AUTHENTICATION_SETUP_GUIDE.md
```

#### Option B: FastAPI OAuth2 + JWT (1 hour)
**Best for**: Production APIs, external integrations

```bash
# 1. Install
pip install python-jose[cryptography] passlib[bcrypt]

# 2. Generate secret key
openssl rand -hex 32

# 3. Set environment variable
export JWT_SECRET_KEY="your_random_secret"

# 4. Implement endpoints (see docs)
```

#### Option C: Supabase Auth (30 min)
**Best for**: Cloud deployment, managed solution

```bash
# 1. Enable in Supabase dashboard
# 2. Use existing Supabase connection
# 3. Sign up users via API or dashboard
# 4. See code example in docs
```

**Documentation**: [docs/AUTHENTICATION_SETUP_GUIDE.md](AUTHENTICATION_SETUP_GUIDE.md)

---

## 🚀 Getting Started Checklist

- [ ] Clone repository
- [ ] Create Python virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env.local` and configure
- [ ] Start Grafana: `bash scripts/start_grafana.sh`
- [ ] Start dashboard: `streamlit run streamlit_app.py`
- [ ] Upload sample data via dashboard
- [ ] Query AI agents via CLI or dashboard
- [ ] Setup authentication (optional)

---

## 📚 Documentation Index

| Topic | Document | Description |
|-------|----------|-------------|
| **🎯 Operations** | [USER_OPERATIONS_GUIDE.md](USER_OPERATIONS_GUIDE.md) | Complete user guide (START HERE) |
| **🔮 ML & AI** | [ML_CONTINUOUS_LEARNING_ROADMAP.md](ML_CONTINUOUS_LEARNING_ROADMAP.md) | Predictions roadmap |
| **🔐 Security** | [AUTHENTICATION_SETUP_GUIDE.md](AUTHENTICATION_SETUP_GUIDE.md) | User management setup |
| **📊 Monitoring** | [PROMETHEUS_GRAFANA_QUICKSTART.md](PROMETHEUS_GRAFANA_QUICKSTART.md) | Grafana quickstart |
| **🤖 AI Agents** | [../python/multi_agent/README.md](../python/multi_agent/README.md) | Multi-agent system |
| **🔧 Pipeline** | [PIPELINE_ARCHITECTURE.md](PIPELINE_ARCHITECTURE.md) | ETL pipeline details |

---

## 🆘 Common Issues

### Issue: "Command not found: streamlit"
**Solution**: Activate virtual environment
```bash
source .venv/bin/activate
```

### Issue: "Module not found: python.multi_agent"
**Solution**: Ensure you're in project root
```bash
cd /path/to/abaco-loans-analytics
python -m python.multi_agent.cli --help
```

### Issue: "Grafana port already in use"
**Solution**: Change port in `docker-compose.monitoring.yml`
```yaml
ports:
  - "3002:3000"  # Changed from 3001
```

### Issue: "Authentication required"
**Solution**: Setup auth following [AUTHENTICATION_SETUP_GUIDE.md](AUTHENTICATION_SETUP_GUIDE.md)

---

## 📞 Getting Help

1. **Read Documentation**: Check docs/ directory first
2. **Run Demo**: `bash scripts/demo_platform.sh`
3. **Check Logs**: `data/runs/<run_id>/` for pipeline logs
4. **GitHub Issues**: Create issue with [QUESTION] tag
5. **Test System**: Run `pytest` to verify health

---

**Last Updated**: 2026-02-02  
**Version**: 2.0 (Complete Operations Guide)
