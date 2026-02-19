-- ================================================================
-- CREATE READ-ONLY DATABASE USER FOR SAFE DIAGNOSTICS
-- ================================================================
-- Purpose: Create a restricted user for investigating RLS policies
--          without exposing superuser credentials
-- 
-- Usage: 
--   1. Connect as postgres superuser to your database
--   2. Edit the username and password below
--   3. Run: psql <connection_string> -f scripts/create-readonly-user.sql
-- ================================================================

-- Configuration (EDIT THESE VALUES)
\set readonly_user 'abaco_readonly'
\set readonly_password 'CHANGE_THIS_STRONG_PASSWORD'

-- Step 1: Create the read-only role
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = :'readonly_user') THEN
        EXECUTE format('CREATE ROLE %I WITH LOGIN PASSWORD %L', :'readonly_user', :'readonly_password');
        RAISE NOTICE 'Created role: %', :'readonly_user';
    ELSE
        RAISE NOTICE 'Role % already exists', :'readonly_user';
    END IF;
END
$$;

-- Step 2: Grant database connection
GRANT CONNECT ON DATABASE postgres TO :readonly_user;

-- Step 3: Grant schema access (public schema)
GRANT USAGE ON SCHEMA public TO :readonly_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :readonly_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO :readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO :readonly_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO :readonly_user;

-- Step 4: Grant monitoring schema access (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_namespace WHERE nspname = 'monitoring') THEN
        GRANT USAGE ON SCHEMA monitoring TO :readonly_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO :readonly_user;
        ALTER DEFAULT PRIVILEGES IN SCHEMA monitoring GRANT SELECT ON TABLES TO :readonly_user;
        RAISE NOTICE 'Granted access to monitoring schema';
    END IF;
END
$$;

-- Step 5: Grant auth schema access (Supabase auth tables, if needed)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_namespace WHERE nspname = 'auth') THEN
        GRANT USAGE ON SCHEMA auth TO :readonly_user;
        -- Be careful with auth tables - only grant if truly needed for diagnostics
        -- GRANT SELECT ON auth.users TO :readonly_user; -- Uncomment if needed
        RAISE NOTICE 'Granted auth schema usage (tables restricted by default)';
    END IF;
END
$$;

-- Step 6: Grant storage schema access (if needed)
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_namespace WHERE nspname = 'storage') THEN
        GRANT USAGE ON SCHEMA storage TO :readonly_user;
        GRANT SELECT ON ALL TABLES IN SCHEMA storage TO :readonly_user;
        RAISE NOTICE 'Granted access to storage schema';
    END IF;
END
$$;

-- Step 7: Verify the user was created successfully
\echo '\n=== Read-Only User Created ==='
\echo 'Username: :readonly_user'
\echo 'Permissions: SELECT on public, monitoring, storage schemas'
\echo '\nConnection string format:'
\echo 'postgresql://:readonly_user::readonly_password@<host>:<port>/<database>'
\echo '\n=== Security Notes ==='
\echo '- This user has READ-ONLY access'
\echo '- No INSERT, UPDATE, DELETE, or DDL permissions'
\echo '- Safe for sharing with diagnostics/monitoring tools'
\echo '- Revoke access when diagnostics complete: DROP ROLE :readonly_user;'

-- Display granted permissions
SELECT 
    grantee,
    table_schema,
    privilege_type,
    COUNT(*) as table_count
FROM information_schema.role_table_grants 
WHERE grantee = :'readonly_user'
GROUP BY grantee, table_schema, privilege_type
ORDER BY table_schema, privilege_type;
