# Alembic Migration Governance

This directory hosts schema migration governance for deployment environments.

## Usage

1. Configure `sqlalchemy.url` in `alembic.ini` (or override via env var in CI/CD).
2. Generate migration:

```bash
alembic revision -m "describe_change"
```

3. Apply migrations:

```bash
alembic upgrade head
```

## Policy

- Migrations must be idempotent and reviewed.
- Production releases must include `alembic upgrade head` in the deployment gate.
