-- =====================================================================
-- Abaco Analytics – Base + KPI Views
-- Schema: analytics
-- =====================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS analytics;

SET search_path TO public, analytics;

-- ---------------------------------------------------------------------
-- 1. CUSTOMER SEGMENT VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.customer_segment AS
WITH src AS (
    SELECT
        COALESCE(c.customer_id::text, '') AS customer_id,
        LOWER(COALESCE(c.segment, '')) AS segment_raw,
        COALESCE(c.subcategoria_linea, '') AS subcategoria_linea,
        COALESCE(c.kam_id, '') AS kam_id,
        COALESCE(c.industry, '') AS industry_code
    FROM customer_data c
)
SELECT
    customer_id,
    segment_raw AS segment_source,
    subcategoria_linea,
    kam_id,
    industry_code,
    CASE
        WHEN segment_raw = 'gob' THEN 'Gob'
        ELSE 'Private'
    END AS sector_segment,
    CASE
        WHEN segment_raw = 'oc' THEN 'OC'
        WHEN segment_raw = 'top' THEN 'Top'
        WHEN subcategoria_linea ILIKE '%ccf%' THEN 'CCF'
        WHEN subcategoria_linea ILIKE '%dte%' THEN 'DTE'
        WHEN segment_raw = 'nimal' THEN 'Nimal'
        ELSE 'Other'
    END AS business_segment
FROM src;

-- ---------------------------------------------------------------------
-- 2. LOAN_MONTH VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.loan_month AS
WITH month_ends AS (
    SELECT
        (date_trunc('month', d) + INTERVAL '1 month - 1 day')::date AS month_end
    FROM generate_series('2024-01-01'::date, '2025-12-31'::date, INTERVAL '1 month') AS d
),
loan_meta AS (
    -- Representative metadata for each loan ID
    SELECT
        loan_id,
        MAX(customer_id) as customer_id,
        MAX(interest_rate_apr) as interest_rate_apr,
        MAX(origination_fee) as origination_fee,
        MAX(origination_fee_taxes) as origination_fee_taxes,
        MAX(days_past_due) as days_past_due
    FROM loan_data
    GROUP BY loan_id
),
cum_disb AS (
    SELECT
        m.month_end,
        l.loan_id,
        SUM(l.disbursement_amount) AS total_disbursed
    FROM month_ends m
    JOIN loan_data l ON m.month_end >= l.disbursement_date
    GROUP BY 1, 2
),
cum_pay AS (
    SELECT
        m.month_end,
        p.loan_id,
        SUM(p.true_principal_payment) AS total_paid
    FROM month_ends m
    JOIN real_payment p ON m.month_end >= p.true_payment_date
    GROUP BY 1, 2
)
SELECT
    cd.month_end,
    cd.loan_id,
    lm.customer_id,
    cd.total_disbursed as disbursement_amount, -- for pricing view compatibility
    lm.interest_rate_apr,
    lm.origination_fee,
    lm.origination_fee_taxes,
    GREATEST(cd.total_disbursed - COALESCE(cp.total_paid, 0), 0) AS outstanding,
    lm.days_past_due
FROM cum_disb cd
JOIN loan_meta lm ON lm.loan_id = cd.loan_id
LEFT JOIN cum_pay cp ON cd.loan_id = cp.loan_id AND cd.month_end = cp.month_end;

-- ---------------------------------------------------------------------
-- 3. PRICING KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_monthly_pricing AS
WITH income_per_loan AS (
    SELECT
        loan_id,
        (date_trunc('month', true_payment_date) + INTERVAL '1 month - 1 day')::date AS month_end,
        SUM(COALESCE(true_interest_payment, 0)) AS total_int,
        SUM(COALESCE(true_fee_payment, 0))      AS total_fee,
        SUM(COALESCE(true_other_payment, 0))    AS total_other,
        SUM(COALESCE(true_tax_payment, 0))      AS total_tax,
        SUM(COALESCE(true_fee_tax_payment, 0))  AS total_fee_tax,
        SUM(COALESCE(true_rebates, 0))          AS total_rebates
    FROM real_payment
    GROUP BY 1, 2
),
loan_rates AS (
    SELECT
        lm.month_end,
        lm.loan_id,
        lm.outstanding,
        lm.interest_rate_apr AS apr,
        (lm.origination_fee + lm.origination_fee_taxes)
            / NULLIF(lm.disbursement_amount, 0)      AS fee_rate,
        (
            (COALESCE(i.total_fee, 0)
            + COALESCE(i.total_other, 0)
            + COALESCE(i.total_tax, 0)
            + COALESCE(i.total_fee_tax, 0)
            - COALESCE(i.total_rebates, 0))
            / NULLIF(lm.outstanding, 0)
        )                                           AS other_income_rate
    FROM analytics.loan_month lm
    LEFT JOIN income_per_loan i
      ON i.loan_id = lm.loan_id AND i.month_end = lm.month_end
)
SELECT
    lr.month_end                           AS year_month,
    SUM(lr.apr * lr.outstanding)
        / NULLIF(SUM(lr.outstanding), 0)   AS weighted_apr,
    SUM(lr.fee_rate * lr.outstanding)
        / NULLIF(SUM(lr.outstanding), 0)   AS weighted_fee_rate,
    SUM(COALESCE(lr.other_income_rate, 0) * lr.outstanding)
        / NULLIF(SUM(lr.outstanding), 0)   AS weighted_other_income_rate,
    SUM((COALESCE(i.total_int, 0) + COALESCE(i.total_fee, 0) + COALESCE(i.total_other, 0) + COALESCE(i.total_tax, 0) + COALESCE(i.total_fee_tax, 0) - COALESCE(i.total_rebates, 0)))
        / NULLIF(SUM(lr.outstanding), 0) AS weighted_effective_rate
FROM loan_rates lr
LEFT JOIN income_per_loan i ON i.loan_id = lr.loan_id AND i.month_end = lr.month_end
WHERE lr.outstanding > 1e-4
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 4. RISK KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_monthly_risk AS
SELECT
    month_end AS year_month,
    SUM(outstanding) AS total_outstanding,

    SUM(CASE WHEN days_past_due >= 7  THEN outstanding ELSE 0 END) AS dpd7_amount,
    SUM(CASE WHEN days_past_due >= 7  THEN outstanding ELSE 0 END)
        / NULLIF(SUM(outstanding),0)                               AS dpd7_pct,

    SUM(CASE WHEN days_past_due >= 15 THEN outstanding ELSE 0 END) AS dpd15_amount,
    SUM(CASE WHEN days_past_due >= 15 THEN outstanding ELSE 0 END)
        / NULLIF(SUM(outstanding),0)                               AS dpd15_pct,

    SUM(CASE WHEN days_past_due >= 30 THEN outstanding ELSE 0 END) AS dpd30_amount,
    SUM(CASE WHEN days_past_due >= 30 THEN outstanding ELSE 0 END)
        / NULLIF(SUM(outstanding),0)                               AS dpd30_pct,

    SUM(CASE WHEN days_past_due >= 60 THEN outstanding ELSE 0 END) AS dpd60_amount,
    SUM(CASE WHEN days_past_due >= 60 THEN outstanding ELSE 0 END)
        / NULLIF(SUM(outstanding),0)                               AS dpd60_pct,

    SUM(CASE WHEN days_past_due >= 90 THEN outstanding ELSE 0 END) AS dpd90_amount,
    SUM(CASE WHEN days_past_due >= 90 THEN outstanding ELSE 0 END)
        / NULLIF(SUM(outstanding),0)                               AS default_pct
FROM analytics.loan_month
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 5. CUSTOMER TYPES KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_customer_types AS
WITH ranked_loans AS (
    SELECT
        l.customer_id,
        l.disbursement_date::date AS disbursement_date,
        l.disbursement_amount,
        l.days_past_due,
        ROW_NUMBER() OVER (PARTITION BY l.customer_id ORDER BY l.disbursement_date, l.loan_id) AS rn,
        LAG(l.disbursement_date::date) OVER (PARTITION BY l.customer_id ORDER BY l.disbursement_date, l.loan_id) AS prev_disb,
        MAX(l.days_past_due) OVER (PARTITION BY l.customer_id) AS max_dpd_ever
    FROM loan_data l
    JOIN customer_data c ON l.customer_id = c.customer_id
),
classified AS (
    SELECT
        customer_id,
        disbursement_date,
        disbursement_amount,
        CASE
            WHEN max_dpd_ever > 90 AND days_past_due <= 30 THEN 'Recovered'
            WHEN rn = 1 THEN 'New'
            WHEN prev_disb IS NOT NULL AND (disbursement_date - prev_disb) > 180 THEN 'Reactivated'
            ELSE 'Recurrent'
        END AS customer_type
    FROM ranked_loans
)
SELECT
    (date_trunc('month', disbursement_date) + INTERVAL '1 month - 1 day')::date AS year_month,
    customer_type,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(disbursement_amount) AS disbursement_amount
FROM classified
GROUP BY 1, 2
ORDER BY 1, 2;

-- ---------------------------------------------------------------------
-- 6. ACTIVE UNIQUE CUSTOMERS KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_active_unique_customers AS
SELECT
    month_end AS year_month,
    COUNT(DISTINCT customer_id) AS active_customers
FROM analytics.loan_month
WHERE outstanding > 1e-4
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 7. AVERAGE TICKET KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_average_ticket AS
WITH src AS (
    SELECT
        (date_trunc('month', disbursement_date) + INTERVAL '1 month - 1 day')::date AS year_month,
        loan_id,
        disbursement_amount,
        CASE
            WHEN disbursement_amount < 10000 THEN '< 10K'
            WHEN disbursement_amount <= 25000 THEN '10-25K'
            WHEN disbursement_amount <= 50000 THEN '25-50K'
            WHEN disbursement_amount <= 100000 THEN '50-100K'
            ELSE '> 100K'
        END AS ticket_band
    FROM loan_data
)
SELECT
    year_month,
    ticket_band,
    COUNT(loan_id) AS num_loans,
    AVG(disbursement_amount) AS avg_ticket,
    SUM(disbursement_amount) AS total_disbursement
FROM src
GROUP BY 1, 2
ORDER BY 1, 2;

-- ---------------------------------------------------------------------
-- 8. INTENSITY SEGMENTATION KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_intensity_segmentation AS
WITH loans_per_cust AS (
    SELECT
        customer_id,
        COUNT(DISTINCT loan_id) AS loans_count
    FROM loan_data
    GROUP BY 1
),
intensity AS (
    SELECT
        customer_id,
        CASE
            WHEN loans_count <= 1 THEN 'Low'
            WHEN loans_count <= 3 THEN 'Medium'
            ELSE 'Heavy'
        END AS use_intensity
    FROM loans_per_cust
)
SELECT
    (date_trunc('month', l.disbursement_date) + INTERVAL '1 month - 1 day')::date AS year_month,
    i.use_intensity,
    COUNT(DISTINCT l.customer_id) AS unique_customers,
    SUM(l.disbursement_amount) AS disbursement_amount
FROM loan_data l
JOIN intensity i ON l.customer_id = i.customer_id
GROUP BY 1, 2
ORDER BY 1, 2;

-- ---------------------------------------------------------------------
-- 9. LINE SIZE SEGMENTATION KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_line_size_segmentation AS
WITH src AS (
    SELECT
        (date_trunc('month', disbursement_date) + INTERVAL '1 month - 1 day')::date AS year_month,
        customer_id,
        disbursement_amount,
        CASE
            WHEN disbursement_amount < 10000 THEN '< 10K'
            WHEN disbursement_amount <= 25000 THEN '10-25K'
            WHEN disbursement_amount <= 50000 THEN '25-50K'
            ELSE '> 50K'
        END AS line_band
    FROM loan_data
)
SELECT
    year_month,
    line_band,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(disbursement_amount) AS disbursement_amount
FROM src
GROUP BY 1, 2
ORDER BY 1, 2;

-- ---------------------------------------------------------------------
-- 10. CONCENTRATION KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_concentration AS
WITH ranked AS (
    SELECT
        month_end,
        outstanding,
        ROW_NUMBER() OVER (PARTITION BY month_end ORDER BY outstanding DESC) AS rn,
        COUNT(*) OVER (PARTITION BY month_end) AS total_n,
        SUM(outstanding) OVER (PARTITION BY month_end) AS total_outstanding
    FROM analytics.loan_month
    WHERE outstanding > 1e-4
),
bands AS (
    SELECT
        month_end,
        total_outstanding,
        SUM(CASE WHEN rn <= ceil(0.10 * total_n) THEN outstanding ELSE 0 END) AS top10_amount,
        SUM(CASE WHEN rn <= ceil(0.03 * total_n) THEN outstanding ELSE 0 END) AS top3_amount,
        SUM(CASE WHEN rn <= ceil(0.01 * total_n) THEN outstanding ELSE 0 END) AS top1_amount
    FROM ranked
    GROUP BY 1, 2
)
SELECT
    month_end AS year_month,
    total_outstanding,
    top10_amount / NULLIF(total_outstanding, 0) AS top10_concentration,
    top3_amount / NULLIF(total_outstanding, 0) AS top3_concentration,
    top1_amount / NULLIF(total_outstanding, 0) AS top1_concentration
FROM bands
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 11. WEIGHTED APR KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_weighted_apr AS
SELECT
    month_end AS year_month,
    SUM(interest_rate_apr * outstanding) / NULLIF(SUM(outstanding), 0) AS weighted_apr
FROM analytics.loan_month
WHERE outstanding > 1e-4
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 12. WEIGHTED FEE RATE KPI VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW analytics.kpi_weighted_fee_rate AS
SELECT
    month_end AS year_month,
    SUM(((origination_fee + origination_fee_taxes) / NULLIF(disbursement_amount, 0)) * outstanding)
        / NULLIF(SUM(outstanding), 0) AS weighted_fee_rate
FROM analytics.loan_month
WHERE outstanding > 1e-4
GROUP BY 1
ORDER BY 1;

-- ---------------------------------------------------------------------
-- 13. ANALYTICS FACTS TABLE (For CSV Imports)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.analytics_facts (
    month                       DATE PRIMARY KEY,
    outstanding                 NUMERIC,
    active_clients              INTEGER,
    sched_revenue               NUMERIC,
    recv_revenue_paid_month     NUMERIC,
    sched_interest              NUMERIC,
    recv_interest_paid_month    NUMERIC,
    recv_fee_paid_month         NUMERIC,
    sched_fee                   NUMERIC,
    new_clients                 NUMERIC,
    reactivated_clients         NUMERIC,
    recovered_clients           NUMERIC,
    recurrent_clients           NUMERIC,
    disbursement                NUMERIC,
    top10_concentration         NUMERIC,
    early                       NUMERIC,
    late                        NUMERIC,
    on_time                     NUMERIC,
    unmapped                    NUMERIC,
    collection_rate_due_month   NUMERIC,
    cum_scheduled               NUMERIC,
    cum_received_paid_month     NUMERIC,
    cum_received_due_month      NUMERIC,
    outstanding_proj            NUMERIC,
    planned_disbursement        NUMERIC,
    remaining_capital           NUMERIC,
    recv_interest_for_month     NUMERIC,
    recv_fee_for_month          NUMERIC,
    recv_revenue_for_month      NUMERIC,
    recurrence_pct              NUMERIC,
    throughput_12m              NUMERIC,
    rotation                    NUMERIC,
    apr_realized                NUMERIC,
    yield_incl_fees             NUMERIC,
    sam_penetration             NUMERIC,
    cac                         NUMERIC,
    ltv_realized                NUMERIC,
    ltv_cac_ratio               NUMERIC,
    cum_unique_customers        NUMERIC
);

-- ---------------------------------------------------------------------
-- 14. FIGMA DASHBOARD VIEW
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW public.figma_dashboard AS
SELECT
  month::date                AS "Month",
  to_char(month,'YYYY-MM')   AS "Month Label",
  active_clients             AS "Active Clients",
  new_clients                AS "New Clients",
  recurrent_clients          AS "Recurrent Clients",
  recovered_clients          AS "Recovered Clients",
  outstanding                AS "Outstanding",
  outstanding_proj           AS "Outstanding (Proj)",
  disbursement               AS "Disbursement",
  top10_concentration        AS "Top10 Concentration",
  planned_disbursement       AS "Planned Disbursement",
  remaining_capital          AS "Remaining Capital",
  sched_interest             AS "Sched Interest",
  sched_fee                  AS "Sched Fee",
  sched_revenue              AS "Sched Revenue",
  recv_interest_for_month    AS "Recv Interest for Month",
  recv_fee_for_month         AS "Recv Fee for Month",
  recv_revenue_for_month     AS "Recv Revenue for Month",
  recv_interest_paid_month   AS "Recv Interest (Paid Month)",
  recv_fee_paid_month        AS "Recv Fee (Paid Month)",
  recv_revenue_paid_month    AS "Recv Revenue (Paid Month)",
  early                      AS "Early",
  on_time                    AS "On-time",
  late                       AS "Late",
  unmapped                   AS "Unmapped",
  collection_rate_due_month  AS "Collection Rate (for Due Month)",
  cum_scheduled              AS "Cum Scheduled",
  cum_received_paid_month    AS "Cum Received (Paid Month)",
  cum_received_due_month     AS "Cum Received (for Due Month)",
  recurrence_pct             AS "Recurrence (%)",
  throughput_12m             AS "Throughput 12M",
  rotation                   AS "Rotation",
  apr_realized               AS "APR Realized",
  yield_incl_fees            AS "Yield incl. Fees",
  sam_penetration            AS "SAM Penetration",
  cac                        AS "CAC",
  ltv_realized               AS "LTV Realized",
  ltv_cac_ratio              AS "LTV/CAC Ratio",
  cum_unique_customers       AS "Clients EOP"
FROM public.analytics_facts;

COMMIT;
