# SQL Directory Conventions

This folder contains SQL assets for multiple runtimes.

- `sql/migrations/`: PostgreSQL migrations only (safe for migration runners).
- `sql/models/`: PostgreSQL analytical views/models.
- `sql/calculations/`: validated PostgreSQL calculation queries.
- `sql/non_postgres/`: SQL Server / BigQuery reference scripts (not executable in Postgres).
- `sql/drafts/`: incomplete drafts/placeholders; not production-safe.

Never execute files from `sql/non_postgres/` or `sql/drafts/` as database migrations.
