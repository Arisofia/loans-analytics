# Supabase RLS Hardening (2026-02-04)

**Status**: âœ… Implemented  
**Date**: 2026-02-04  
**Severity**: HIGH - Addresses 8 Supabase security alerts

---

## Overview

This document describes the Row Level Security (RLS) implementation for Loans Loans Analytics. All sensitive tables now have RLS enabled with least-privilege policies.

## Tables with RLS Enabled

### Public Schema

| Table                  | RLS Status | Policies | Purpose                                             |
| ---------------------- | ---------- | -------- | --------------------------------------------------- |
| `financial_statements` | âœ… Enabled | 2        | Financial data (internal only)                      |
| `payment_schedule`     | âœ… Enabled | 2        | Scheduled payments (customer view + service manage) |
| `real_payment`         | âœ… Enabled | 2        | Actual payments (customer view + service manage)    |
| `loan_data`            | âœ… Enabled | 2        | Loan records (customer view + service manage)       |
| `customer_data`        | âœ… Enabled | 4        | Customer PII (customer owns + service full)         |
| `historical_kpis`      | âœ… Enabled | 2        | Historical metrics (auth read + service manage)     |
| `kpi_timeseries_daily` | âœ… Enabled | 2        | Daily KPIs (auth read + service manage)             |
| `analytics_facts`      | âœ… Enabled | 2        | Analytics data (auth read + service manage)         |
| `data_lineage`         | âœ… Enabled | 2        | Data lineage (auth read + service manage)           |
| `lineage_columns`      | âœ… Enabled | 2        | Column lineage (auth read + service manage)         |
| `lineage_dependencies` | âœ… Enabled | 2        | Dependency tracking (auth read + service manage)    |
| `lineage_audit_log`    | âœ… Enabled | 2        | Audit logs (auth read + service manage)             |

### Monitoring Schema

| Table        | RLS Status | Policies | Purpose                                            |
| ------------ | ---------- | -------- | -------------------------------------------------- |
| `kpi_values` | âœ… Enabled | 3        | KPI metrics (service + internal insert, auth read) |

**Total**: 13 tables with RLS enabled, 31 policies defined

## Policy Design Principles

### 1. Customer Data Access

**Pattern**: Customers own their data

```sql
-- Read: Customer can see their own records
USING (auth.uid()::text = user_id::text OR auth.jwt()->>'role' = 'service_role')

-- Update: Customer can update their own non-critical fields
USING (auth.uid()::text = user_id::text)
WITH CHECK (auth.uid()::text = user_id::text AND pg_trigger_depth() = 0)

-- Insert/Delete: Only service_role
WITH CHECK (auth.jwt()->>'role' = 'service_role')
```

**Applies to**: `customer_data`, `loan_data` (via JOIN), `payment_schedule`, `real_payment`

### 2. Internal Analytics Data

**Pattern**: Authenticated read, service_role write

```sql
-- Read: All authenticated internal users
USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'))

-- Write: Only service_role (pipeline/backend)
USING (auth.jwt()->>'role' = 'service_role')
WITH CHECK (auth.jwt()->>'role' = 'service_role')
```

**Applies to**: `kpi_timeseries_daily`, `historical_kpis`, `analytics_facts`, `data_lineage`, `lineage_*`

### 3. Sensitive Financial Data

**Pattern**: Internal domain restriction + service_role

```sql
-- Read: Only internal authenticated users (@loans.* email)
USING (
  auth.jwt()->>'role' IN ('authenticated', 'service_role')
  AND auth.jwt()->>'email' LIKE '%@loans.%'
)

-- Write: Only service_role
USING (auth.jwt()->>'role' = 'service_role')
WITH CHECK (auth.jwt()->>'role' = 'service_role')
```

**Applies to**: `financial_statements`

### 4. KPI Insertion Control

**Pattern**: Service_role + internal authenticated (with audit trail)

```sql
-- Service role: Full access
USING (auth.jwt()->>'role' = 'service_role')
WITH CHECK (auth.jwt()->>'role' = 'service_role')

-- Internal users: Insert only (for manual corrections)
WITH CHECK (
  auth.jwt()->>'role' = 'authenticated'
  AND auth.jwt()->>'email' LIKE '%@loans.%'
)

-- All authenticated: Read-only
USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'))
```

**Applies to**: `monitoring.kpi_values`

**Audit Trail**: `created_by` column auto-populated via trigger

## Security Fixes Implemented

### 1. RLS Enablement (Migration: `20260204_enable_rls.sql`)

- Enabled RLS on 13 tables
- Verified all sensitive tables have `rowsecurity = true`
- Added audit comments to tables

### 2. Policy Definition (Migration: `20260204_rls_policies.sql`)

- Created 31 granular policies
- Implemented least-privilege access control
- Added domain restrictions for sensitive data

### 3. Function Security (Migration: `20260204_fix_broadcast_trigger.sql`)

**Vulnerability**: `loan_data_broadcast_trigger()` had mutable `search_path`

**Risk**: SQL injection via schema manipulation

**Fix**: Pinned `search_path` to `public, pg_temp`

```sql
ALTER FUNCTION public.loan_data_broadcast_trigger()
  SET search_path = public, pg_temp;
```

### 4. KPI Policy Hardening (Migration: `20260204_fix_kpi_values_policy.sql`)

**Vulnerability**: `allow_insert` policy with `WITH CHECK (true)` allowed unrestricted inserts

**Risk**: Data pollution, metric manipulation

**Fix**: Replaced with 3 granular policies:

- Service role: full access
- Internal authenticated: insert only
- All authenticated: read-only

**Added**: `created_by` audit column with auto-populate trigger

## Deployment

### Prerequisites

1. Supabase CLI installed: `npm install -g supabase`
2. Linked to project: `supabase link --project-ref sddviizcgheusvwqpthm`
3. Service role key available in `.env`

### Apply Migrations

```bash
# Method 1: Supabase CLI (recommended)
cd /path/to/loans-loans-analytics
supabase db push

# Method 2: Manual via SQL Editor
# 1. Go to https://supabase.com/dashboard/project/sddviizcgheusvwqpthm/sql
# 2. Copy contents of each migration file in order:
#    - db/migrations/20260204_enable_rls.sql
#    - db/migrations/20260204_rls_policies.sql
#    - db/migrations/20260204_fix_broadcast_trigger.sql
#    - db/migrations/20260204_fix_kpi_values_policy.sql
# 3. Click "Run" for each
```

### Verification

1. **Check RLS Status**:

   ```sql
   SELECT schemaname, tablename, rowsecurity
   FROM pg_tables
   WHERE schemaname IN ('public', 'monitoring')
   AND tablename IN (
     'financial_statements', 'payment_schedule', 'real_payment',
     'loan_data', 'customer_data', 'historical_kpis', 'kpi_values'
   )
   ORDER BY schemaname, tablename;
   ```

   **Expected**: All rows show `rowsecurity = true`

2. **List Policies**:

   ```sql
   SELECT schemaname, tablename, policyname, cmd
   FROM pg_policies
   WHERE schemaname IN ('public', 'monitoring')
   ORDER BY schemaname, tablename, policyname;
   ```

   **Expected**: 31 policies listed

3. **Verify Function Fix**:

   ```sql
   SELECT pg_get_functiondef(oid)
   FROM pg_proc
   WHERE proname = 'loan_data_broadcast_trigger'
   AND pronamespace = 'public'::regnamespace;
   ```

   **Expected**: Function definition contains `SET search_path = public, pg_temp`

4. **Test Access** (from application):

   ```javascript
   // As authenticated user - should succeed
   const { data, error } = await supabase
     .from("loan_data")
     .select("*")
     .eq("customer_id", currentUser.id);

   // As anon - should fail with RLS error
   const { data, error } = await supabase.from("customer_data").select("*");
   ```

## Troubleshooting

### Issue: "permission denied for table X"

**Cause**: RLS is blocking legitimate access

**Solution**: Check user's JWT claims match policy conditions

```sql
-- Inspect JWT in Supabase dashboard SQL editor:
SELECT auth.jwt();

-- Common issues:
-- - 'role' claim is 'anon' instead of 'authenticated'
-- - 'email' claim doesn't match @loans.* pattern
```

### Issue: "new row violates row-level security policy"

**Cause**: INSERT/UPDATE doesn't satisfy `WITH CHECK` condition

**Solution**: Verify service_role key is used for backend operations

```javascript
// Correct: Use service_role client for pipeline
import { createClient } from "@supabase/supabase-js";

const supabaseAdmin = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_ROLE_KEY, // Not anon key!
);
```

### Issue: Policies not applied

**Cause**: RLS enabled but no policies exist = all access denied

**Solution**: Verify policies were created:

```sql
SELECT COUNT(*) FROM pg_policies WHERE tablename = 'your_table';
```

## Best Practices

1. **Always use service_role for backend/pipeline**:
   - Never use anon key in backend code
   - Store service_role key as secret (not in git)

2. **Test policies with different user contexts**:
   - Anon user (should have minimal access)
   - Authenticated user (should see own data)
   - Service role (should have full access)

3. **Monitor RLS policy violations**:
   - Check Supabase logs for frequent policy violations
   - May indicate application bug or attack attempt

4. **Document policy changes**:
   - All policy changes via migrations (never manual SQL)
   - Add comments explaining business logic

5. **Regular security audits**:
   - Review policies quarterly
   - Check for tables without RLS
   - Verify function `search_path` settings

## Related Documentation

- [PostgreSQL RLS Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase RLS Guide](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Auth Helpers](https://supabase.com/docs/guides/auth/auth-helpers)

---

**Last Updated**: 2026-02-04  
**Next Review**: 2026-05-04  
**Owner**: Security Team
