# RLS & Supabase Diagnostics Tools

This directory contains safe diagnostic tools for investigating RLS (Row-Level Security) and Supabase connection issues **without exposing database credentials**.

## 📋 Available Tools

### 1. `create-readonly-user.sql`

**Purpose:** Create a read-only database user for safe diagnostics

**Usage:**

```bash
# Edit the script first to set username and password
vim scripts/create-readonly-user.sql

# Run with superuser credentials
psql $DATABASE_URL -f scripts/create-readonly-user.sql
```

**What it does:**

- Creates a role with LOGIN but no write permissions
- Grants SELECT on `public`, `monitoring`, `storage` schemas
- Safe to share connection string with diagnostics tools
- Can be revoked easily: `DROP ROLE abaco_readonly;`

---

### 2. `diagnose-rls.sql`

**Purpose:** Comprehensive RLS policy investigation (read-only queries)

**Usage:**

```bash
# Run and capture output
psql $DATABASE_URL -f scripts/diagnose-rls.sql > rls-diagnostics.txt

# Review the report
cat rls-diagnostics.txt
```

**What it reports:**

1. Database connection info
2. All RLS-enabled tables
3. Detailed policies per table
4. Indexes on policy columns (performance)
5. Database roles and permissions
6. Supabase-specific roles (`anon`, `authenticated`, `service_role`)
7. Custom functions used in RLS (e.g., `auth.uid()`)
8. Table row counts (no sensitive data)
9. Active connections
10. RLS bypass privileges
11. Key table policies (`fact_loans`, `kpi_timeseries_daily`)

**Safe to share:** Yes (no sensitive data exposed, only schema information)

---

### 3. `diagnose-supabase-keys.mjs`

**Purpose:** Validate Supabase connection strings and JWT keys

**Usage:**

```bash
# Run diagnostics
node scripts/diagnose-supabase-keys.mjs
```

**What it checks:**

1. **Environment variables:**
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (JWT validation)
   - `SUPABASE_SERVICE_ROLE_KEY` (JWT validation)
   - `DATABASE_URL` (connection string parsing)
   - `SUPABASE_DB_URL` (optional pooler URL)

2. **JWT validation:**
   - Token structure (header.payload.signature)
   - Role claim (`anon` vs `service_role`)
   - Expiration date
   - Issuer consistency

3. **Connection tests:**
   - Anonymous role database access
   - Service role RLS bypass
   - Health check queries

4. **Common issues:**
   - Missing SSL configuration
   - Mismatched project keys
   - Expired tokens
   - Wrong key types

**Safe to share:** Output masks secrets (shows only first/last 8 characters)

---

## 🛡️ Security Best Practices

### For Read-Only User

1. **Never grant superuser or write permissions**
2. **Exclude sensitive auth tables** (commented out in script)
3. **Revoke when done:**
   ```sql
   REVOKE ALL ON ALL TABLES IN SCHEMA public FROM abaco_readonly;
   DROP ROLE abaco_readonly;
   ```

### For Sharing Diagnostics

1. **Remove any connection strings from output**
2. **Redact IP addresses if sharing publicly**
3. **Review table row counts** (ensure no PII leaked)
4. **Mask any email addresses or usernames in role names**

---

## 🔍 Troubleshooting Workflow

### Issue: "No suitable key or wrong key type"

**Steps:**

1. Run `node scripts/diagnose-supabase-keys.mjs`
2. Check JWT validation results
3. Verify `role` claim matches expected value:
   - `SUPABASE_ANON_KEY` → role: `anon`
   - `SUPABASE_SERVICE_ROLE_KEY` → role: `service_role`
4. If JWT is invalid, regenerate in **Supabase Dashboard → Settings → API**

### Issue: RLS blocking valid queries

**Steps:**

1. Run `psql $DATABASE_URL -f scripts/diagnose-rls.sql > report.txt`
2. Check section **3. RLS POLICIES** for the affected table
3. Verify the `using_expression` matches your query conditions
4. Check section **5. INDEXES** to ensure RLS columns are indexed
5. Review section **12. RLS BYPASS** to see if your role has bypass privileges

### Issue: Connection timeout or "permission denied"

**Steps:**

1. Run `node scripts/diagnose-supabase-keys.mjs`
2. Check **DATABASE_URL** SSL configuration
3. Verify **SUPABASE_URL** format: `https://<project-ref>.supabase.co`
4. Test with service role key if anon key fails

---

## 📊 Example Outputs

### diagnose-rls.sql

```
=== 2. RLS-ENABLED TABLES ===
 schemaname |        tablename       | rls_status | force_rls
------------+------------------------+------------+------------
 public     | fact_loans             | ✓ ENABLED  | ✗ NOT FORCED
 public     | kpi_timeseries_daily   | ✓ ENABLED  | ✗ NOT FORCED
 monitoring | kpi_values             | ✓ ENABLED  | ✓ FORCED

=== 3. RLS POLICIES ===
 schemaname | tablename  | policyname    | policy_type | operation | applies_to_roles | using_clause
------------+------------+---------------+-------------+-----------+------------------+--------------
 public     | fact_loans | anon_readonly | PERMISSIVE  | SELECT    | anon             | (tenant_id = current_setting('app.tenant_id'::text))
 public     | fact_loans | service_all   | PERMISSIVE  | ALL       | service_role     | TRUE
```

### diagnose-supabase-keys.mjs

```
=== 1. ENVIRONMENT VARIABLES ===

SUPABASE_URL:
  ✓ Set (51 chars): https://...supabase.co

SUPABASE_ANON_KEY:
  ✓ Set (256 chars): eyJhbGci...9KTdFLjw
  ✓ Valid JWT token
  Role: anon
  Issuer: https://abcdef123456.supabase.co/auth/v1
  Expires: 2030-01-01T00:00:00.000Z ✓

=== 2. SUPABASE CLIENT CONNECTION TEST ===
✓ Client created successfully
✓ Database connection successful
✓ RLS is working (anonymous blocked as expected)
```

---

## 🚀 Quick Start

**Scenario:** Investigating RLS issue with `fact_loans` table

```bash
# Step 1: Validate environment and keys
node scripts/diagnose-supabase-keys.mjs

# Step 2: Generate RLS report
psql $DATABASE_URL -f scripts/diagnose-rls.sql > rls-report.txt

# Step 3: Review the report
grep -A 10 "fact_loans" rls-report.txt

# Step 4: Create read-only user if needed for deeper investigation
# Edit create-readonly-user.sql first
psql $DATABASE_URL -f scripts/create-readonly-user.sql
```

---

## 📮 Sharing Diagnostics Safely

When requesting help, run these commands and share the **sanitized** output:

```bash
# Generate reports
node scripts/diagnose-supabase-keys.mjs > supabase-keys-report.txt
psql $DATABASE_URL -f scripts/diagnose-rls.sql > rls-policies-report.txt

# Sanitize (remove secrets)
sed -i 's/postgres:\/\/.*@/postgres:\/\/REDACTED@/g' *.txt
sed -i 's/eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*/JWT_REDACTED/g' *.txt

# Share the sanitized files
cat supabase-keys-report.txt
cat rls-policies-report.txt
```

---

## 🔐 Security Notes

- **Never commit `.env` files** with real credentials
- **Use `.env.local` for secrets** (gitignored)
- **Rotate keys after sharing diagnostics** (even read-only users)
- **Monitor audit logs** in Supabase Dashboard after creating users
- **Prefer service accounts** over personal credentials for diagnostics

---

## 📚 Additional Resources

- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)
- [PostgreSQL Policy Documentation](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Supabase API Keys Guide](https://supabase.com/docs/guides/api/api-keys)
