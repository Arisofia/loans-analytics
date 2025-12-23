-- v_loans_overview
-- Provides canonical loan-level snapshot for analytics pipelines
CREATE OR REPLACE VIEW analytics.v_loans_overview AS
SELECT
  loan_id,
  origination_date,
  maturity_date,
  CAST(balance AS numeric) AS balance,
  days_past_due,
  product_id,
  borrower_id,
  data_ingest_ts
FROM data_warehouse.fact_loans
WHERE balance IS NOT NULL;
