# Integration Tests Setup for G4.2 Historical KPIs

## Overview

The G4.2.1 integration test suite validates REAL mode against an actual Supabase instance. These tests require valid Supabase credentials to run and will gracefully skip if they are not provided.

## Running Integration Tests

### Option 1: Skip Integration Tests (Default - No Supabase Required)

If you don't have Supabase credentials, run unit tests only:

```bash
# Run all tests EXCEPT integration tests
pytest -m "not integration_supabase"

# Or run only specific unit test files
pytest python/multi_agent/test_config_historical.py
```

### Option 2: Run Integration Tests (Requires Valid Supabase Credentials)

To run REAL mode integration tests, provide valid Supabase credentials:

```bash
# Set real Supabase credentials (not placeholders)
export SUPABASE_URL="https://your-actual-project-ref.supabase.co"
export SUPABASE_ANON_KEY="your-real-anon-key-starts-with-eyJ"

# Run integration tests
pytest python/multi_agent/test_historical_supabase_integration.py -m integration_supabase -v

# Or run all tests (unit + integration)
pytest -v
```

## Important: Credential Validation

The integration test suite validates that your credentials are:

1. **Present** - Both `SUPABASE_URL` and `SUPABASE_ANON_KEY` environment variables are set
2. **Not Placeholders** - The following are rejected as invalid:
   - URLs containing `your-project` or `your-project.supabase.co`
   - Keys containing `your-key` or `your-anon-key`
3. **Properly Formatted** - URLs must follow the pattern `https://{project-ref}.supabase.co`

If credentials are invalid or missing, integration tests will **skip automatically** with a message:

```
SKIPPED [reason: Supabase credentials not configured (SUPABASE_URL, SUPABASE_ANON_KEY)]
```

## Common Scenarios

### Scenario 1: Local Development (No Supabase)

```bash
# Unset any test credentials
unset SUPABASE_URL
unset SUPABASE_ANON_KEY

# Run unit tests only
pytest -m "not integration_supabase" -v
```

**Result:** ✅ Unit tests pass, integration tests skipped

### Scenario 2: CI/CD Pipeline (With Supabase Secrets)

```bash
# GitHub Actions will provide secrets as environment variables
# The integration tests will run automatically if secrets are configured
pytest python/multi_agent/test_historical_supabase_integration.py -m integration_supabase -v
```

**Result:** ✅ Integration tests run and validate REAL mode

### Scenario 3: Testing with Placeholder Credentials (Previous Issue)

❌ **This will no longer work** - placeholders are now rejected:

```bash
# These placeholders will be detected and tests will skip
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-key"

pytest python/multi_agent/test_historical_supabase_integration.py -m integration_supabase -v
```

**Result:** ✅ Tests skip gracefully (no failure), with reason message

## Obtaining Real Supabase Credentials

1. **Create a Supabase Project** (if you don't have one):
   - Go to [https://app.supabase.com](https://app.supabase.com)
   - Create a new project
   - Wait for the database to be created

2. **Get Your Credentials**:
   - Project Settings → API → URLs
   - Copy the **Project URL** (format: `https://xxxxx.supabase.co`)
   - Copy the **anon** public key (starts with `eyJ...`)

3. **Set Environment Variables**:

   ```bash
   export SUPABASE_URL="https://xxxxx.supabase.co"
   export SUPABASE_ANON_KEY="eyJ..."
   ```

4. **Create the Schema** (one-time):

   ```bash
   supabase db push  # Apply migrations
   ```

5. **Run Integration Tests**:
   ```bash
   pytest python/multi_agent/test_historical_supabase_integration.py -m integration_supabase -v
   ```

## Test Flow

When you run integration tests:

1. **Credential Check** → `_supabase_configured()` validates environment variables
   - ✅ Valid & real → Tests run
   - ❌ Missing/placeholder → Tests skip gracefully
   - ❌ Malformed → Tests skip with reason

2. **Connection Test** → `test_supabase_backend_connection()` verifies network access
   - ✅ Can reach Supabase → Tests continue
   - ❌ Network error → Test fails (DNS, timeout, etc.)
   - ❌ Invalid key → Test fails (401 Unauthorized)

3. **Data Tests** → `test_historical_context_provider_real_mode_roundtrip()` etc.
   - ✅ Data contract is valid → Test passes
   - ❌ Schema missing → Test fails (table not found)
   - ❌ Wrong data format → Test fails (assertion error)

## Troubleshooting

### Tests Skip with "Supabase credentials not configured"

This is **expected behavior** and means:

- Your environment variables are not set, OR
- They contain placeholder/example values

**Solution:** Provide real Supabase credentials (see "Obtaining Real Supabase Credentials" above)

### Tests Fail with "Failed to resolve hostname"

The credentials are valid but the Supabase instance is not reachable:

- Check your internet connection
- Verify the Supabase project URL is correct (no typos)
- Ensure your Supabase project is active (not paused)

### Tests Fail with "401 Unauthorized"

The anon key is invalid or expired:

- Regenerate the anon key in Supabase → Project Settings → API
- Update your environment variables with the new key

### Tests Fail with "Table historical_kpis does not exist"

The database schema has not been created:

- Run `supabase db push` to apply migrations
- Verify the migration file exists: `db/migrations/20260201_create_historical_kpis.sql`

## CI/CD Integration

The GitHub Actions workflow `.github/workflows/historical_supabase_integration.yml` automatically:

1. Checks if Supabase secrets are configured
2. Skips gracefully if they're missing (no failure)
3. Runs integration tests if secrets are present
4. Reports results

To enable it:

1. Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to GitHub repository secrets
2. The workflow will automatically include them in scheduled (nightly) and manual runs

## Summary

| Scenario                         | Credentials                | Command                                | Result                   |
| -------------------------------- | -------------------------- | -------------------------------------- | ------------------------ |
| Local development, no Supabase   | None                       | `pytest -m "not integration_supabase"` | ✅ Unit tests pass       |
| Local development, with Supabase | Real                       | `pytest`                               | ✅ All tests pass        |
| Placeholder credentials          | `your-project.supabase.co` | `pytest`                               | ✅ Tests skip gracefully |
| CI/CD with secrets               | Real (from GitHub secrets) | Auto-triggered                         | ✅ Integration tests run |
| CI/CD without secrets            | None                       | Auto-triggered                         | ✅ Tests skip gracefully |
