# Pipeline v2 Scaffold

This repository now includes a minimal, config-driven scaffold for the v2 canonical pipeline.
It lives alongside the existing v1 pipeline to avoid breaking current workflows.

## What is included

- `src/abaco_pipeline/`: v2 package scaffold (CLI, ingestion placeholders, KPI registry, quality gates).
- `config/kpis.yml`: versioned KPI definitions and validation ranges.
- `requirements.pipeline.txt`: baseline dependencies for the v2 pipeline scaffold.
- `supabase/migrations/20251231_pipeline_audit_tables.sql`: audit/lineage tables for run tracking.

## What is not included (yet)

- Production ingestion logic (Cascade API client, Looker import orchestration).
- Full KPI engine implementation.
- Database writer implementations.
- Full orchestration beyond the daily/backfill GitHub Actions workflows.

## Quick usage (config inspection)

```bash
python -m abaco_pipeline.main print-config --config config/pipeline.yml
```

To apply environment overrides, set `PIPELINE_ENV` before running:

```bash
PIPELINE_ENV=development python -m abaco_pipeline.main print-config
```

## Scheduled run (validate + publish)

```bash
python -m abaco_pipeline.main --config config/pipeline.yml --validate --publish
```

## Idempotency + quality gates

- Idempotency state is stored in `logs/runs/state.json` (configurable via `run.state_file`).
- Re-running with the same input hash will skip publish unless `--force` is set.
- Schema drift writes `logs/runs/<run_id>/schema_diff.json` and stops publish.
- Quality gates write `logs/runs/<run_id>/quality.json` and stop publish when thresholds fail.

```text

## Audit tables migration

Apply the migration to your Supabase/Postgres instance:

```bash
supabase db reset
```

Or run the SQL directly using `psql`:

```bash
psql "$SUPABASE_DB_URL" -f supabase/migrations/20251231_pipeline_audit_tables.sql
```

## Notes

- The v1 pipeline remains in `src/pipeline/`.
- The scaffold is intentionally minimal and safe to extend without destabilizing v1.
