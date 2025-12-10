# ABACO — Loan Analytics Platform

## Golden Path: Adding a KPI, Dashboard View, or Agent

Follow these steps to ship changes with full lineage, tests, and persona contracts.

### 1) Define the KPI contract

- Update `config/kpis/kpi_definitions.yaml` with metric id, owner, formula, and refresh cadence.
- If the KPI is persona-specific, add it to `config/personas.yml` with alert thresholds and provenance.

### 2) Model and migrate

- Add SQL models and create/update migrations under `sql/migrations/` for lineage tables if needed.
- Keep calculations deterministic and reference upstream tables in `lineage` metadata columns.

### 3) Validate data quality

- Add or extend pytest cases in `tests/data_tests/` to assert exact outputs using sample CSVs.
- Run `pytest tests/data_tests/test_kpi_contracts.py` locally before opening a PR.

### 4) Wire orchestration

- Register extraction/validation/compute steps in `orchestration/airflow_dags/` for daily refresh.
- Ensure DAG tasks push lineage identifiers (ingest_run_id, kpi_snapshot_id) for downstream agents.

### 5) Expose the dashboard

- Add or update the Next.js route in `apps/web/src/app/<persona>/page.tsx` with provenance tooltips.
- Run `npm run lint` from the repo root after UI changes.

### 6) Update agents and logging

- When agents use the new KPI, log executions via `python/agents/orchestrator.py` to the `agent_runs` table.
- Capture prompt version, model, input hash, output markdown, and citations.

### 7) CI and PR expectations

- CI blocks merges if KPI logic changes without a config update or if KPI contract tests fail.
- Keep PR summaries concise and focused on lineage, contracts, and persona impact.
