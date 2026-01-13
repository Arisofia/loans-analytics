-- PAR 30 Calculation
-- Portfolio at Risk (loans past due 30+ days)
-- Returns percentage of portfolio in arrears

SELECT
  CURRENT_TIMESTAMP() as calculation_timestamp,
  ROUND(SUM(CASE WHEN days_past_due >= 30 THEN balance ELSE 0 END) / SUM(balance) * 100, 2) as par_30_percentage,
  COUNT(CASE WHEN days_past_due >= 30 THEN 1 END) as loans_30_plus_count,
  COUNT(*) as total_loans,
  SUM(CASE WHEN days_past_due >= 30 THEN balance ELSE 0 END) as balance_30_plus,
  SUM(balance) as total_balance
FROM
  raw_layer.cascade_loans_raw
WHERE
  date_load = CURRENT_DATE()
