-- ================================================================
-- RLS DIAGNOSTIC QUERIES - COMPREHENSIVE INVESTIGATION
-- ================================================================
-- Purpose: Collect all RLS-related schema information without
--          exposing sensitive data
--
-- Usage: psql <connection_string> -f scripts/diagnose-rls.sql > rls-diagnostics.txt
-- ================================================================

\echo '╔════════════════════════════════════════════════════════════════╗'
\echo '║                RLS DIAGNOSTICS - COMPREHENSIVE REPORT            ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo ''

-- ================================================================
-- 1. DATABASE CONNECTION INFO
-- ================================================================
\echo '\n=== 1. DATABASE CONNECTION INFO ==='
SELECT 
    current_database() as database_name,
    current_user as connected_as,
    inet_server_addr() as server_ip,
    inet_server_port() as server_port,
    version() as postgres_version;

-- ================================================================
-- 2. RLS-ENABLED TABLES
-- ================================================================
\echo '\n=== 2. RLS-ENABLED TABLES ==='
\echo 'Tables with Row-Level Security enabled:\n'

SELECT 
    schemaname,
    tablename,
    CASE 
        WHEN relrowsecurity THEN '✓ ENABLED'
        ELSE '✗ DISABLED'
    END as rls_status,
    CASE 
        WHEN relforcerowsecurity THEN '✓ FORCED'
        ELSE '✗ NOT FORCED'
    END as force_rls
FROM pg_catalog.pg_tables t 
JOIN pg_catalog.pg_class c ON t.tablename = c.relname 
JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace AND n.nspname = t.schemaname
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename;

-- ================================================================
-- 3. ALL RLS POLICIES (DETAILED)
-- ================================================================
\echo '\n=== 3. RLS POLICIES (ALL TABLES) ==='

SELECT 
    schemaname,
    tablename,
    policyname,
    CASE permissive
        WHEN TRUE THEN 'PERMISSIVE'
        WHEN FALSE THEN 'RESTRICTIVE'
    END as policy_type,
    CASE cmd
        WHEN 'r' THEN 'SELECT'
        WHEN 'a' THEN 'INSERT'
        WHEN 'w' THEN 'UPDATE'
        WHEN 'd' THEN 'DELETE'
        WHEN '*' THEN 'ALL'
    END as operation,
    COALESCE(
        ARRAY_TO_STRING(roles, ', '),
        'PUBLIC'
    ) as applies_to_roles,
    CASE 
        WHEN qual IS NOT NULL THEN 
            SUBSTRING(qual::text, 1, 80) || CASE WHEN LENGTH(qual::text) > 80 THEN '...' ELSE '' END
        ELSE 'NO USING CLAUSE'
    END as using_clause,
    CASE 
        WHEN with_check IS NOT NULL THEN 
            SUBSTRING(with_check::text, 1, 80) || CASE WHEN LENGTH(with_check::text) > 80 THEN '...' ELSE '' END
        ELSE 'NO WITH CHECK CLAUSE'
    END as with_check_clause
FROM pg_policies
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY schemaname, tablename, policyname;

-- ================================================================
-- 4. POLICIES FOR SPECIFIC KEY TABLES
-- ================================================================
\echo '\n=== 4. KEY TABLE POLICIES (DETAILED) ==='

-- fact_loans policies
\echo '\n--- fact_loans policies:'
SELECT 
    policyname,
    CASE cmd WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT' WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE' WHEN '*' THEN 'ALL' END as cmd,
    roles,
    qual::text as using_expression,
    with_check::text as with_check_expression
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'fact_loans';

-- kpi_timeseries_daily policies
\echo '\n--- kpi_timeseries_daily policies:'
SELECT 
    policyname,
    CASE cmd WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT' WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE' WHEN '*' THEN 'ALL' END as cmd,
    roles,
    qual::text as using_expression,
    with_check::text as with_check_expression
FROM pg_policies 
WHERE schemaname = 'public' AND tablename = 'kpi_timeseries_daily';

-- monitoring.kpi_values policies (if exists)
\echo '\n--- monitoring.kpi_values policies (if exists):'
SELECT 
    policyname,
    CASE cmd WHEN 'r' THEN 'SELECT' WHEN 'a' THEN 'INSERT' WHEN 'w' THEN 'UPDATE' WHEN 'd' THEN 'DELETE' WHEN '*' THEN 'ALL' END as cmd,
    roles,
    qual::text as using_expression,
    with_check::text as with_check_expression
FROM pg_policies 
WHERE schemaname = 'monitoring' AND tablename = 'kpi_values';

-- ================================================================
-- 5. INDEXES ON RLS POLICY COLUMNS
-- ================================================================
\echo '\n=== 5. INDEXES ON RLS POLICY COLUMNS ==='
\echo 'Indexes that may affect RLS policy performance:\n'

SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname IN ('public', 'monitoring')
  AND (
    indexdef ILIKE '%tenant_id%' OR 
    indexdef ILIKE '%user_id%' OR
    indexdef ILIKE '%auth.uid()%' OR
    indexdef ILIKE '%auth.role()%'
  )
ORDER BY schemaname, tablename, indexname;

-- ================================================================
-- 6. DATABASE ROLES AND PERMISSIONS
-- ================================================================
\echo '\n=== 6. DATABASE ROLES ==='

SELECT 
    rolname,
    CASE WHEN rolsuper THEN '✓' ELSE '✗' END as superuser,
    CASE WHEN rolinherit THEN '✓' ELSE '✗' END as inherit,
    CASE WHEN rolcreaterole THEN '✓' ELSE '✗' END as create_role,
    CASE WHEN rolcreatedb THEN '✓' ELSE '✗' END as create_db,
    CASE WHEN rolcanlogin THEN '✓' ELSE '✗' END as can_login,
    CASE WHEN rolreplication THEN '✓' ELSE '✗' END as replication,
    CASE WHEN rolconnlimit = -1 THEN 'unlimited' ELSE rolconnlimit::text END as conn_limit
FROM pg_roles
WHERE rolname NOT LIKE 'pg_%'
ORDER BY rolname;

-- ================================================================
-- 7. TABLE GRANTS (PERMISSIONS)
-- ================================================================
\echo '\n=== 7. TABLE GRANTS (PUBLIC SCHEMA) ==='

SELECT 
    grantee,
    table_name,
    STRING_AGG(privilege_type, ', ' ORDER BY privilege_type) as privileges
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND grantee NOT LIKE 'pg_%'
GROUP BY grantee, table_name
ORDER BY grantee, table_name;

-- ================================================================
-- 8. SUPABASE-SPECIFIC ROLES (IF APPLICABLE)
-- ================================================================
\echo '\n=== 8. SUPABASE ROLES (IF APPLICABLE) ==='

SELECT 
    rolname,
    CASE WHEN rolsuper THEN '✓' ELSE '✗' END as superuser,
    CASE WHEN rolcanlogin THEN '✓' ELSE '✗' END as can_login
FROM pg_roles
WHERE rolname IN ('anon', 'authenticated', 'service_role', 'supabase_admin', 'postgres', 'authenticator')
ORDER BY 
    CASE rolname
        WHEN 'postgres' THEN 1
        WHEN 'supabase_admin' THEN 2
        WHEN 'authenticator' THEN 3
        WHEN 'service_role' THEN 4
        WHEN 'authenticated' THEN 5
        WHEN 'anon' THEN 6
    END;

-- ================================================================
-- 9. FUNCTION DEFINITIONS USED IN RLS POLICIES
-- ================================================================
\echo '\n=== 9. CUSTOM FUNCTIONS USED IN RLS ==='
\echo 'Functions like auth.uid(), auth.role(), etc.:\n'

SELECT 
    n.nspname as schema,
    p.proname as function_name,
    pg_get_function_arguments(p.oid) as arguments,
    pg_get_functiondef(p.oid) as definition
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname IN ('auth', 'public')
  AND (
    p.proname ILIKE '%uid%' OR 
    p.proname ILIKE '%role%' OR
    p.proname ILIKE '%jwt%'
  )
ORDER BY n.nspname, p.proname;

-- ================================================================
-- 10. TABLE ROW COUNTS (SANITIZED)
-- ================================================================
\echo '\n=== 10. TABLE ROW COUNTS (NO SENSITIVE DATA) ==='

SELECT 
    schemaname,
    tablename,
    n_live_tup as approximate_rows,
    n_dead_tup as dead_rows,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE schemaname IN ('public', 'monitoring')
ORDER BY n_live_tup DESC;

-- ================================================================
-- 11. ACTIVE CONNECTIONS AND CURRENT QUERIES
-- ================================================================
\echo '\n=== 11. ACTIVE DATABASE CONNECTIONS ==='

SELECT 
    datname as database,
    usename as user,
    application_name,
    client_addr,
    state,
    COUNT(*) as connection_count
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY datname, usename, application_name, client_addr, state
ORDER BY connection_count DESC;

-- ================================================================
-- 12. RLS BYPASS CHECKS
-- ================================================================
\echo '\n=== 12. RLS BYPASS PRIVILEGES ==='
\echo 'Users who can bypass RLS (dangerous if misconfigured):\n'

SELECT 
    r.rolname,
    CASE WHEN r.rolbypassrls THEN '⚠️  CAN BYPASS RLS' ELSE '✓ Cannot bypass' END as bypass_status
FROM pg_roles r
WHERE r.rolname NOT LIKE 'pg_%'
ORDER BY r.rolbypassrls DESC, r.rolname;

-- ================================================================
-- REPORT COMPLETE
-- ================================================================
\echo '\n╔════════════════════════════════════════════════════════════════╗'
\echo '║                   DIAGNOSTICS COMPLETE                           ║'
\echo '╚════════════════════════════════════════════════════════════════╝'
\echo '\nSave this output and share (sanitized) for analysis.'
\echo 'To export: psql <connection> -f diagnose-rls.sql > rls-report.txt'
