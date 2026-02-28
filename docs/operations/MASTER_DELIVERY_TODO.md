# Master Delivery TODO (No-Pause Flow)

Single execution checklist to complete end-to-end delivery without stopping every few changes.

## Rules (always-on)

- [x] Work only on canonical paths from `docs/operations/SCRIPT_CANONICAL_MAP.md`
- [x] Keep one active command/doc per task (remove duplicates and stale references)
- [x] Use real input data only for pipeline validations
- [x] No dummy/sample fallback in production code paths
- [x] Keep `main` as source of truth and sync frequently

## Phase 0 - Baseline Snapshot

- [x] `git status --short`
- [x] `git rev-parse --short HEAD`
- [x] `python scripts/maintenance/validate_structure.py`
- [x] Confirm working dataset exists: `data/raw/abaco_real_data_20260202.csv`

Exit criteria:
- [x] Repository structure validation = 100%
- [x] Baseline state documented in delivery notes

## Phase 1 - Repo Hygiene (Single Flow)

- [x] Remove duplicate files (e.g., names ending in ` 2`, duplicate docs, duplicate scripts)
- [x] Remove orphan references to deleted/legacy routes
- [x] Remove stale CI/workflow refs and obsolete process references
- [x] Ensure only one canonical entrypoint per operation

Validation:
- [x] `rg -n --hidden --glob '!node_modules/**' --glob '!.git/**' \"( 2\\.| copy|duplicate|deprecated path)\"`
- [x] `python scripts/maintenance/validate_structure.py`

## Phase 2 - Dependency and Security Hardening

- [x] Run dependency audit:
- [x] `npm audit --omit=dev`
- [x] `pip install -r requirements.txt` (CI-equivalent venv)
- [x] Run security scans:
- [x] `safety check --continue-on-error --save-json /tmp/safety-results.json`
- [x] `bandit -r python src scripts -f json -o /tmp/bandit-report.json`
- [x] Resolve High/Critical dependency findings
- [x] Ensure Snyk gate is strict when scan executes (workflow must fail on High/Critical)

Validation:
- [x] No blocking High/Critical vulns in dependency scan
- [x] Security workflow remains green after remediation

Current notes:
- Remediated `protobuf` vulnerability path by migrating from the legacy Gemini SDK to `google-genai` and upgrading runtime stack to:
  `protobuf==6.33.5`, `grpcio==1.78.0`, `grpcio-status==1.78.0`.
- `safety` now reports `0` vulnerabilities in local CI-equivalent `.venv`.
- `bandit` continues to report only `LOW` severity findings (`80`), with `0` medium/high.
- Verified strict Snyk gate in `.github/workflows/security-scan.yml`:
  `--severity-threshold=high --fail-on=all` (scan is conditional on `SNYK_TOKEN` presence).

## Phase 3 - Real Data Pipeline Validation (All Modes)

- [x] Dry-run ingestion:
- [x] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode dry-run`
- [x] Validate mode:
- [x] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode validate`
- [x] Full mode:
- [x] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode full`
- [x] Confirm artifacts exist under `logs/runs/<run_id>/`

Calculation integrity:
- [x] Independently recompute critical KPIs from `clean_data.parquet`
- [x] Compare against `kpis_output.json` and confirm exact/expected tolerance

## Phase 4 - Test and Quality Gate

- [x] `ruff check .`
- [x] `black --check .`
- [x] `pytest tests/ -v --tb=short -m \"not integration\"`
- [x] `pytest python/multi_agent/ -v -k \"test_\" --tb=short`
- [x] If secrets present: `pytest tests/ -v -m \"integration\" --tb=short`
  Skipped locally (not applicable): `SUPABASE_URL` and `SUPABASE_ANON_KEY` are not set.

Exit criteria:
- [x] All required checks pass
- [x] No new failing tests

## Phase 5 - CI/Actions Verification

- [x] Push branch/`main`
- [x] Verify latest runs for commit SHA:
- [x] `Tests` workflow = success
- [x] `Security Scan` workflow = success
- [x] Inspect job-level details (unit/integration/multi-agent/smoke + CodeQL/Snyk/Bandit)

## Phase 6 - Release Sync and Branch Hygiene

- [x] `git add -A`
- [x] `git commit -m \"<clear message>\"`
- [x] `git push origin main`
- [x] Remove only merged non-protected branches (local + remote)
- [x] Confirm `origin/main` == local `main`

## Phase 7 - Delivery Report (Single Final Message)

- [x] What changed (files + purpose)
- [x] What was executed (commands + outcomes)
- [x] Real-data verification proof (not dummy)
- [x] CI results (workflow URLs and statuses)
- [x] Open risks (if any) and exact next actions

Delivery report snapshot (2026-02-27):
- What changed:
  - Added advanced-risk KPI engine and API wiring:
    `python/kpis/advanced_risk.py`,
    `python/apps/analytics/api/models.py`,
    `python/apps/analytics/api/service.py`,
    `python/apps/analytics/api/main.py`.
  - Expanded realtime `/analytics/kpis` coverage to include:
    `LOSS_RATE`, `RECOVERY_RATE`, `CASH_ON_HAND`, `AVERAGE_LOAN_SIZE`,
    `DISBURSEMENT_VOLUME_MTD`, `NEW_LOANS_COUNT_MTD`,
    `ACTIVE_BORROWERS`, `REPEAT_BORROWER_RATE`, `AUTOMATION_RATE`,
    `PROCESSING_TIME_AVG`.
  - Closed remaining catalog coverage gaps by wiring:
    `DEFAULT_RATE`, `TOTAL_LOANS_COUNT`, and `CUSTOMER_LIFETIME_VALUE`
    in realtime API metadata/aliases.
  - Added advanced-risk tests:
    `python/tests/test_advanced_risk.py`,
    `python/tests/test_advanced_risk_api.py`,
    `python/tests/test_advanced_risk_openapi.py`.
  - Extended realtime KPI tests:
    `python/tests/test_kpi_service_realtime.py`,
    `python/tests/test_kpi_realtime_api.py`.
  - Updated this checklist with validated completion state.
- What was executed:
  - Lint/format: `ruff check .`, `black --check .`.
  - Tests: `pytest tests/ -m "not integration"`, `pytest python/multi_agent/ -k "test_"`,
    and targeted advanced-risk suites.
  - Pipeline (real data): dry-run, validate, full modes over
    `data/raw/abaco_real_data_20260202.csv`.
  - Security checks: `npm audit`, `safety`, `bandit`.
- Real-data verification proof:
  - Full pipeline run ID: `20260227_1c0def53`.
  - Compared recomputed KPIs from `clean_data.parquet` against
    `logs/runs/20260227_1c0def53/kpis_output.json` using canonical formulas.
- CI results:
  - Tests workflow: https://github.com/Arisofia/abaco-loans-analytics/actions/runs/22498904827 (success)
  - Security scan workflow: https://github.com/Arisofia/abaco-loans-analytics/actions/runs/22498904767 (success)
- Open risks and next actions:
  - Previous `protobuf` CVE-2026-0994 blocker has been remediated via Gemini SDK migration.
  - Next actions:
    1. Keep monitoring Safety/Snyk feeds for regressions in `protobuf`, `grpcio`, and `google-genai`.
    2. Optionally add CI assertions for the PR-review helper script path using `google-genai`.

---

## Quick Command Block (Copy/Paste)

```bash
python scripts/maintenance/validate_structure.py
python scripts/maintenance/abaco_infra_validator.py -v
npm audit --omit=dev
ruff check .
black --check .
pytest tests/ -v --tb=short -m "not integration"
pytest python/multi_agent/ -v -k "test_" --tb=short
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode dry-run
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode validate
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode full
```
