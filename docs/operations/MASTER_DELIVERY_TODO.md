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
- [ ] Resolve High/Critical dependency findings
- [ ] Ensure Snyk gate is strict when scan executes (workflow must fail on High/Critical)

Validation:
- [ ] No blocking High/Critical vulns in dependency scan
- [x] Security workflow remains green after remediation

Current notes:
- `safety` still reports `protobuf` vulnerability `CVE-2026-0994` (ID `85151`), currently blocked by upstream version constraints (`google-ai-generativelanguage` and `grpcio-status` pins).
- `bandit` report contains only `LOW` severity findings (`80`), with no `MEDIUM/HIGH`.

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
- [ ] If secrets present: `pytest tests/ -v -m \"integration\" --tb=short`

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

- [ ] `git add -A`
- [ ] `git commit -m \"<clear message>\"`
- [ ] `git push origin main`
- [x] Remove only merged non-protected branches (local + remote)
- [x] Confirm `origin/main` == local `main`

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
