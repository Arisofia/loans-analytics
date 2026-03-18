-- Grant monitoring schema access to service_role and authenticated users
-- Date: 2026-02-05
-- Purpose: Enable cross-schema access for RLS tests and monitoring
-- Related: #RLS-DIAGNOSTICS

BEGIN;

-- Grant USAGE on monitoring schema to service_role (allows table enumeration)
GRANT USAGE ON SCHEMA "monitoring" TO "service_role";

-- Grant SELECT on monitoring tables to service_role
GRANT SELECT ON ALL TABLES IN SCHEMA "monitoring" TO "service_role";

-- Grant SELECT on monitoring tables to authenticated users
GRANT SELECT ON ALL TABLES IN SCHEMA "monitoring" TO "authenticated";

-- Set default privileges for future tables (service_role)
ALTER DEFAULT PRIVILEGES IN SCHEMA "monitoring"
  GRANT SELECT ON TABLES TO "service_role";

-- Set default privileges for future tables (authenticated)
ALTER DEFAULT PRIVILEGES IN SCHEMA "monitoring"
  GRANT SELECT ON TABLES TO "authenticated";

COMMIT;
