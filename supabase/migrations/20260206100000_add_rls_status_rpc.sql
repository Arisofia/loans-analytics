-- Add RPC to check RLS status of critical tables
-- This allows the smoke test to verify RLS is enabled without direct DB access

CREATE OR REPLACE FUNCTION monitoring.check_rls_status()
RETURNS TABLE (schemaname text, tablename text, rowsecurity boolean)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT schemaname::text, tablename::text, rowsecurity
  FROM pg_tables
  WHERE (schemaname, tablename) IN (
    ('monitoring','kpi_values'),
    ('public','customer_data'),
    ('public','loan_data'),
    ('public','financial_statements')
  )
  ORDER BY schemaname, tablename;
$$;

-- Grant execute permission to service_role
GRANT EXECUTE ON FUNCTION monitoring.check_rls_status() TO service_role;
