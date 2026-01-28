# Repository Cleanup Plan - Abaco Loans Analytics

**Date**: 2026-01-28  
**Target**: 85%+ size reduction, production-ready repository  
**Current State**: 440 files, 4.8MB, 44 workflows  
**Target State**: ~100 files, <1MB, 7 workflows  

---

## Executive Summary

This document outlines a comprehensive two-phase cleanup operation:
1. **Test & optimize workflow fixes** - Validate critical workflows with actual CI runs
2. **Production cleanup** - Remove 300+ legacy files, consolidate documentation, achieve production-focused architecture

---

## Phase 1: Workflow Testing & Optimization

### Workflows to Test (6 core + 1 optional)
1. ✅ `ci.yml` - Code quality & tests
2. ✅ `deploy.yml` - Production deployment
3. ✅ `codeql.yml` - Security scanning
4. ✅ `docker-ci.yml` - Docker image build
5. ✅ `lint_and_policy.yml` - Code style enforcement
6. ✅ `pr-review.yml` - AI-powered PR review
7. ⚠️  `agent_orchestrator.yml` - Core agent execution (if exists)

### Workflows to Delete (37 files)
- `analytics.yml`
- `auto_close_stale_prs.yml`
- `azure_diagnostics.yml`
- `azure_static_web_apps_yellow_cliff_03015b20f.yml`
- `batch_export_scheduled.yml`
- `customer_segmentation.yml`
- `dependency_submission.yml`
- `dependency_validate.yml`
- `deploy_dashboard.yml`
- `deploy_verify.yml`
- `docker_images.yml`
- `financial_forecast.yml`
- `investor_reporting.yml`
- `kpi_daily.yml`
- `kpi_parity.yml`
- `main_abaco_analytics_dashboard.yml`
- `model_evaluation.yml`
- `nightly_dispatch.yml`
- `operations_dashboard.yml`
- `opik_observability.yml`
- `orchestrate_deploy_verify.yml`
- `playwright.yml`
- `post_rollout_validation.yml`
- `pr_assignee_check.yml`
- `pr_auto_assign.yml`
- `pr_monitor.yml`
- `product_analytics.yml`
- `reusable_secret_check.yml`
- `risk_monitoring.yml`
- `secret_check.yml`
- `security-audit.yml`
- `snyk.yml`
- `sonarcloud.yml`
- `sonarqube.yml`
- `unified_data_pipeline.yml`
- `validate_deployment.yml`
- `validate_workflows.yml`
- `web_middleware_smoke.yml`

---

## Phase 2: Repository Cleanup

### Section 1: Legacy Directories to Remove

#### Remove Completely
- ✅ `streamlit_app/` - Streamlit UI (not in new flow)
- ✅ `node/` - Node.js artifacts
- ⚠️  `.gradle/` - Gradle build cache (if exists)
- ✅ `models/` - Old ML models directory
- ⚠️  `experiments/` - Experimental code (if exists)
- ⚠️  `demos/` - Demo applications (if exists)
- ⚠️  `mocks/` - Mock data/services (if exists)
- ⚠️  `data_samples/` - Sample data (if exists)
- ✅ `projects/` - Orphaned projects
- ✅ `packages/` - Old npm packages
- ✅ `patches/` - Old npm patches
- ✅ `.vercel/` - Vercel deployment config
- ✅ `services/` - Old microservices
- ✅ `runbooks/` - Legacy operational runbooks
- ⚠️  `infra/` - Old infrastructure code (check if Terraform needed)
- ✅ `nginx-conf/` - Legacy NGINX config
- ✅ `fi-analytics/` - Old financial analytics
- ✅ `data-processor/` - Old data processor
- ✅ `templates/` - Legacy templates (if unused)
- ✅ `tools/` - Old tools

#### Consolidate (Move to src/)
- ✅ `python/` - Old python directory → integrate into `src/` structure

#### Keep (Required for new architecture)
- ✅ `apps/web` - Next.js dashboard (actively used)
- ✅ `src/` - Core source code
- ✅ `supabase/` - Database configuration
- ✅ `sql/` - Analytics queries
- ✅ `tests/` - Test suite
- ✅ `scripts/` - Build/deployment scripts
- ✅ `.github/` - GitHub configuration (workflows, actions)
- ⚠️  `db/` - Database migrations (keep if used)
- ⚠️  `docs/` - Documentation (consolidate)

---

### Section 2: Legacy Documentation Files to Remove

**Keep Only (3 files):**
- `README.md` - Project overview (UPDATE)
- `DEPLOYMENT.md` - Production deployment guide
- `SECURITY.md` - Security policies

**Delete (11 files):**
- ✅ `AGENTS.md`
- ✅ `AUDIT_REPORT.md`
- ✅ `CHANGELOG.md`
- ✅ `CLAUDE.md`
- ✅ `CONTEXT.md`
- ✅ `COMPLETE-PR-SETUP.sh`
- ✅ `next-steps.md`
- ✅ `MULTI_AGENT_STATUS.md`
- ✅ `ENGINEERING_STANDARDS.md`
- ✅ `SECURITY_HARDENING_PR16.md`
- ✅ `SUPABASE_EDGE_FUNCTIONS_DEPLOYMENT.md`

---

### Section 3: Legacy Root-Level Files to Remove

**Scripts & Utilities:**
- ✅ `dashboard_utils.py`
- ✅ `data_normalization.py`
- ✅ `kpi_catalog_processor.py`
- ✅ `run_complete_analytics.py`
- ✅ `theme.py`
- ✅ `sitecustomize.py`
- ✅ `tracing_setup.py`
- ✅ `main.ts`
- ✅ `gemini_cli.py`

**Legacy Configs:**
- ✅ `local.settings.json`
- ✅ `host.json`
- ✅ `build.gradle`
- ✅ `openapi.yaml`
- ✅ `docker-compose.dev.yml`
- ✅ `docker-compose.override.yml`
- ✅ `Dockerfile.pipeline`
- ✅ `vercel.json`
- ✅ `profile.ps1`
- ✅ `git` (file if exists)
- ✅ `azure.yaml`
- ✅ `audit-npm.json`
- ✅ `package-lock.json` (use pnpm)
- ✅ `.vercelignore`

**Keep (Required configs):**
- ✅ `docker-compose.yml` (UPDATE)
- ✅ `Dockerfile`
- ✅ `pyproject.toml`
- ✅ `requirements.txt`
- ✅ `requirements-dev.txt`
- ✅ `.gitignore` (UPDATE)
- ✅ `Makefile` (UPDATE)
- ✅ `package.json` (for apps/web)
- ✅ `pnpm-lock.yaml`
- ✅ `pnpm-workspace.yaml`

---

### Section 4: Update Critical Files

#### 4.1 Update .gitignore
Add production-focused patterns:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.mypy_cache/
.dmypy.json
dmypy.json
*.pyi

# Virtual environments
venv/
.venv
env/
.env
.env.local
.env.*.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
*.sublime-workspace
.project
.pydevproject

# Node (for apps/web)
node_modules/
npm-debug.log
yarn-error.log

# Logs
logs/
*.log
*.log.*

# Docker
docker-compose.override.yml

# Database
*.db
*.sqlite
*.sqlite3

# Build artifacts
build/
dist/
*.egg-info/

# Temp files
.tmp/
tmp/
temp/

# OS
.DS_Store
Thumbs.db

# Secrets (CRITICAL)
.env
.env.local
.env.*.local
secrets.json
**/credentials.json
**/config/secrets.yml

# Legacy/deprecated
experiments/
demos/
mocks/
data_samples/
__legacy__/
```

#### 4.2 Update README.md
- Add architecture flow diagram
- Document new stack (n8n → Supabase → Python Multi-Agent)
- Update quick start instructions
- Reference consolidated docs

#### 4.3 Update Makefile
- Production-focused targets
- Test, lint, format commands
- Docker compose shortcuts
- Deploy command

#### 4.4 Update docker-compose.yml
- n8n webhook orchestration
- PostgreSQL for n8n
- Python multi-agent orchestrator
- Remove old services (frontend/backend if not needed)

#### 4.5 Create docs/UNIFIED.md
- Consolidate all documentation
- System overview
- Architecture flow
- Deployment guide
- Monitoring & observability

---

### Section 5: Validation Criteria

**File Count:**
- ✅ Total files: 440 → ~100 (77% reduction)
- ✅ Workflows: 44 → 7 (84% reduction)

**Critical Files Exist:**
- ✅ `src/agents/` (or `python/multi_agent/`)
- ✅ `supabase/`
- ✅ `sql/`
- ✅ `docker-compose.yml`
- ✅ `README.md`
- ✅ `DEPLOYMENT.md`
- ✅ `SECURITY.md`

**CI Checks:**
- ✅ All critical workflows pass or gracefully degrade
- ✅ No hard failures on optional steps
- ✅ Security scans pass (CodeQL, etc.)

---

## Rollback Plan

All deletions can be recovered from git history:
```bash
# Restore specific file
git checkout <commit-before-cleanup> -- path/to/file

# Restore entire directory
git checkout <commit-before-cleanup> -- path/to/directory/

# Create rollback branch
git checkout -b rollback/<cleanup-branch>
git revert <cleanup-commit-hash>
```

**Git Reference**: All deleted files remain in git history indefinitely.

---

## Expected Outcome

✅ Repository size: 440 → ~100 files (77% reduction)  
✅ Repository size: 4.8MB → <1MB (80% reduction)  
✅ Workflows: 44 → 7 (84% reduction)  
✅ All CI checks passing  
✅ Production-ready architecture  
✅ Zero legacy cruft or orphaned files  
✅ Ready for immediate production deployment  

---

## Notes

- Python multi-agent code currently in `python/multi_agent/` - may consolidate to `src/agents/` later
- `apps/web` is actively used by deploy.yml and azure workflows - MUST KEEP
- Check `infra/` before deletion - may contain active Terraform/IaC
- Some directories (demos, experiments, mocks, data_samples) don't exist - skip deletion
- Preserve all git history - nothing is permanently lost
