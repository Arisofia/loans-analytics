# Integration Tests

These tests require real external services and network connectivity.

## Running Integration Tests

### Locally
```bash
# Requires Supabase credentials in .env or environment
export RUN_REAL_SUPABASE_TESTS=1
export SUPABASE_URL=your-supabase-url
export SUPABASE_ANON_KEY=your-supabase-key

pytest python/multi_agent/test_historical_supabase_integration.py -m integration_supabase -v
```

### In CI
Integration tests run automatically via dedicated workflow (`.github/workflows/historical_supabase_integration.yml`) on:
- Manual trigger (`workflow_dispatch`)
- Nightly schedule (3 AM UTC)

They use GitHub secrets for credentials and only run when secrets are available. The workflow sets `RUN_REAL_SUPABASE_TESTS: '1'` in its environment variables to enable the real network tests.

## Test Types

### Unit Tests (Default)
- No external dependencies
- Run on every PR
- Fast (<5 seconds total)
- Always enabled

### Integration Tests (Opt-in)
- Require Supabase credentials (`SUPABASE_URL`, `SUPABASE_ANON_KEY`)
- Require network connectivity
- Require explicit enablement via `RUN_REAL_SUPABASE_TESTS=1`
- Skip automatically in local dev unless enabled
- Run via dedicated workflow in CI

## Disabling Integration Tests

Integration tests are disabled by default. To explicitly exclude them:

```bash
# Run only unit tests (explicit exclusion)
pytest -m "not integration_supabase"

# Or in VS Code settings.json
"python.testing.pytestArgs": ["-m", "not integration_supabase"]
```

## Test Markers

- `integration_supabase`: Tests that require real Supabase connection
- `stats`: Advanced statistical tests (optional)

## Environment Variables

- `RUN_REAL_SUPABASE_TESTS`: Set to `1` to enable real network tests
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Your Supabase anonymous key
- `HISTORICAL_CONTEXT_MODE`: Set to `REAL` for production mode (default: `MOCK`)

## Troubleshooting

### DNS Resolution Errors
```
urllib3.exceptions.NameResolutionError: Failed to resolve 'pljjgdtczxmrxydfuaep.supabase.co'
```

**Cause**: Tests attempting real network calls without proper configuration.

**Solution**: 
1. Ensure `RUN_REAL_SUPABASE_TESTS=1` is set
2. Verify Supabase credentials are configured
3. Check network connectivity

### Tests Skipped Unexpectedly
```
SKIPPED [1] test_historical_supabase_integration.py: Real Supabase tests disabled
```

**Cause**: `RUN_REAL_SUPABASE_TESTS` not set or Supabase credentials missing.

**Solution**: Set environment variable and credentials as shown above.

## CI/CD Workflows

### Main CI (`ci.yml`)
- Runs on every PR and push to main
- Excludes integration tests: `pytest -m "not integration_supabase"`
- Fast feedback loop

### Multi-Agent Tests (`multi-agent-tests.yml`)
- Runs agent orchestration tests
- Excludes integration tests requiring network
- Tests agent communication and chaining

### Historical Supabase Integration (`historical_supabase_integration.yml`)
- Dedicated workflow for Supabase integration tests
- Manual trigger or nightly schedule
- Uses GitHub secrets for credentials
- Only runs when secrets are available
