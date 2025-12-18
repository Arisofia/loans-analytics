-- Collection Rate Calculation
-- Monthly collection rate as percentage of receivables

SELECT
  CURRENT_TIMESTAMP() as calculation_timestamp,
  ROUND(total_collections / total_receivables * 100, 2) as collection_rate_pct,
  total_collections,
  total_receivables,
  COUNT(*) as records_analyzed
FROM (
  SELECT
    SUM(CASE WHEN status = 'Collected' THEN balance ELSE 0 END) as total_collections,
    SUM(balance) as total_receivables
  FROM
    raw_layer.cascade_loans_raw
  WHERE
    date_load = CURRENT_DATE()
) subquery
