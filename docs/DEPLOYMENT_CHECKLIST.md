# Production Deployment Checklist

**Last Updated**: 2026-02-06
**Status**: Active
**Working Directory (Mac)**: `cd "/Users/jenineferderas/Documents/Documentos - MacBook Pro (6)/abaco-loans-analytics"`

---

## Key Improvements to the Deployment Checklist Prompt

- **Alignment with Repo Structure**: Updated file paths and names based on actual repository contents (e.g., `repo_maintenance.sh` is under `scripts/maintenance/`, no `start_grafana.sh` found—replaced with equivalent Docker commands; added references to existing tools like Prefect for orchestration and LangChain for agents).
- **Realism for Connections**: Incorporated placeholders for Supabase credentials via environment variables (e.g., `$SUPABASE_URL`, `$SUPABASE_SERVICE_ROLE_KEY`) to avoid hardcoding; added verification for actual integrations like n8n workflows and Azure traces, as these are present in the repo. Removed assumptions about non-existent files like `CLEANUP_SCRIPTS_AUDIT.md` and adjusted workflow names to match GitHub Actions (e.g., "Security Scan" instead of "Python QA").
- **Enhanced Thoroughness and Safety**: Added checks for additional repo elements (e.g., n8n configs, Prefect flows); emphasized dry-run modes for scripts; included modern best practices like dependency vulnerability scans with `pip-audit`; made RLS tests more robust with actual queries; ensured no real data in `data/` by specifying exclusion of PII-sensitive files.
- **Conciseness and Clarity**: Streamlined redundant sections, used consistent formatting, and added optional flags for tools to handle errors gracefully. Ensured the prompt accounts for the repo's 2026-dated elements as forward-looking but treats them as current for deployment.

---

## Checklist

Before approving deployment to production, run and confirm ALL of the following checks from the repository root. Do not deploy unless every item passes with no unexpected differences, no sample/demo data, and no leftover "pruebas" or dev artifacts.

### 1. Git & Branch Hygiene

```bash
git checkout main
git fetch origin
git pull origin main
git status
```

**Expected**: On branch main. Your branch is up to date with 'origin/main'. Nothing to commit, working tree clean.

Also confirm:

```bash
git branch -vv
```

Only main and any actively used feature branches. No stale local branches; delete merged ones:

```bash
git branch --merged main | grep -v "main" | xargs -I {} git branch -d "{}" 2>/dev/null || true
```

### 2. No Sample / Demo Data in Production Paths

Check for any remaining sample/demo/test data in active paths:

```bash
rg "sample_" data/ scripts/ src/ docs/ || echo "No 'sample_' references found"
rg "demo" data/ scripts/ src/ docs/ || echo "No 'demo' references found"
rg "prueba" data/ scripts/ src/ docs/ || echo "No 'prueba' references found"
rg "test_data" data/ scripts/ src/ docs/ || echo "No 'test_data' references found"
```

**Actions**: Any hits in production paths (src/, scripts/, data/, streamlit_app/, infra/) must be removed or moved to archives/ or tests/. Re-run the rg commands until no unintended references remain. Also ensure there are no real data files under data/ that should not be deployed (e.g., exclude PII-sensitive CSVs):

```bash
find data -type f
```

Only expected production data locations for runtime (or empty); no ad-hoc CSVs from experiments.

### 3. Run Cleanup & Maintenance Scripts

Execute the project's cleanup and maintenance tooling to remove orphaned files, caches, and dev artifacts.

```bash
bash clean.sh --dry-run  # review first, then run without --dry-run if safe
bash scripts/maintenance/repo_maintenance.sh --mode=standard --dry-run  # review, then run
git status
```

**Expected**: No orphaned files, no temporary artifacts, no stray logs or local config. git status should be clean or only show intentional, reviewable changes (which must then be committed or reverted).

If there are additional maintenance scripts documented in docs/MAINTENANCE_SCRIPTS_AUDIT.md, run them as instructed there and confirm they complete without errors.

> **Note**: No `CLEANUP_SCRIPTS_AUDIT.md` exists; rely on `MAINTENANCE_SCRIPTS_AUDIT.md`.

### 4. Full Test Suite – Unit + Integration + Multi-Agent

Activate the virtual environment if not already:

```bash
source .venv/bin/activate
```

Run the full Python test suite:

```bash
pytest tests/ -v
```

**Expected**: All unit tests and non-credentialled integration tests must pass. Any remaining failures must be explicitly documented as: requiring external credentials (e.g., Supabase, external APIs), or out of scope for this deployment. No new failures relative to the baseline (docs/SPRINT_STATUS_2026_02_04.md).

For multi-agent / pipeline integration tests (under tests/agents/ and tests/integration/):

```bash
pytest tests/agents/ -v
pytest tests/integration/ -v
```

**Confirm**: Agent orchestration (using LangChain), scenarios, and Supabase integration tests behave as expected. Any skipped tests are documented and intentional.

For data integrity checks:

```bash
pytest tests/test_data_integrity.py -v
```

### 5. Supabase & RLS / Monitoring Schema Verification

Ensure database schema and RLS are aligned with migrations. (Use env vars: export `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` from .env)

List migrations:

```bash
supabase migration list --db-url $SUPABASE_URL
```

**Expected**: Local and remote migration IDs match (no pending migrations).

Optionally, verify monitoring schema and KPI policies:

```bash
supabase db dump --linked | rg -i "monitoring.kpi_values|ENABLE ROW LEVEL SECURITY|CREATE POLICY" | head -40
```

**Confirm**: monitoring.kpi_values exists with RLS enabled. Policies for authenticated and service_role access are present and restrictive (no "allow all" inserts).

If you added an RLS smoke test runner (e.g., scripts/test-rls.js):

```bash
node scripts/test-rls.js
```

**Expected**: Anonymous key: cannot read/write sensitive tables. Authenticated users: can access only their own rows per policy. Service role: has expected, controlled access. Refer to docs/RLS_VERIFICATION_TESTS.md for additional queries.

### 6. Observability & Grafana/Monitoring Integration

Validate that the observability stack (Prometheus + Grafana + Alerting) is wired correctly to this version.

#### 6.1 Local/Dev Monitoring Stack

If you have a local monitoring stack:

```bash
docker-compose -f docker-compose.monitoring.yml up -d
```

> No `start_grafana.sh` found; use Docker directly.

Then: Access Grafana at http://localhost:3000 (default port). Confirm dashboards are loading and data sources connected: Pipeline run dashboard, Data quality / KPI panels, Supabase metrics if applicable.

#### 6.2 Metrics from Current Build

Run a pipeline execution to generate metrics/traces:

```bash
python scripts/run_data_pipeline.py --mode validate --verbose --input data/sample_loans.csv
```

**Confirm**: Metrics and logs appear in Grafana/Prometheus (or your chosen backend). No hard-coded sample metrics or fake series are left in production dashboards.

If you have OpenTelemetry/Azure monitor integration: Verify traces for pipeline phases (using Prefect) and multi-agent flows are visible in your tracing backend (Application Insights / Azure Monitor). Check n8n/ for workflow integrations.

### 7. CI / Workflow Health Check (GitHub Actions)

Validate that all workflows relevant for production are green:

In GitHub → Actions, confirm latest runs on main: Security Scan (CodeQL + Bandit/Snyk), Model Evaluation Pipeline, Tests, Deployment.

Optionally, trigger a manual run of the core workflows on main: security-scan.yml, model-evaluation.yml.

**Confirm**: All jobs complete successfully. No failing or flaky steps. actions/upload-artifact is pinned to the expected SHA (v4.4.3 in your repo).

### 8. Static Analysis, Lint, and Security Tools

Run core static analysis locally:

#### 8.1 Python compile + lint

```bash
python -m compileall -q src python
pylint src python || true
```

Fix any errors; warnings are acceptable only if understood and documented.

#### 8.2 Markdown & YAML

```bash
markdownlint-cli2 "**/*.md" --ignore node_modules --ignore .venv || true
yamllint . || true
```

No new MD0xx violations (headings, lists, tables, fences). No YAML syntax errors or critical style issues in .github/workflows, config/, infra/, openapi.yaml, etc.

#### 8.3 Secret scanning

```bash
gitleaks detect --no-banner --redact || true
```

**Confirm**: No API keys, secrets, passwords, or key-like patterns in committed files. .env.example and other templates use placeholders only.

#### 8.4 Security & dependency scans (CI)

Confirm in GitHub Actions: CodeQL Analysis: passing; Snyk dependency scan: clean or risk accepted and documented; Python Security Audit: safety/bandit have no untriaged critical findings.

```bash
pip-audit
```

### 9. Baseline Comparison – No Hidden Regressions

Compare current main against the baseline Tag v1.0.0-baseline:

```bash
git diff v1.0.0-baseline..main --stat
```

**Confirm**: Every difference is understood and intentional. No reintroduction of: sample/demo/test-only artifacts, weakened RLS or security policies, removed logging/observability hooks.

Optionally, compare test counts to baseline (documented in docs/SPRINT_STATUS_2026_02_04.md):

```bash
pytest tests/ -q > /tmp/tests_current.txt 2>&1
grep -E "tests collected|passed|failed|skipped" docs/SPRINT_STATUS_2026_02_04.md
grep -E "tests collected|passed|failed|skipped" /tmp/tests_current.txt
```

Any deltas must be explained (new tests added, expected skips, etc.).

---

## Final Go / No-Go Confirmation (Team Reply)

In the deployment channel, each responsible owner replies with:

- **Git/Branch**: CLEAN (main = origin/main, no uncommitted changes)
- **Tests**: PASS (details: X passed, Y skipped, Z known/accepted)
- **Multi-agent & Pipeline**: PASS (or documented limitations)
- **Supabase & RLS**: PASS (migrations applied, RLS verified, no open security alerts)
- **Grafana/Monitoring**: PASS (dashboards & metrics confirmed for this build)
- **CI/Workflows**: PASS (all relevant GitHub Actions jobs green)
- **Security & Secrets**: PASS (CodeQL, Snyk, gitleaks; no hardcoded secrets)
- **Docs & Governance**: PASS (status docs updated, no sample/demo data, planning aligned)

If any item is not PASS: Deployment is blocked. Open a short incident note with: Problem, Risk, Fix plan and owner. Only after the fix is implemented and re-validated may deployment proceed.

---

## Repository Context

The Abaco Loans Analytics repository represents a comprehensive fintech platform focused on loan portfolio management, featuring:

- A unified 4-phase data pipeline (Ingestion, Transformation, Calculation, Output)
- AI multi-agent systems with 9 specialized agents (e.g., Risk Assessment, Fraud Detection)
- Real-time visualizations via Streamlit and Grafana
- Secure data handling through Supabase with Row Level Security (RLS)

Integrations: Prometheus (metrics), OpenTelemetry (tracing), Prefect (orchestration), LangChain (AI agents), n8n (workflows), Azure (cloud deployment).

---

## Alignment Analysis

| Category        | Original Prompt Issues                                                              | Improvements Made                                                                            | Repo Alignment                                      |
| --------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Script Paths    | Assumes root-level `repo_maintenance.sh`; mentions non-existent `start_grafana.sh`. | Updated to `scripts/maintenance/repo_maintenance.sh`; replaced with `docker-compose`.        | Matches scripts/ structure; grafana/ uses Docker.   |
| Docs References | References non-existent `CLEANUP_SCRIPTS_AUDIT.md`.                                 | Removed; focused on existing `MAINTENANCE_SCRIPTS_AUDIT.md` and `RLS_VERIFICATION_TESTS.md`. | docs/ has 90+ files, including sprint and RLS docs. |
| Test Suite      | Assumes specific subdirs; no mention of LangChain.                                  | Added LangChain agent confirmation; verbose flags.                                           | tests/ has agents/, integration/; ~232 tests total. |
| Supabase        | No env vars; assumes project ID.                                                    | Added env exports; noted fictional ID.                                                       | supabase/ configs use placeholders; RLS in docs/.   |
| CI Workflows    | Mismatched names (e.g., "Python QA").                                               | Updated to actual: Security Scan, Model Evaluation.                                          | Actions page shows green runs for key workflows.    |
| Security Tools  | Basic scans only.                                                                   | Added `pip-audit` for deps.                                                                  | .github/ has CodeQL, Snyk integrated.               |
