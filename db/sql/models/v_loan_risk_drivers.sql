-- v_loan_risk_drivers
-- Surface risk drivers by product/segment for business reviews
CREATE OR REPLACE VIEW analytics.v_loan_risk_drivers AS
SELECT
  product_id,
  COUNT(*) AS loan_count,
  SUM(balance) AS total_balance,
  SUM(CASE WHEN days_past_due >= 30 THEN balance ELSE 0 END) AS par_30_balance,
  SUM(CASE WHEN days_past_due >= 90 THEN balance ELSE 0 END) AS par_90_balance,
  AVG(days_past_due) AS avg_days_past_due,
  MAX(days_past_due) AS max_days_past_due,
  CASE WHEN COUNT(*) = 0 THEN 0 ELSE (SUM(CASE WHEN days_past_due >= 30 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) END AS pct_roll_30,
  CASE WHEN COUNT(*) = 0 THEN 0 ELSE (SUM(CASE WHEN days_past_due >= 90 THEN 1 ELSE 0 END) * 100.0) / COUNT(*) END AS pct_roll_90
FROM analytics.v_loans_overview
GROUP BY product_id;
