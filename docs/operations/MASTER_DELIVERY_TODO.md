# Master Delivery TODO (No-Pause Flow)

Single execution checklist to complete end-to-end delivery without stopping every few changes.

## Rules (always-on)

- [ ] Work only on canonical paths from `docs/operations/SCRIPT_CANONICAL_MAP.md`
- [ ] Keep one active command/doc per task (remove duplicates and stale references)
- [ ] Use real input data only for pipeline validations
- [ ] No dummy/sample fallback in production code paths
- [ ] Keep `main` as source of truth and sync frequently

## Phase 0 - Baseline Snapshot

- [ ] `git status --short`
- [ ] `git rev-parse --short HEAD`
- [ ] `python scripts/maintenance/validate_structure.py`
- [ ] Confirm working dataset exists: `data/raw/abaco_real_data_20260202.csv`

Exit criteria:
- [ ] Repository structure validation = 100%
- [ ] Baseline state documented in delivery notes

## Phase 1 - Repo Hygiene (Single Flow)

- [ ] Remove duplicate files (e.g., names ending in ` 2`, duplicate docs, duplicate scripts)
- [ ] Remove orphan references to deleted/legacy routes
- [ ] Remove stale CI/workflow refs and obsolete process references
- [ ] Ensure only one canonical entrypoint per operation

Validation:
- [ ] `rg -n --hidden --glob '!node_modules/**' --glob '!.git/**' \"( 2\\.| copy|duplicate|deprecated path)\"`
- [ ] `python scripts/maintenance/validate_structure.py`

## Phase 2 - Dependency and Security Hardening

- [ ] Run dependency audit:
- [ ] `npm audit --omit=dev`
- [ ] `pip install -r requirements.txt` (CI-equivalent venv)
- [ ] Run security scans:
- [ ] `safety check --continue-on-error --save-json /tmp/safety-results.json`
- [ ] `bandit -r python src scripts -f json -o /tmp/bandit-report.json`
- [ ] Resolve High/Critical dependency findings
- [ ] Ensure Snyk gate is strict when scan executes (workflow must fail on High/Critical)

Validation:
- [ ] No blocking High/Critical vulns in dependency scan
- [ ] Security workflow remains green after remediation

## Phase 3 - Real Data Pipeline Validation (All Modes)

- [ ] Dry-run ingestion:
- [ ] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode dry-run`
- [ ] Validate mode:
- [ ] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode validate`
- [ ] Full mode:
- [ ] `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv --mode full`
- [ ] Confirm artifacts exist under `logs/runs/<run_id>/`

Calculation integrity:
- [ ] Independently recompute critical KPIs from `clean_data.parquet`
- [ ] Compare against `kpis_output.json` and confirm exact/expected tolerance

## Phase 4 - Test and Quality Gate

- [ ] `ruff check .`
- [ ] `black --check .`
- [ ] `pytest tests/ -v --tb=short -m \"not integration\"`
- [ ] `pytest python/multi_agent/ -v -k \"test_\" --tb=short`
- [ ] If secrets present: `pytest tests/ -v -m \"integration\" --tb=short`

Exit criteria:
- [ ] All required checks pass
- [ ] No new failing tests

## Phase 5 - CI/Actions Verification

- [ ] Push branch/`main`
- [ ] Verify latest runs for commit SHA:
- [ ] `Tests` workflow = success
- [ ] `Security Scan` workflow = success
- [ ] Inspect job-level details (unit/integration/multi-agent/smoke + CodeQL/Snyk/Bandit)

## Phase 6 - Release Sync and Branch Hygiene

- [ ] `git add -A`
- [ ] `git commit -m \"<clear message>\"`
- [ ] `git push origin main`
- [ ] Remove only merged non-protected branches (local + remote)
- [ ] Confirm `origin/main` == local `main`

## Phase 7 - Delivery Report (Single Final Message)

- [ ] What changed (files + purpose)
- [ ] What was executed (commands + outcomes)
- [ ] Real-data verification proof (not dummy)
- [ ] CI results (workflow URLs and statuses)
- [ ] Open risks (if any) and exact next actions

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
