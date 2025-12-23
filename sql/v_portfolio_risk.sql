-- BigQuery Portfolio Risk Model
-- Implements PAR_90 and Portfolio Health calculations
-- Source: Cascade Debt loan-level data
-- Version: 1.0 (Fintech Factory Agentic Ecosystem)

CREATE OR REPLACE TABLE `{project_id}.{dataset_id}.v_portfolio_risk` AS
WITH base_loans AS (
  -- Extract base loan portfolio from cascade data
  SELECT
    loan_id,
    client_id,
    disbursement_date,
    original_balance,
    current_balance,
    interest_rate,
    CASE
      WHEN EXTRACT(DAY FROM CURRENT_DATE()) - EXTRACT(DAY FROM last_payment_date) > 90 THEN '90+'
      WHEN EXTRACT(DAY FROM CURRENT_DATE()) - EXTRACT(DAY FROM last_payment_date) > 60 THEN '60-89'
      WHEN EXTRACT(DAY FROM CURRENT_DATE()) - EXTRACT(DAY FROM last_payment_date) > 30 THEN '30-59'
      ELSE 'Current'
    END AS delinquency_bucket,
    last_payment_date,
    total_paid_to_date,
    total_collections_30_days,
    CURRENT_TIMESTAMP() AS _processed_at,
    '1.0' AS _data_version
  FROM `{project_id}.{dataset_id}.cascade_loans`
  WHERE date_load = CURRENT_DATE()
),

par_90_calculation AS (
  -- Calculate PAR_90: Sum of balances for loans >90 days delinquent
  SELECT
    SUM(current_balance) AS par_90_balance,
    COUNT(DISTINCT loan_id) AS par_90_loan_count,
    SUM(original_balance) AS total_receivables,
    ROUND(SUM(current_balance) / SUM(original_balance) * 100, 2) AS par_90_pct
  FROM base_loans
  WHERE delinquency_bucket = '90+'
),

delinquency_summary AS (
  -- Delinquency bucket summary
  SELECT
    delinquency_bucket,
    COUNT(DISTINCT loan_id) AS loan_count,
    SUM(balance) AS bucket_balance
  FROM base_loans
  GROUP BY delinquency_bucket
),

collection_rate AS (
  -- Calculate collection rate (last 30 days)
  SELECT
    SUM(total_collections_30_days) AS collections_30d,
    SUM(current_balance) AS receivables_outstanding,
    ROUND(SUM(total_collections_30_days) / NULLIF(SUM(current_balance), 0) * 100, 2) AS collection_rate_pct
  FROM base_loans
),

portfolio_metrics AS (
  -- Aggregate portfolio health metrics
  SELECT
    CURRENT_TIMESTAMP() AS calculated_at,
    (SELECT par_90_pct FROM par_90_calculation) AS par_90_pct,
    (SELECT par_90_balance FROM par_90_calculation) AS par_90_balance,
    (SELECT par_90_loan_count FROM par_90_calculation) AS par_90_loan_count,
    (SELECT total_receivables FROM par_90_calculation) AS total_receivables,
    (SELECT SUM(loan_count) FROM delinquency_summary) AS total_loan_count,
    (SELECT collections_30d FROM collection_rate) AS collections_30d,
    (SELECT collection_rate_pct FROM collection_rate) AS collection_rate_pct,
    (SELECT COUNT(DISTINCT loan_id) FROM base_loans) AS active_loans
)

SELECT
  pm.*,
  CASE
    WHEN pm.par_90_pct > 5.0 THEN 'CRITICAL'
    WHEN pm.par_90_pct > 3.0 THEN 'WARNING'
    WHEN pm.par_90_pct > 1.0 THEN 'CAUTION'
    ELSE 'HEALTHY'
  END AS portfolio_health_status,
  ROUND((100 - COALESCE(pm.par_90_pct, 0)) * 0.6 + COALESCE(pm.collection_rate_pct, 0) * 0.4, 2) AS health_score,
  GENERATE_UUID() AS run_id,
  CURRENT_TIMESTAMP() AS _processed_at,
  '1.0' AS _data_version
FROM portfolio_metrics pm;
