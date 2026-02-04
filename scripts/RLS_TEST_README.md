# RLS Smoke Test Runner

Quick end-to-end validation that Row Level Security is working correctly in production.

## Quick Start

### 1. Install Dependencies

```bash
npm install @supabase/supabase-js
```

### 2. Set Environment Variables

```bash
# Required
export SUPABASE_URL="***REMOVED***"
export SUPABASE_ANON_KEY="your-anon-key-here"           # From Supabase Dashboard > Settings > API
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"    # From Supabase Dashboard > Settings > API (KEEP PRIVATE)

# Optional (for authenticated user tests)
export TEST_USER_EMAIL="user@example.com"
export TEST_USER_PASSWORD="password"
```

### 3. Run Tests

```bash
node scripts/test-rls.js
```

## Test Scenarios

### Test 1: Anonymous Key Should NOT Access Data ✅

- **What it tests**: RLS blocks anonymous API key from reading sensitive tables
- **Expected**: Error with code PGRST301 (permission denied)
- **Tables**: customer_data, loan_data, financial_statements
- **Status**: ✅ PASS if error occurs

### Test 2: Service Role Should Have Full Access ✅

- **What it tests**: Backend service role can read/write all tables
- **Expected**: Successfully retrieve data from customer_data, loan_data, kpi_values
- **Tables**: customer_data, loan_data, kpi_values
- **Status**: ✅ PASS if no errors and data returned

### Test 3: Authenticated User Access (Role-Based) ✅

- **What it tests**: Authenticated JWT users see data filtered by RLS policies
- **Expected**: Can read KPI values (limited by role-based policy)
- **Tables**: kpi_values
- **Status**: ✅ PASS if user can read KPIs (or PGRST301 if not authorized)
- **Requires**: TEST_USER_EMAIL and TEST_USER_PASSWORD set

### Test 4: RLS Enabled on Tables ✅

- **What it tests**: RLS is enabled on all sensitive tables
- **Expected**: pg_tables.rowsecurity = true for customer_data, loan_data, financial_statements, kpi_values
- **Status**: ✅ PASS if all show rowsecurity=true
- **Note**: Requires admin access (run via psql or db dashboard)

## Output Format

```
═══════════════════════════════════════════════════════════════
     RLS SMOKE TEST SUITE - SUPABASE PRODUCTION SECURITY
═══════════════════════════════════════════════════════════════

ℹ️  Testing: ***REMOVED***
ℹ️  Anon Key: ✓ Set
ℹ️  Service Role Key: ✓ Set
ℹ️  Test User: ✗ Missing

TEST 1: Anonymous Key Access (Should FAIL)
✅ Anonymous correctly blocked from reading customer_data (RLS policy enforced)

TEST 2: Service Role Access (Should SUCCEED)
✅ Service role has full read access (returned 5 rows)
✅ Service role has full read access to loan_data (returned 42 rows)
✅ Service role has full read access to kpi_values (returned 1200 rows)

TEST 3: Authenticated User Access (Should use policies)
⚠️  TEST_USER_EMAIL or TEST_USER_PASSWORD not set, skipping authenticated user test

TEST 4: RLS Status on Tables (Direct DB Check)
ℹ️  RLS Status Check: Requires direct database access

═══════════════════════════════════════════════════════════════
TEST SUMMARY
═══════════════════════════════════════════════════════════════

✅ Anonymous customer_data access
✅ Service role customer_data read
✅ Service role loan_data read
✅ Service role kpi_values read

Total Passed: 4
Total Failed: 0
Total Skipped: 2

✅ ALL TESTS PASSED! RLS is working correctly.
```

## Troubleshooting

### Test fails: "Anonymous should not have access"

- **Cause**: RLS not enabled or policy allows anonymous
- **Fix**: Run SQL in Supabase dashboard:
  ```sql
  ALTER TABLE public.customer_data ENABLE ROW LEVEL SECURITY;
  SELECT * FROM pg_policies WHERE tablename = 'customer_data';
  ```

### Test fails: "Service role should have full access"

- **Cause**: Policy restricts service_role or permission denied
- **Fix**: Check service_role has `sql` permission and policies allow it:
  ```sql
  SELECT * FROM pg_policies WHERE tablename = 'customer_data';
  -- Should show policies that allow service_role or use USING (true)
  ```

### Test fails: "Authenticated user"

- **Cause**: Invalid JWT token or user doesn't exist
- **Fix**: Verify user is signed up in Supabase Auth, or create test user:
  ```bash
  supabase auth users create --email "test@abaco.com" --password "test123"
  ```

### Tests skipped: "Environment variable not set"

- Set the missing environment variable and retry
- For authenticated tests: `export TEST_USER_EMAIL="test@abaco.com" TEST_USER_PASSWORD="test123"`

## Integration with CI/CD

Add to your GitHub Actions or CI pipeline:

```yaml
- name: Run RLS Smoke Tests
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    npm install @supabase/supabase-js
    node scripts/test-rls.js
```

## Related Documentation

- [RLS_VERIFICATION_TESTS.md](../docs/RLS_VERIFICATION_TESTS.md) - Manual test scenarios and psql queries
- [DEPLOYMENT_LOG_2026_02_04.md](../docs/DEPLOYMENT_LOG_2026_02_04.md) - Deployment record and sign-offs
- [SECURITY_STATUS_REPORT.md](../docs/SECURITY_STATUS_REPORT.md) - Vulnerability details and remediation
