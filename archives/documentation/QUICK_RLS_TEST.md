# Quick RLS Test Execution Guide

## 1. Run the Automated Test Suite

```bash
# Install Supabase JS library (one-time)
npm install @supabase/supabase-js

# Set your API keys (from Supabase Dashboard > Settings > API)
export SUPABASE_URL="***REMOVED***"
export SUPABASE_ANON_KEY="REDACTED"  # From dashboard
export SUPABASE_SERVICE_ROLE_KEY="REDACTED"  # From dashboard (KEEP PRIVATE!)

# Run tests
node scripts/test-rls.js
```

**Expected Output:**

```
✅ Anonymous correctly blocked from reading customer_data (RLS policy enforced)
✅ Service role has full read access (returned N rows)
✅ Service role has full read access to loan_data (returned N rows)
✅ Service role has full read access to kpi_values (returned N rows)

Total Passed: 4
Total Failed: 0
✅ ALL TESTS PASSED! RLS is working correctly.
```

## 2. Manual SQL Verification (via psql or Supabase Dashboard)

### Check RLS is Enabled

```sql
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('customer_data', 'loan_data', 'financial_statements', 'payment_schedule', 'real_payment', 'historical_kpis')
ORDER BY tablename;
```

Expected: All show `rowsecurity = t` (true)

### List All RLS Policies

```sql
SELECT schemaname, tablename, policyname, cmd, qual
FROM pg_policies
WHERE schemaname IN ('public', 'analytics', 'monitoring')
ORDER BY tablename, policyname;
```

Expected: Multiple policies per table

- `service_role_write` — for INSERT/UPDATE/DELETE
- `authenticated_read` or similar — for SELECT
- `anon_read` (optional) — for public tables

### Check Broadcast Trigger Security

```sql
SELECT proname, prosecdef, prosqlbody
FROM pg_proc
WHERE proname = 'loan_data_broadcast_trigger';
```

Expected: `prosecdef = true` and `prosqlbody` should reference specific schemas (search_path pinned)

## 3. Test from Your Application

Once automated tests pass, verify your app's auth flows:

```javascript
// In your app
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

// Sign in user
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password',
})

// Try to read protected data (should work if RLS allows)
const { data: customers, error: fetchError } = await supabase
  .from('customer_data')
  .select('*')

// If RLS blocks, you'll see error:
// error.code = 'PGRST301'
// error.message = 'new row violates row-level security policy'
```

## 4. Monitor for RLS Violations

Check your application logs for RLS errors:

```bash
# In your app logs, watch for:
# - "new row violates row-level security policy"
# - HTTP 403 responses from Supabase API
# - Any permission denied errors on protected tables
```

If users report access errors:

1. Check user's auth JWT (has email? has correct role?)
2. Verify RLS policy uses correct role/email checks
3. Check if user is in correct email domain (@abaco.\* for internal)

---

## ✅ What Success Looks Like

- ✅ Anonymous key blocked (PGRST301 error)
- ✅ Service role has full access
- ✅ Authenticated users see filtered data
- ✅ All 13 tables have RLS enabled (rowsecurity=true)
- ✅ No permission errors in app logs
- ✅ Supabase Dashboard Security Advisor shows 0 alerts

---

## Next Steps

1. **Run automated test**: `node scripts/test-rls.js`
2. **Verify SQL**: Run check queries above in Supabase Dashboard
3. **Test application**: Sign in and confirm data access works
4. **Document results**: Fill in [DEPLOYMENT_LOG_2026_02_04.md](../docs/DEPLOYMENT_LOG_2026_02_04.md) sign-off section
5. **Monitor**: Watch logs for any RLS-related errors over next 24 hours

---

**Questions?** See [scripts/RLS_TEST_README.md](RLS_TEST_README.md) for detailed troubleshooting.
