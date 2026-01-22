-- Base Views for Abaco Financial Intelligence Platform
-- Version: 1.0

-- View: v_loan_month_snapshot
-- Builds a monthly snapshot for every loan with outstanding balance and DPD.
CREATE OR REPLACE VIEW v_loan_month_snapshot AS
WITH month_ends AS (
  SELECT (date_trunc('month', d) + interval '1 month - 1 day')::date AS month_end
  FROM generate_series('2024-01-01'::date, current_date, interval '1 month') AS d
),
principal_cum AS (
  SELECT
    loan_id,
    true_payment_date::date AS pay_date,
    SUM(true_principal_payment) OVER (PARTITION BY loan_id ORDER BY true_payment_date) AS cum_principal
  FROM real_payment
),
loan_month AS (
  SELECT
    m.month_end,
    l.loan_id,
    l.customer_id,
    l.disbursement_amount,
    l.interest_rate_apr,
    l.disbursement_date::date,
    (l.disbursement_amount - COALESCE(
      (SELECT pc.cum_principal
       FROM principal_cum pc
       WHERE pc.loan_id = l.loan_id AND pc.pay_date <= m.month_end
       ORDER BY pc.pay_date DESC LIMIT 1), 0)
    ) AS outstanding,
    l.days_past_due
  FROM month_ends m
  JOIN loan_data l ON m.month_end >= l.disbursement_date::date
)
SELECT * FROM loan_month;

-- View: v_customer_segments
-- Enriches customers with their segments and ticket bands.
CREATE OR REPLACE VIEW v_customer_segments AS
SELECT
  c.customer_id,
  c.cliente,
  COALESCE(NULLIF(c.segment, ''), 'Standard') AS segment,
  COALESCE(NULLIF(c.subcategoria_linea, ''), 'TBD') AS line_band,
  c.kam_id,
  c.first_disbursement_date
FROM customer_data c;
