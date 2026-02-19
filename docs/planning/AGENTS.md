# AGENTS.md

## Repository expectations

- Run `npm run lint` at the repository root for JS/TS changes (this delegates to
  the web app lint task). If you update another package with its own lint
  workflow, run that package's documented lint command instead.
- Document public utilities in `docs/` when you change behavior.

## Unified agents

- **Pipeline orchestration**: ingestion & transformation logging and compliance
  helpers (owner: data engineering, reviewer: analytics ops) ensures schema
  verification, lineage capture, and audit metadata are versioned with outputs.
- **Validation & compliance utilities**: `src/pipeline/ingestion.py` enforces
  required column validation today, while `src/compliance` is planned to mask
  detected PII, record access, and serialize the report (owner: data
  engineering, reviewer: data privacy) so that workflow context is versioned in
  `logs/runs`.
- **Collaboration**: key artefacts (manifests, compliance reports, access logs)
  remain under the pipeline workflow repo path with associated metadata and
  reviewer approvals in PR descriptions.

## Agent Roles

### 1. Pipeline Orchestrator Agent

- Triggers:
  - New ingestion runs (GitHub Actions schedule, manual ops request).
  - Backfills / re-runs for specific dates or portfolios.
- Responsibilities:
  - Call `scripts/data/run_data_pipeline.py` with approved parameters.
  - Ensure preconditions:
    - Required secrets are present.
    - Source datasets accessible (storage / DB).
  - Publish run metadata:
    - Start/end time, duration.
    - Input dataset version / commit SHA.
    - Exit status and error summary.

### 2. Validation & Compliance Agent

- Triggers:
  - Immediately after each pipeline run (success or controlled failure).
- Responsibilities:
  - Run schema validation (ingestion validation results from `src/pipeline/ingestion.py`).
  - Run PII/compliance checks (`src/compliance`, planned).
  - Persist:
    - Validation report.
    - Compliance report.
    - PII findings (masked, aggregated).
  - Write artefacts to:
    - `logs/runs/<run_id>/validation_report.json`
    - `logs/runs/<run_id>/compliance_report.json`

### 3. Observability & Performance Agent

- Triggers:
  - Every pipeline run (via CI workflow, e.g. `run_pipeline_daily.yml`).
- Responsibilities:
  - Measure:
    - End-to-end runtime.
    - Records processed.
    - Error rate.
  - Compare against baselines and thresholds.
  - Emit:
    - Supabase metrics row (for trend analysis).
    - GitHub issue / notification if degraded.

### 4. Collaboration Agent (Change Management)

- Triggers:
  - On PRs affecting pipeline, KPIs, or compliance modules.
- Responsibilities:
  - Enforce:
    - PR checklists (validation, tests, risk impact).
    - Required reviewers (data engineering + data privacy).
  - Summarize changes:
    - Affected flows.
    - KPI impact.
    - Backward-compatibility notes.

## Implementation Mapping

- Pipeline Orchestrator Agent
  - Entrypoint: `scripts/data/run_data_pipeline.py`
  - Workflows:
    - `.github/workflows/run_pipeline_daily.yml`
    - `.github/workflows/batch_export_scheduled.yml`
    - `.github/workflows/agents_unified_pipeline.yml`

- Validation & Compliance Agent
  - Validation:
    - `src/pipeline/ingestion.py` (schema validation results emitted in run manifest)
  - Compliance (planned / evolving):
    - `src/compliance`
  - Artefact paths:
    - `logs/runs/<run_id>/validation_report.json`
    - `logs/runs/<run_id>/compliance_report.json`

- Observability & Performance Agent
  - Workflows:
    - `.github/workflows/run_pipeline_daily.yml`
    - `.github/workflows/agents_unified_pipeline.yml`
  - Metrics Store:
    - Supabase `pipeline_performance_metrics` (existing)
  - Reporting:
    - GitHub Issues (automated)
    - Workflow run summaries

- Collaboration Agent
  - GitHub configuration:
    - PR templates.
    - CODEOWNERS for `src/pipeline`, `src/kpis`, `src/compliance`.
  - Validation:
    - `.github/workflows/agent-checklist-validation.yml`
