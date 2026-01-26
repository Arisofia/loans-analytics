# Backend Testing Guide (Pytest + DB seeding)
This document explains how to run backend tests that require a Postgres connection and how to use the Python seed/teardown manager.
## Setup (local)
1. Create a Python virtual environment (we recommend Python 3.11):
```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
```
2. Install runtime plus test utilities:
```bash
pip install -r requirements.txt
# requirements.txt now includes `Faker` and we rely on `psycopg[binary]` (psycopg 3.x)
```
3. Provide a Postgres connection string (DATABASE_URL) in a `.env` file at the repo root (or export it in your shell):
```
DATABASE_URL="postgresql://user:password@localhost:5432/your_db"
```
> Tip: For local development use a local or ephemeral DB instance. Do not point tests at production.
## DB Manager (tests/db_manager.py)
- `DBManager` implements:
  - `wipe_database()` — truncates a short list of tables (see `tables_to_clear`). Adjust to match your schema if needed.
  - `seed_kpi_data()` — inserts deterministic KPI rows used by backend tests and the Figma sync validation.
You can run it directly:
```bash
DATABASE_URL="$DATABASE_URL" python -m tests.db_manager
```
## Pytest integration
- The project already adds a session-scoped fixture `db_setup` (in `tests/conftest.py`) that:
  - Reads `DATABASE_URL`
  - Runs `wipe_database()` and `seed_kpi_data()` before tests run
- Use the `db_reset` fixture in tests to get a fresh seeded state per test.
## Example: Running tests
```bash
. .venv/bin/activate
export DATABASE_URL="postgresql://user:password@localhost:5432/your_db"
pytest -q
```
## Notes & Next steps
- The `tables_to_clear` list in `tests/db_manager.py` is intentionally small — please extend it as you identify other tables that need deterministic cleanup (e.g., `users`, `loans`, `transactions`).
- If your DB uses a different schema or column names, update the insert statements in `seed_kpi_data()` to match.
- If you prefer `psycopg2` instead of `psycopg` (psycopg3), a drop-in rewrite is straightforward — I used `psycopg` because this repo already lists `psycopg[binary]` in `requirements.txt`.
### CI: Ephemeral Postgres (recommended)
To run backend tests in CI without relying on a remote DB, use an ephemeral Postgres service container in your GitHub Actions workflow. Example tips:
- Use `postgres:15` service container and add a `--health-cmd pg_isready` options block so the job waits until Postgres is ready.
- Export `DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db` in the job environment before applying migrations and running tests.
- Apply SQL migrations with `psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f supabase/migrations/<file>.sql` in order.
Locally you can use Docker:
```bash
docker run --name abaco-test-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=test_db -p 5432:5432 -d postgres:15
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test_db"
pip install -r requirements.txt -r dev-requirements.txt
pytest -q
```
This keeps CI deterministic, fast, and isolated from shared/staging DBs.
