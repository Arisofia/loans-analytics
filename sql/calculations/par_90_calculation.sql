-- PAR 90 Calculation
-- Portfolio at Risk (loans past due 90+ days)
-- Returns percentage of portfolio in arrears

SELECT
  CURRENT_TIMESTAMP() as calculation_timestamp,
  ROUND(SUM(CASE WHEN days_past_due >= 90 THEN balance ELSE 0 END) / SUM(balance) * 100, 2) as par_90_percentage,
  COUNT(CASE WHEN days_past_due >= 90 THEN 1 END) as loans_90_plus_count,
  COUNT(*) as total_loans,
  SUM(CASE WHEN days_past_due >= 90 THEN balance ELSE 0 END) as balance_90_plus,
  SUM(balance) as total_balance
FROM
  raw_layer.cascade_loans_raw
WHERE
  date_load = CURRENT_DATE()
