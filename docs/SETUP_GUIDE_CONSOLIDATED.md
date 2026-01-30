# 🚀 Setup Guide - Consolidated

> **Purpose**: Single source of truth for all project setup procedures  
> **Replaces**: 12 scattered SETUP files (2,478 lines total)  
> **Date**: January 30, 2026

---

## 📑 Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Python Environment Setup](#python-environment-setup)
3. [Code Quality Setup](#code-quality-setup)
4. [Integration Tests Setup](#integration-tests-setup)
5. [Monitoring & Alertmanager Setup](#monitoring--alertmanager-setup)
6. [Secrets & Environment Setup](#secrets--environment-setup)
7. [Azure Cloud Setup](#azure-cloud-setup)
8. [Supabase Database Setup](#supabase-database-setup)
9. [Workspace Configuration](#workspace-configuration)

---

## 1. Local Development Setup

### Quick Start (5 minutes)

```bash
# Clone repository
git clone https://github.com/Arisofia/abaco-loans-analytics.git
cd abaco-loans-analytics

# Setup Python environment
make setup

# Verify installation
make test
```

### Prerequisites

- **Python**: 3.9+ (check: `python3 --version`)
- **Node.js**: 18+ (check: `node --version`)
- **Docker**: Latest (check: `docker --version`)
- **Git**: 2.x+ (check: `git --version`)

### Installation Steps

1. **Clone and enter directory**

   ```bash
   git clone https://github.com/Arisofia/abaco-loans-analytics.git
   cd abaco-loans-analytics
   ```

2. **Create virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development tools
   ```

4. **Install pre-commit hooks**

   ```bash
   pre-commit install
   ```

5. **Verify setup**
   ```bash
   make test
   make lint
   ```

---

## 2. Python Environment Setup

### Virtual Environment

```bash
# Create
python3 -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

### Dependencies

- **Production**: `requirements.txt`
- **Development**: `requirements-dev.txt`
- **Lock file**: `requirements.lock.txt` (frozen versions)

### Common Issues

**Issue**: `ModuleNotFoundError`  
**Solution**: Ensure virtual environment is activated, reinstall dependencies

**Issue**: Version conflicts  
**Solution**: Use `requirements.lock.txt`: `pip install -r requirements.lock.txt`

---

## 3. Code Quality Setup

### Automated via Makefile

```bash
make format      # Black + isort formatting
make lint        # Ruff, flake8, pylint
make type-check  # Mypy static typing
```

### Pre-commit Hooks

Automatically runs on `git commit`:

- Secret scanning (detect-secrets)
- Code formatting (black, isort)
- Linting (ruff, flake8)
- Type checking (mypy)

**Manual run**:

```bash
pre-commit run --all-files
```

### Configuration Files

- `.pre-commit-config.yaml` - Pre-commit hooks
- `pyproject.toml` - Black, isort, pytest config
- `mypy.ini` - Mypy type checking
- `.flake8` - Flake8 linting rules

---

## 4. Integration Tests Setup

### Run Tests

```bash
make test                    # All tests
pytest -m integration        # Integration tests only
pytest -m "not integration"  # Unit tests only
```

### Environment Variables for Integration Tests

Required for Supabase integration tests:

```bash
# .env.local
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

### Test Coverage

```bash
coverage run -m pytest
coverage report
coverage html  # Open htmlcov/index.html
```

---

## 5. Monitoring & Alertmanager Setup

### Quick Start

```bash
# Start monitoring stack
make monitoring-start

# Check health
make monitoring-health

# View logs
make monitoring-logs

# Stop
make monitoring-stop
```

### Components

- **Prometheus**: Metrics collection (port 9090)
- **Grafana**: Visualization (port 3001)
- **Alertmanager**: Alert routing (port 9093)

### Email Notifications Setup

1. **Configure SMTP in `.env.local`**:

   ```bash
   SMTP_HOST=smtp.gmail.com:587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-gmail-app-password  # NOT regular password!
   ALERT_EMAIL_FROM=your-email@gmail.com
   CRITICAL_EMAIL_TO=recipient@gmail.com
   ```

2. **Generate Gmail App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Name it "Alertmanager"
   - Copy 16-character code

3. **Restart stack**:

   ```bash
   make monitoring-stop
   make monitoring-start
   ```

4. **Test email notification**:
   ```bash
   curl -X POST http://localhost:9093/api/v2/alerts \
     -H "Content-Type: application/json" \
     -d '[{
       "labels": {"alertname": "TestAlert", "severity": "critical"},
       "annotations": {"summary": "Test email"},
       "startsAt": "'$(date -u -v+1M +"%Y-%m-%dT%H:%M:%S.000Z")'",
       "endsAt": "'$(date -u -v+10M +"%Y-%m-%dT%H:%M:%S.000Z")'"
     }]'
   ```

**See**: [ALERTMANAGER_NOTIFICATIONS_SETUP.md](ALERTMANAGER_NOTIFICATIONS_SETUP.md) for details

---

## 6. Secrets & Environment Setup

### Local Development

Create `.env.local` (gitignored):

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# SMTP (for alerts)
SMTP_HOST=smtp.gmail.com:587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# OpenAI (for multi-agent)
OPENAI_KEY=your_openai_key_here

# Optional: Other LLM providers
ANTHROPIC_KEY=your_anthropic_key_here
GOOGLE_KEY=your_google_key_here
```

### Production Secrets (GitHub)

Required GitHub Secrets:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `OPENAI_API_KEY`

**Add via**: Repository Settings → Secrets → Actions

**See**: [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md), [PRODUCTION_SECRETS_SETUP.md](PRODUCTION_SECRETS_SETUP.md)

---

## 7. Azure Cloud Setup

### Azure CLI Installation

```bash
# macOS
brew install azure-cli

# Windows
winget install Microsoft.AzureCLI

# Verify
az --version
```

### Login

```bash
az login
az account set --subscription "Your Subscription"
```

### Deploy Resources

```bash
# Deploy infrastructure
az deployment group create \
  --resource-group your-rg \
  --template-file infra/main.bicep

# Deploy function app
func azure functionapp publish your-function-app
```

**See**: [AZURE_SETUP.md](AZURE_SETUP.md) for detailed steps

---

## 8. Supabase Database Setup

### Create Project

1. Go to: https://supabase.com/dashboard
2. Click "New Project"
3. Choose region, set password
4. Copy URL and keys

### Run Migrations

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref your-project-ref

# Run migrations
supabase db push
```

### Load Sample Data

```bash
python scripts/load_sample_kpis_supabase.py
```

**See**: [supabase-setup.md](supabase-setup.md) for detailed steps

---

## 9. Workspace Configuration

### VS Code Extensions (Recommended)

- `ms-python.python` - Python support
- `ms-python.vscode-pylance` - IntelliSense
- `charliermarsh.ruff` - Fast linting
- `ms-azuretools.vscode-docker` - Docker support
- `GitHub.copilot` - AI code assistant

### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black",
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  }
}
```

**See**: [workspace-setup.md](workspace-setup.md) for complete configuration

---

## 📞 Troubleshooting

### Common Issues

**1. Port already in use (Grafana, Prometheus, etc.)**

```bash
# Find process using port
lsof -i :3001  # or :9090, :9093
kill -9 <PID>
```

**2. Docker not running**

```bash
# Start Docker Desktop
open -a Docker  # macOS
# Or start Docker service on Linux/Windows
```

**3. Python module not found**

```bash
# Ensure venv is activated
source .venv/bin/activate
pip install -r requirements.txt
```

**4. Pre-commit hooks failing**

```bash
# Update hooks
pre-commit autoupdate
pre-commit install --force
```

**5. Git conflicts**

```bash
# Run repo cleanup
bash scripts/repo-cleanup.sh
```

---

## 🎯 Next Steps

After setup:

1. **Run the pipeline**: `python scripts/run_data_pipeline.py`
2. **Start monitoring**: `make monitoring-start`
3. **Explore dashboards**: http://localhost:3001 (Grafana)
4. **Run multi-agent**: See `python/multi_agent/README.md`
5. **Read architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📚 Additional Resources

- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
- [COMMAND_REFERENCE.md](COMMAND_REFERENCE.md) - All available commands
- [CODE_QUALITY_GUIDE.md](CODE_QUALITY_GUIDE.md) - Coding standards
- [MONITORING_AUTOMATION_COMPLETE.md](MONITORING_AUTOMATION_COMPLETE.md) - Monitoring details

---

**✅ Setup Complete**: You're ready to develop!
