# SQL Directory Conventions

This folder contains SQL assets for multiple runtimes.

- `sql/migrations/`: PostgreSQL migrations only (safe for migration runners).
- `sql/models/`: PostgreSQL analytical views/models.
- `sql/calculations/`: validated PostgreSQL calculation queries.
Never execute raw SQL files as database migrations — use the migration runner with `migration_index.yml`.
