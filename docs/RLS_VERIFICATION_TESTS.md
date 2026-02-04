# RLS Verification Tests — Post-Deployment Smoke Tests

**Date**: February 4, 2026  
**Purpose**: Verify that Row Level Security is functioning correctly in production after 20260204100000, 20260204120000, 20260204120500 migrations

---

## Quick Verification Checklist

Before running full tests, confirm these basic checks:

```bash
# 1. Verify RLS is enabled on protected tables
supabase db dump --linked | grep -i "enable row level security"

# 2. Verify migration history (should show all 8)
supabase migration list

# 3. Verify monitoring schema exists
supabase db dump --linked | grep -i "create schema.*monitoring"
```

---

## Test 1: Anonymous Key (Should FAIL - No Access)

**Setup**: Obtain your `anon` key from Supabase Dashboard → Settings → API

```javascript
// supabase-js example (Node.js or browser)
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = '***REMOVED***'
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY_HERE'

const anonClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Test: Try to read customer_data (should be blocked by RLS)
async function testAnonNoAccess() {
  const { data, error } = await anonClient
    .from('customer_data')
    .select('*')
    .limit(1)

  console.log('=== Anonymous Key Test ===')
  console.log('Error (expected):', error?.message)
  console.log('Data (expected: null):', data)

  if (error && error.code === 'PGRST301') {
    console.log('✅ PASS: Anonymous access blocked by RLS')
    return true
  } else {
    console.log('❌ FAIL: Anonymous should not have access')
    return false
  }
}

testAnonNoAccess()
```

**Expected Output:**

```
=== Anonymous Key Test ===
Error (expected): new row violates row-level security policy for table "customer_data"
Data (expected: null): null
✅ PASS: Anonymous access blocked by RLS
```

---

## Test 2: Service Role (Should SUCCEED - Full Access)

**Setup**: Use service_role key from Supabase Dashboard → Settings → API (keep private!)

```javascript
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = '***REMOVED***'
const SERVICE_ROLE_KEY = 'YOUR_SERVICE_ROLE_KEY_HERE' // Private - never expose

const adminClient = createClient(SUPABASE_URL, SERVICE_ROLE_KEY)

// Test: Read customer_data as service_role (should succeed)
async function testServiceRoleFullAccess() {
  const { data, error } = await adminClient
    .from('customer_data')
    .select('*')
    .limit(1)

  console.log('=== Service Role Test ===')
  console.log('Error:', error)
  console.log('Rows returned:', data?.length ?? 0)

  if (!error && data && data.length >= 0) {
    console.log('✅ PASS: Service role has full access')
    return true
  } else {
    console.log('❌ FAIL: Service role should have full access')
    return false
  }
}

testServiceRoleFullAccess()
```

**Expected Output:**

```
=== Service Role Test ===
Error: null
Rows returned: 1
✅ PASS: Service role has full access
```

---

## Test 3: Authenticated JWT User (Should Use Policies)

**Setup**: Get a JWT token from your auth system (e.g., `supabase.auth.getSession()` in your app)

```javascript
import { createClient } from '@supabase/supabase-js'

const SUPABASE_URL = '***REMOVED***'
const SUPABASE_ANON_KEY = 'YOUR_ANON_KEY_HERE'

const userClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Test: Authenticated user accessing KPI values (should succeed if email matches @abaco.*)
async function testAuthenticatedKPIAccess() {
  // First, sign in or get a valid session
  const {
    data: { session },
  } = await userClient.auth.getSession()

  if (!session) {
    console.log('❌ No active session. Sign in first.')
    return false
  }

  const userEmail = session.user.email
  console.log('=== Authenticated User Test ===')
  console.log('User email:', userEmail)

  // Test reading KPI values
  const { data, error } = await userClient
    .from('kpi_values')
    .select('*')
    .limit(1)

  console.log('Error:', error)
  console.log('KPI rows returned:', data?.length ?? 0)

  if (userEmail?.endsWith('@abaco.')) {
    if (!error && data) {
      console.log('✅ PASS: @abaco.* user can read KPI values')
      return true
    } else {
      console.log('❌ FAIL: @abaco.* user should read KPI values')
      return false
    }
  } else {
    if (error?.code === 'PGRST301') {
      console.log('✅ PASS: Non-@abaco.* user correctly denied')
      return true
    } else {
      console.log('⚠️  User email does not match @abaco.*, cannot test access')
      return null
    }
  }
}

testAuthenticatedKPIAccess()
```

---

## Test 4: Direct SQL (psql) Verification

If you have psql access to production (requires DB password):

```sql
-- Test 1: Check RLS is enabled
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('customer_data', 'loan_data', 'financial_statements')
ORDER BY tablename;

-- Expected: All should show rowsecurity = true

-- Test 2: List all policies on protected tables
SELECT schemaname, tablename, policyname, cmd
FROM pg_policies
WHERE schemaname IN ('public', 'monitoring', 'analytics')
ORDER BY tablename, policyname;

-- Expected: Should see policies like:
-- customer_data: service_role_write, authenticated_read, anon_read (or similar)
-- monitoring.kpi_values: service_role_insert_kpis, internal_authenticated_insert_kpis, authenticated_read_kpis

-- Test 3: Verify broadcast trigger has pinned search_path
SELECT proname, pronamespace::regnamespace, prosecdef, prosqlbody
FROM pg_proc
WHERE proname = 'loan_data_broadcast_trigger';

-- Expected: prosecdef should be true (security definer)
-- prosqlbody should reference specific schemas (not relying on search_path)
```

---

## Test 5: Performance Check (Indexes for Policies)

If your policies filter by user_id, tenant_id, or other columns, verify indexes exist:

```sql
-- Check indexes on columns used in RLS policies
SELECT
  schemaname,
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE schemaname IN ('public', 'monitoring', 'analytics')
  AND (indexdef LIKE '%user_id%'
    OR indexdef LIKE '%email%'
    OR indexdef LIKE '%tenant%')
ORDER BY tablename, indexname;

-- If policies use user_id but no index exists, consider:
-- CREATE INDEX idx_customer_data_user_id ON public.customer_data(user_id);
```

---

## Troubleshooting Common Issues

### Issue: Anonymous key still has access

**Possible causes:**

- RLS not enabled on table (check `rowsecurity = true` in pg_tables)
- Policy allows anonymous role explicitly
- Policies not applied correctly

**Fix:**

```sql
-- Re-enable RLS explicitly
ALTER TABLE public.customer_data ENABLE ROW LEVEL SECURITY;

-- Verify no overly permissive policies
SELECT * FROM pg_policies WHERE tablename = 'customer_data';
```

### Issue: Service role denied access

**Possible causes:**

- Policy restricts service_role explicitly
- Permission issue (user not superuser)

**Fix:**

```sql
-- Service role needs to bypass RLS or policies should allow it
-- Check if policy has: USING (auth.role() = 'service_role')
-- or
-- USING (true) -- allows all roles including service_role
```

### Issue: Authenticated users denied when they should have access

**Possible causes:**

- Email domain check failing (`auth.jwt()->>'email' LIKE '%@abaco.%'`)
- User's JWT token doesn't include email claim
- Case sensitivity in email matching

**Fix:**

```sql
-- Check current policies
SELECT policyname, cmd, qual FROM pg_policies
WHERE tablename = 'kpi_values';

-- Test with explicit email domain check
-- Ensure user's JWT has email: { "email": "user@abaco.domain" }
```

---

## Post-Deployment Monitoring

Add these checks to your observability dashboard:

1. **RLS Policy Violations**: Query Postgres logs for "violates row-level security policy" errors

   ```sql
   -- In application logs, watch for HTTP 403 errors from Supabase API
   SELECT * FROM postgres_logs
   WHERE message LIKE '%row-level security%'
   LIMIT 100;
   ```

2. **Migration Status**: Ensure migration table stays synchronized

   ```bash
   supabase migration list  # Run weekly
   ```

3. **Policy Performance**: Monitor slow queries on policy-filtered tables
   ```sql
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   WHERE query LIKE '%customer_data%' OR query LIKE '%kpi_values%'
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

---

## Approved By

- **Security Lead**: Verify RLS policies match intended access model
- **DevOps**: Confirm performance baselines unchanged
- **Backend Team**: Test application JWT integration

---

## Next Steps

1. Run Tests 1-3 above with your app's auth flow
2. Collect results in [DEPLOYMENT_LOG.md](DEPLOYMENT_LOG.md)
3. If all pass → **deployment verified**
4. If any fail → Post errors to `#security-incidents` channel

**Test Completion Date**: ******\_\_\_******  
**Verified By**: ******\_\_\_******  
**Notes**: ******\_\_\_******
