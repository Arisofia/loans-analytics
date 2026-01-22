# Audit + Lineage (Supabase)

This repo ships a minimal, regulator/investor-grade audit model for pipeline runs and KPI provenance.

## What gets stored

Tables are created in the `analytics` schema:

- `analytics.pipeline_runs`
- `analytics.raw_artifacts`
- `analytics.kpi_values`
- `analytics.data_quality_results`

Migration:

- `supabase/migrations/20251231_pipeline_audit_tables.sql`

## Required environment variables

- `SUPABASE_URL` (e.g., `https://<project>.supabase.co`)
- `SUPABASE_SERVICE_ROLE` (service-role key; server-side only)

Back-compat:

- `SUPABASE_SERVICE_ROLE_KEY` is also accepted.

## End-to-end (dry run)

Prints the enriched payload that would be written (adds `config_version`, `git_sha`, and defaults `kpi_def_version`).

- `make audit-dry-run`

## End-to-end (write to Supabase)

- `make audit-write`

This posts to Supabase PostgREST:

- `POST /rest/v1/analytics.pipeline_runs?on_conflict=run_id` (upsert)
- `POST /rest/v1/analytics.raw_artifacts`
- `POST /rest/v1/analytics.kpi_values`
- `POST /rest/v1/analytics.data_quality_results?on_conflict=run_id` (upsert)

## Payload format

Example payload lives at:

- `config/audit_payload.example.json`

CLI:

- `python -m src.abaco_pipeline.main --config config/pipeline.yml write-audit --kpis-config config/kpis.yml --payload <payload.json> [--dry-run]`
