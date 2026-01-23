# E2E Testing Guide (Playwright)

This document explains how to run the Playwright E2E tests for `apps/web` and how we recommend configuring test credentials for Supabase.

## Quick start (local)

1. From repo root, install dependencies in the web app:

```bash
cd apps/web
npm install
npx playwright install
```

2. Create a `.env.local` in `apps/web` or at the repo root (Playwright config reads `.env.local` from `apps/web` by default). Add test credentials and (optionally) a Service Role key for automatic DB seeding:

```env
E2E_TEST_EMAIL="e2e-bot@example.com"
E2E_TEST_PASSWORD="super-secure-password"
# Optional (required only if you want the Playwright setup to seed/reset DB automatically):
## SUPABASE_URL should be set in your environment, not in this file.
## SUPABASE_SERVICE_ROLE_KEY should be set in your environment, not in this file.
```

> Create a dedicated test user in your Supabase instance (preferably a local or staging instance). Avoid using production credentials.

3. Run tests (Playwright will start the dev server automatically when configured):

```bash
# in apps/web
npm run test:e2e
```

For CI-friendly runs (installed browsers + GitHub reporter):

```bash
npm run test:e2e:ci
```

## Files created by the scaffolding

- `apps/web/playwright.config.ts` — Playwright configuration (webServer, baseURL, projects, storageState)
- `apps/web/e2e/setup-auth.spec.ts` — Auth setup test that logs in once and saves `playwright/.auth/user.json`
- `apps/web/e2e/lib/db-utils.ts` — TestDataManager helper that can reset and seed DB using the Supabase Service Role key
- `apps/web/e2e/dashboard-executive.spec.ts` — Example executive dashboard test
- `apps/web/.env.local.example` — Example env file with E2E vars
- `.github/workflows/playwright.yml` — Workflow to run Playwright tests on PRs or pushes to `main`

## Authentication strategy

- Use a dedicated Supabase test user (e.g., `e2e-bot@example.com`) on a local/staging Supabase instance.
- If you want to test RLS and security rules, use actual Supabase credentials (local/staging). If you only want UI behavior (faster), you can mock API calls instead (not recommended for critical dashboards).
- To avoid re-authenticating before every test, the `setup-auth.spec.ts` saves storage state to `playwright/.auth/user.json`. **This file is ignored by git**.

## Seeding and teardown (recommended)

- Use the Supabase CLI or the helper Node scripts provided at `apps/web/scripts/e2e/` to seed test data and remove it after tests run.
- Scripts provided:
  - `apps/web/scripts/e2e/seed_test_data.js` — Creates the E2E user and optionally inserts rows into a table.
  - `apps/web/scripts/e2e/teardown_test_data.js` — Reads the seed state file and deletes inserted rows and the created test user.

Usage example (local):

```bash
# from repo root
cd apps/web
# create test user and optionally insert rows (set E2E_SEED_TABLE and E2E_SEED_ROWS for table inserts)
E2E_SEED_TABLE='loans' E2E_SEED_ROWS='[{"amount":1000, "status":"active"}]' \
  # SUPABASE_URL='https://xyz.supabase.co' SUPABASE_SERVICE_ROLE_KEY='your_service_role_key' \
  E2E_TEST_EMAIL='e2e-bot@example.com' E2E_TEST_PASSWORD='super-secret' npm run e2e:seed

# run tests
npm run test:e2e

# teardown after tests
# SUPABASE_URL='https://xyz.supabase.co' SUPABASE_SERVICE_ROLE_KEY='your_service_role_key' npm run e2e:teardown
```

- The scripts write state to `apps/web/playwright/.e2e/seed_state.json` to know what to teardown later. This folder is ignored by git.

- As an alternative to running the seed scripts manually, the Playwright auth setup will automatically call the TestDataManager (implemented in `apps/web/e2e/lib/db-utils.ts`) when `SUPABASE_SERVICE_ROLE_KEY` and `SUPABASE_URL` are present in the environment. This allows the auth setup test to ensure the test user exists and to run deterministic seeding (reset → seed) before saving `playwright/.auth/user.json`.

- For CI, add these secrets in GitHub Settings → Secrets → Actions:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `E2E_TEST_EMAIL`
  - `E2E_TEST_PASSWORD`
  - Optional: `E2E_SEED_TABLE`, `E2E_SEED_ROWS` (JSON string)

Notes:
- The scripts and TestDataManager use the Supabase Service Role key; never commit this key into the repository or .env files.
- If your table has a different primary key name, adjust the scripts or TestDataManager accordingly to capture and delete inserted rows by the appropriate column.

For backend-focused tests (pytest + Postgres), see `docs/backend-testing.md` which documents the Python `DBManager`, `DATABASE_URL` usage, and pytest fixtures.

## CI secrets

Add these repository secrets in GitHub Settings → Secrets → Actions:

- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (required for automatic seeding/reset in CI)
- `E2E_TEST_EMAIL`
- `E2E_TEST_PASSWORD`

The workflow uses these secrets to run the seed step (if configured), run Playwright tests, and perform teardown. Do not store the Service Role key in the repo — use GitHub Secrets only.

## Security note

Never commit real credentials into the repository. Use `env` files locally and GitHub Secrets for CI.

---

If you want, I can add a simple `scripts/e2e/seed.py` + `teardown.py` that use the Supabase Python client to seed and tear down test data. Would you like that? (It can be added as optional step.)
