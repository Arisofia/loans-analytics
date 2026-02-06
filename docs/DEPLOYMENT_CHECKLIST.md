# Production Deployment Checklist

**Last Updated**: 2026-02-06
**Status**: Active
**Verified Against**: Actual repository contents on `main` branch

All paths, scripts, workflow names, and configurations below have been verified to exist in the repository. Run all commands from the repository root.

---

## 1. Git & Branch Hygiene

```bash
git checkout main
git fetch origin
git pull origin main
git status
```

**Expected**: On branch `main`, up to date with `origin/main`, working tree clean.

Delete merged local branches:

```bash
git branch --merged main | grep -v "main" | xargs -I {} git branch -d "{}" 2>/dev/null || true
```

---

## 2. No Sample / Demo / Dev Artifacts in Production Paths

Scan for leftover test/demo data in production-facing directories:

```bash
rg "sample_" data/ scripts/ src/ python/ streamlit_app/ || echo "No 'sample_' references found"
rg "prueba" data/ scripts/ src/ python/ streamlit_app/ || echo "No 'prueba' references found"
rg "test_data" data/ scripts/ src/ python/ streamlit_app/ || echo "No 'test_data' references found"
```

Review what's in `data/` for any PII-sensitive or ad-hoc experiment files:

```bash
find data -type f | head -50
```

**Actions**: Hits in `src/`, `python/`, `streamlit_app/`, or `scripts/` (outside `tests/`) must be removed or moved to `archives/` or `tests/`. The `data/` directory should only contain expected runtime data, ML models (`data/models/`), and usage metrics.

---

## 3. Run Cleanup & Maintenance Scripts

Both scripts exist at the paths below:

```bash
bash clean.sh --dry-run
# Review output, then run without --dry-run if safe:
bash clean.sh
```

```bash
bash scripts/maintenance/repo_maintenance.sh --mode=standard --dry-run
# Review output, then run without --dry-run if safe:
bash scripts/maintenance/repo_maintenance.sh --mode=standard
```

Alternatively, use the Makefile targets:

```bash
make maintenance-dry-run   # Preview cleanup
make maintenance           # Execute cleanup (runs clean.sh)
```

```bash
git status
```

**Expected**: No orphaned files, no temporary artifacts. Working tree should be clean or only show intentional changes (commit or revert them).

---

## 4. Full Test Suite

Activate the virtual environment:

```bash
source .venv/bin/activate
```

The `pytest.ini` defines testpaths as `python/multi_agent`, `python/tests`, and `tests`. Run the full suite:

```bash
pytest -v
```

Or use the Makefile:

```bash
make test
```

**Expected**: All unit tests pass. The suite has ~145+ test functions across 27 files. Any failures must be documented as requiring external credentials or being out of scope.

### 4.1 Agent Tests

Agent tests cover base agents, orchestrator, protocol, scenarios (happy path, error, concurrency, timeout), integration (chaining, communication, webhooks, Supabase), and concrete agents (risk, analytics, validation, custom):

```bash
pytest tests/agents/ -v
```

### 4.2 Integration Tests

Integration tests include real Supabase tests (opt-in) and financial analytics:

```bash
pytest tests/integration/ -v
```

**Note**: Real Supabase integration tests require `RUN_REAL_SUPABASE_TESTS=1` and valid credentials. It is acceptable to skip these if credentials are not available locally; CI handles them.

### 4.3 Security Tests

```bash
pytest tests/security/ -v
```

### 4.4 Data Integrity

```bash
pytest tests/test_data_integrity.py -v
```

---

## 5. Supabase & RLS Verification

Export credentials from `.env` (see `.env.example` for the full variable list):

```bash
export SUPABASE_URL="$NEXT_PUBLIC_SUPABASE_URL"
export SUPABASE_SERVICE_ROLE_KEY="<from .env>"
```

### 5.1 Migration Status

The repo has migrations in two locations:

- `supabase/migrations/` (15 migration files, including RLS, security hardening, monitoring schemas)
- `db/migrations/` (7 migration files for KPI tables, RLS policies)

```bash
supabase migration list --db-url "$SUPABASE_DATABASE_URL"
```

**Expected**: Local and remote migration IDs match. No pending migrations.

### 5.2 RLS Smoke Test

The RLS test script exists at `scripts/test-rls.js`:

```bash
node scripts/test-rls.js
```

Additional RLS diagnostics:

```bash
bash scripts/diagnose-rls.sh
```

**Expected**: Anonymous key cannot read/write sensitive tables. Service role has controlled access. RLS is enabled on `financial_statements`, `payment_schedule`, and `monitoring.kpi_values`.

### 5.3 Schema Verification (Optional)

```bash
supabase db dump --linked | rg -i "ENABLE ROW LEVEL SECURITY|CREATE POLICY" | head -40
```

---

## 6. Observability & Monitoring Stack

### 6.1 Start the Monitoring Stack

Use the Makefile or scripts:

```bash
make monitoring-start
# Or directly:
bash scripts/monitoring/start_monitoring.sh
```

This brings up Prometheus, Grafana, and Alertmanager via `docker-compose.monitoring.yml`:

- **Prometheus**: http://localhost:9090 (60s scrape interval, 30-day retention)
- **Grafana**: http://localhost:3001 (note: port 3001, not 3000)
- **Alertmanager**: http://localhost:9093

### 6.2 Verify Grafana Dashboards

Access Grafana at http://localhost:3001. Confirm these dashboards load with live data:

- `kpi-overview.json` - KPI tracking
- `supabase-postgresql.json` - Database metrics

Dashboard files are in `grafana/dashboards/`, provisioned via `grafana/provisioning/dashboards/default.yml`.

Datasources configured in `grafana/provisioning/datasources/supabase.yml`:

1. Supabase PostgreSQL (default)
2. Supabase REST API
3. Azure Monitor
4. Prometheus Local

### 6.3 Verify Alert Rules

Alert rules are in `config/rules/`:

- `config/rules/pipeline_alerts.yml`
- `config/rules/supabase_alerts.yml`

Alertmanager config: `config/alertmanager.yml` (template at `config/alertmanager.yml.template`).

### 6.4 Health Check

```bash
make monitoring-health
# Or directly:
bash scripts/monitoring/health_check_monitoring.sh
```

### 6.5 Backup Dashboards (Before Deploy)

```bash
make dashboard-backup
# Or: bash scripts/monitoring/backup_dashboards.sh
```

---

## 7. Docker Builds

The repo has three Dockerfiles:

| Dockerfile             | Purpose               | Port | Healthcheck                                 |
| ---------------------- | --------------------- | ---- | ------------------------------------------- |
| `Dockerfile`           | FastAPI Analytics API | 8000 | `curl http://localhost:8000/health`         |
| `Dockerfile.pipeline`  | Data Pipeline         | -    | -                                           |
| `Dockerfile.dashboard` | Streamlit Dashboard   | 8501 | `curl http://localhost:8501/_stcore/health` |

Build and verify each:

```bash
docker build -t abaco-api -f Dockerfile .
docker build -t abaco-pipeline -f Dockerfile.pipeline .
docker build -t abaco-dashboard -f Dockerfile.dashboard .
```

Test the dashboard stack locally:

```bash
docker-compose -f docker-compose.dashboard.yml up -d
# Verify at http://localhost:8501
docker-compose -f docker-compose.dashboard.yml down
```

---

## 8. CI / GitHub Actions Workflow Health

### 8.1 Active Workflows (13)

Verify these are green on `main` in GitHub Actions:

| Workflow File                   | Purpose                                        | Trigger                                               |
| ------------------------------- | ---------------------------------------------- | ----------------------------------------------------- |
| `pr-checks.yml`                 | Python QA (ruff, black, pytest)                | PR events                                             |
| `unified-tests.yml`             | Unit + integration + multi-agent + smoke tests | Push to main/develop, PRs                             |
| `deployment.yml`                | Deploy to production                           | Push to main, manual                                  |
| `docker.yml`                    | Build/push Docker images to ghcr.io            | Dockerfile changes, manual                            |
| `daily-ingest.yml`              | Daily data ingestion pipeline                  | Cron 2 AM UTC, manual                                 |
| `security-scan.yml`             | CodeQL + Snyk + Bandit + Safety                | Push to main, PRs, Monday schedule                    |
| `model_evaluation.yml`          | Model evaluation + threshold checks            | PRs, nightly 2 AM UTC                                 |
| `agents_unified_pipeline.yml`   | Agent pipeline orchestration + validation      | Cron 5:15 AM UTC, manual                              |
| `cost-regression-detection.yml` | Cost benchmark on agent changes                | PRs touching src/agents/ or config/cost_baselines.yml |
| `dependencies.yml`              | Auto-update dependencies                       | Monday 8 AM UTC, manual                               |
| `cleanup-old-runs.yml`          | Delete old workflow runs (>15 days)            | Sunday 2 AM UTC, manual                               |
| `ci-web.yml`                    | Web frontend CI (placeholder)                  | Push/PR                                               |
| `azure-static-web-apps-*.yml`   | Azure Static Web Apps                          | Auto-generated                                        |

### 8.2 Disabled Workflows (9)

Located in `.github/workflows/.disabled/`. These were disabled due to failures or being unused. Verify none have been accidentally re-enabled:

```bash
ls .github/workflows/.disabled/
```

**Expected**: 9 `.yml.disabled` files (agent-checklist-validation, azure_diagnostics, batch_export_scheduled, code-maintenance, customer_segmentation, financial_forecast, historical_supabase_integration, investor_reporting, security-scan).

---

## 9. Static Analysis & Security

### 9.1 Python Compile + Lint

```bash
python -m compileall -q src python
make lint
# Or manually:
# ruff check src python
# black --check src python
# pylint src python || true
```

### 9.2 Trunk Check (Full Linter Suite)

Trunk orchestrates 20+ linters (bandit, black, flake8, gitleaks, hadolint, isort, markdownlint, mypy, pylint, ruff, shellcheck, yamllint, etc.). Run the full check:

```bash
trunk check --all
```

### 9.3 Secret Scanning

```bash
gitleaks detect --no-banner --redact || true
```

**Confirm**: No API keys, secrets, or key-like patterns in committed files. `.env.example` and `n8n/.env.example` use placeholders only.

### 9.4 Dependency Vulnerability Scan

```bash
pip-audit
```

Also confirm in GitHub Actions that the `security-scan.yml` workflow (CodeQL + Snyk + Bandit + Safety) is passing.

---

## 10. Infrastructure Configuration

### 10.1 Azure Bicep (infra/)

The `infra/` directory contains Azure Bicep templates:

- `main.bicep` - Main infrastructure
- `appinsights.bicep` - Application Insights
- `loganalytics-workspace.bicep` - Log Analytics
- `main.parameters.json` - Parameters

Verify parameters are correct for production:

```bash
cat infra/main.parameters.json
```

### 10.2 Environment Variables

Cross-check `.env.example` against the actual `.env` to ensure all required variables are set:

```bash
diff <(grep -oP '^[A-Z_]+' .env.example | sort) <(grep -oP '^[A-Z_]+' .env | sort)
```

Key variable groups (from `.env.example`):

- **Supabase**: `NEXT_PUBLIC_SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_DATABASE_URL`, `SUPABASE_JWT_SECRET`
- **LLM/Agents**: `AGENT_PROVIDER`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
- **Observability**: `ENABLE_OTEL`, `OTEL_ENDPOINT`, `APPLICATIONINSIGHTS_CONNECTION_STRING`
- **Application**: `NODE_ENV`, `LOG_LEVEL`, `PIPELINE_RUN_SCHEDULE`

### 10.3 N8N Automation

Verify n8n configuration if using webhook-based flows:

```bash
cat n8n/.env.example
ls n8n/workflows/
```

---

## 11. Deployment Execution

### Option A: Azure App Service (Primary)

Use the deployment script:

```bash
bash scripts/deployment/deploy_to_azure.sh
```

This script:

1. Validates git state (clean, on main, synced)
2. Runs local tests
3. Triggers `deployment.yml` via GitHub CLI
4. Polls workflow status (10-minute timeout)
5. Runs health checks against https://abaco-analytics-dashboard.azurewebsites.net

### Option B: Docker Stack (Self-Hosted)

```bash
bash scripts/deployment/deploy_stack.sh
```

This builds and brings up `docker-compose.dashboard.yml`.

### Post-Deploy Health Check

```bash
bash scripts/deployment/production_health_check.sh
```

Checks: application health, response time, git status, code quality, environment, and test suite.

---

## 12. Rollback Plan

If deployment fails, rollback is available:

```bash
bash scripts/deployment/rollback_deployment.sh [commits_back]
# Default: 1 commit back
```

This script:

1. Validates branch state
2. Shows target commit details
3. Requires explicit confirmation
4. Resets and force-pushes
5. Triggers redeployment
6. Runs health checks

---

## Final Go / No-Go Confirmation

Each responsible owner replies with:

- **Git/Branch**: CLEAN (main = origin/main, no uncommitted changes)
- **Tests**: PASS (X passed, Y skipped, Z known/accepted)
- **Agent Tests**: PASS (or documented limitations for credential-dependent tests)
- **Supabase & RLS**: PASS (migrations applied, RLS verified via test-rls.js)
- **Monitoring**: PASS (Grafana dashboards load, Prometheus scraping, alerts configured)
- **Docker Builds**: PASS (all 3 Dockerfiles build successfully)
- **CI/Workflows**: PASS (all 13 active GitHub Actions workflows green)
- **Security**: PASS (gitleaks clean, pip-audit clean, Trunk check passing)
- **Infrastructure**: PASS (Bicep parameters correct, env vars complete)

If any item is not PASS: Deployment is blocked. Document the problem, risk, and fix plan. Only proceed after the fix is implemented and re-validated.
