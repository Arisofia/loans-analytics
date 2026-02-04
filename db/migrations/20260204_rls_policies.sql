-- Migration: Define RLS policies for sensitive tables
-- Date: 2026-02-04
-- Purpose: Implement secure access control policies for fintech data
-- Related: SECURITY_STATUS_2026_02_04.md, docs/security/SUPABASE_RLS_HARDENING.md

BEGIN;

-- ============================================================================
-- CUSTOMER DATA POLICIES
-- ============================================================================

-- Customers can only see their own data
CREATE POLICY "Customers read own data" ON public.customer_data
  FOR SELECT
  USING (
    auth.uid()::text = user_id::text
    OR auth.jwt()->>'role' = 'service_role'
  );

-- Customers can update their own non-critical fields
CREATE POLICY "Customers update own data" ON public.customer_data
  FOR UPDATE
  USING (auth.uid()::text = user_id::text)
  WITH CHECK (
    auth.uid()::text = user_id::text
    AND pg_trigger_depth() = 0  -- Prevent recursive updates
  );

-- Only service role can insert new customers (via backend)
CREATE POLICY "Service role insert customers" ON public.customer_data
  FOR INSERT
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Only service role can delete (for GDPR/data retention)
CREATE POLICY "Service role delete customers" ON public.customer_data
  FOR DELETE
  USING (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- LOAN DATA POLICIES
-- ============================================================================

-- Customers can view loans where they are the borrower
CREATE POLICY "Customers read own loans" ON public.loan_data
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.customer_data cd
      WHERE cd.id = loan_data.customer_id
      AND cd.user_id::text = auth.uid()::text
    )
    OR auth.jwt()->>'role' = 'service_role'
  );

-- Only service role can modify loans (business logic enforced in backend)
CREATE POLICY "Service role manage loans" ON public.loan_data
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- PAYMENT POLICIES
-- ============================================================================

-- Customers can view their payment schedules
CREATE POLICY "Customers read own payment schedules" ON public.payment_schedule
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.loan_data ld
      JOIN public.customer_data cd ON cd.id = ld.customer_id
      WHERE ld.id = payment_schedule.loan_id
      AND cd.user_id::text = auth.uid()::text
    )
    OR auth.jwt()->>'role' = 'service_role'
  );

-- Customers can view their actual payments
CREATE POLICY "Customers read own payments" ON public.real_payment
  FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.loan_data ld
      JOIN public.customer_data cd ON cd.id = ld.customer_id
      WHERE ld.id = real_payment.loan_id
      AND cd.user_id::text = auth.uid()::text
    )
    OR auth.jwt()->>'role' = 'service_role'
  );

-- Only service role can record payments
CREATE POLICY "Service role manage payments" ON public.real_payment
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- FINANCIAL STATEMENTS POLICIES
-- ============================================================================

-- Only authenticated internal users can view financial statements
CREATE POLICY "Authenticated users read financial statements" ON public.financial_statements
  FOR SELECT
  USING (
    auth.jwt()->>'role' IN ('authenticated', 'service_role')
    AND auth.jwt()->>'email' LIKE '%@abaco.%'  -- Internal domain only
  );

-- Only service role can manage financial statements
CREATE POLICY "Service role manage financial statements" ON public.financial_statements
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- KPI AND ANALYTICS POLICIES
-- ============================================================================

-- KPI timeseries: read-only for authenticated, write for service role
CREATE POLICY "Authenticated users read KPIs" ON public.kpi_timeseries_daily
  FOR SELECT
  USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'));

CREATE POLICY "Service role manage KPIs" ON public.kpi_timeseries_daily
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Historical KPIs: same pattern
CREATE POLICY "Authenticated users read historical KPIs" ON public.historical_kpis
  FOR SELECT
  USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'));

CREATE POLICY "Service role manage historical KPIs" ON public.historical_kpis
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Analytics facts: read-only for authenticated
CREATE POLICY "Authenticated users read analytics facts" ON public.analytics_facts
  FOR SELECT
  USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'));

CREATE POLICY "Service role manage analytics facts" ON public.analytics_facts
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- ============================================================================
-- DATA LINEAGE POLICIES
-- ============================================================================

-- Lineage tables: read-only for authenticated, write for service role
CREATE POLICY "Authenticated users read lineage" ON public.data_lineage
  FOR SELECT
  USING (auth.jwt()->>'role' IN ('authenticated', 'service_role'));

CREATE POLICY "Service role manage lineage" ON public.data_lineage
  FOR ALL
  USING (auth.jwt()->>'role' = 'service_role')
  WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Apply same pattern to related lineage tables
DO $$
DECLARE
    lineage_table text;
BEGIN
    FOR lineage_table IN 
        SELECT unnest(ARRAY['lineage_columns', 'lineage_dependencies', 'lineage_audit_log'])
    LOOP
        EXECUTE format(
            'CREATE POLICY "Authenticated users read %s" ON public.%I FOR SELECT USING (auth.jwt()->>''role'' IN (''authenticated'', ''service_role''))',
            lineage_table, lineage_table
        );
        EXECUTE format(
            'CREATE POLICY "Service role manage %s" ON public.%I FOR ALL USING (auth.jwt()->>''role'' = ''service_role'') WITH CHECK (auth.jwt()->>''role'' = ''service_role'')',
            lineage_table, lineage_table
        );
    END LOOP;
END $$;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- List all policies:
-- SELECT schemaname, tablename, policyname, cmd, roles, qual, with_check
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- ORDER BY tablename, policyname;

-- Count policies per table:
-- SELECT tablename, COUNT(*) as policy_count
-- FROM pg_policies
-- WHERE schemaname = 'public'
-- GROUP BY tablename
-- ORDER BY tablename;
