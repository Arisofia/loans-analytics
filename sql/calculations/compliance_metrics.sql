-- Compliance Metrics Calculation
-- Regulatory compliance checks and metrics

SELECT
  CURRENT_TIMESTAMP() as calculation_timestamp,
  CASE
    WHEN par_90_pct > 5.0 THEN 'BREACH'
    WHEN par_90_pct > 3.0 THEN 'WARNING'
    ELSE 'COMPLIANT'
  END as compliance_status,
  ROUND(par_90_pct, 2) as par_90_pct,
  portfolio_balance,
  total_loans,
  CASE WHEN par_90_pct > 5.0 THEN 1 ELSE 0 END as is_breach
FROM (
  SELECT
    ROUND(SUM(CASE WHEN days_past_due >= 90 THEN balance ELSE 0 END) / SUM(balance) * 100, 2) as par_90_pct,
    SUM(balance) as portfolio_balance,
    COUNT(*) as total_loans
  FROM
    raw_layer.cascade_loans_raw
  WHERE
    date_load = CURRENT_DATE()
) compliance_subquery
