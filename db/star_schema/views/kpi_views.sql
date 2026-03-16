-- =============================================================================
-- Monthly KPI Views — Abaco Loans Analytics
-- Compatible with both PostgreSQL (Supabase) and DuckDB
-- =============================================================================

-- ---------------------------------------------------------------------------
-- v_monthly_disbursements
-- Total disbursed principal per month / currency / product
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_disbursements AS
SELECT
    t.year_month,
    t.snapshot_month                              AS month_end,
    l.currency,
    l.product_type,
    l.branch_code,
    COUNT(DISTINCT f.loan_sk)                     AS new_loans,
    SUM(f.principal_amount)                       AS total_disbursed
FROM fact_disbursement f
JOIN dim_loan  l ON l.loan_sk  = f.loan_sk
JOIN dim_time  t ON t.time_id  = f.time_id
GROUP BY 1, 2, 3, 4, 5;

-- ---------------------------------------------------------------------------
-- v_monthly_outstanding_balance
-- Active portfolio balance at each month-end snapshot
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_outstanding_balance AS
SELECT
    t.year_month,
    s.snapshot_month,
    l.currency,
    l.product_type,
    l.branch_code,
    COUNT(DISTINCT s.loan_sk)                     AS active_loans,
    SUM(s.principal_outstanding)                  AS total_outstanding,
    SUM(s.total_overdue_amount)                   AS total_overdue
FROM fact_monthly_snapshot s
JOIN dim_loan  l ON l.loan_sk = s.loan_sk
JOIN dim_time  t ON t.time_id = s.time_id
GROUP BY 1, 2, 3, 4, 5;

-- ---------------------------------------------------------------------------
-- v_monthly_mora
-- DPD / mora breakdown per month-end snapshot
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_mora AS
SELECT
    t.year_month,
    s.snapshot_month,
    l.currency,
    l.product_type,
    s.mora_bucket,
    COUNT(DISTINCT s.loan_sk)                     AS loans_in_bucket,
    SUM(s.principal_outstanding)                  AS outstanding_in_bucket,
    SUM(s.total_overdue_amount)                   AS overdue_in_bucket
FROM fact_monthly_snapshot s
JOIN dim_loan  l ON l.loan_sk = s.loan_sk
JOIN dim_time  t ON t.time_id = s.time_id
GROUP BY 1, 2, 3, 4, 5;

-- ---------------------------------------------------------------------------
-- v_par_monthly
-- Portfolio-at-Risk (PAR) % at each threshold per month
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_par_monthly AS
SELECT
    t.year_month,
    s.snapshot_month,
    l.currency,
    l.product_type,
    SUM(s.principal_outstanding)                                          AS total_outstanding,
    SUM(CASE WHEN s.par_1  THEN s.principal_outstanding ELSE 0 END)       AS par_1_amount,
    SUM(CASE WHEN s.par_30 THEN s.principal_outstanding ELSE 0 END)       AS par_30_amount,
    SUM(CASE WHEN s.par_60 THEN s.principal_outstanding ELSE 0 END)       AS par_60_amount,
    SUM(CASE WHEN s.par_90 THEN s.principal_outstanding ELSE 0 END)       AS par_90_amount,
    CASE WHEN SUM(s.principal_outstanding) > 0
         THEN ROUND(100.0 * SUM(CASE WHEN s.par_1  THEN s.principal_outstanding ELSE 0 END)
                  / SUM(s.principal_outstanding), 2) END                  AS par_1_pct,
    CASE WHEN SUM(s.principal_outstanding) > 0
         THEN ROUND(100.0 * SUM(CASE WHEN s.par_30 THEN s.principal_outstanding ELSE 0 END)
                  / SUM(s.principal_outstanding), 2) END                  AS par_30_pct,
    CASE WHEN SUM(s.principal_outstanding) > 0
         THEN ROUND(100.0 * SUM(CASE WHEN s.par_60 THEN s.principal_outstanding ELSE 0 END)
                  / SUM(s.principal_outstanding), 2) END                  AS par_60_pct,
    CASE WHEN SUM(s.principal_outstanding) > 0
         THEN ROUND(100.0 * SUM(CASE WHEN s.par_90 THEN s.principal_outstanding ELSE 0 END)
                  / SUM(s.principal_outstanding), 2) END                  AS par_90_pct
FROM fact_monthly_snapshot s
JOIN dim_loan  l ON l.loan_sk = s.loan_sk
JOIN dim_time  t ON t.time_id = s.time_id
GROUP BY 1, 2, 3, 4;

-- ---------------------------------------------------------------------------
-- v_monthly_income
-- Monthly payment income (interest + fees) per product
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_income AS
SELECT
    t.year_month,
    t.snapshot_month                              AS month_end,
    l.currency,
    l.product_type,
    l.branch_code,
    COUNT(DISTINCT p.loan_sk)                     AS paying_loans,
    SUM(p.principal_paid)                         AS principal_collected,
    SUM(p.interest_paid)                          AS interest_collected,
    SUM(p.fees_paid)                              AS fees_collected,
    SUM(p.total_paid)                             AS total_collected
FROM fact_payment p
JOIN dim_loan  l ON l.loan_sk = p.loan_sk
JOIN dim_time  t ON t.time_id = p.time_id
GROUP BY 1, 2, 3, 4, 5;

-- ---------------------------------------------------------------------------
-- v_monthly_apr_proxy
-- Annualised Percentage Return proxy: interest_collected / avg_outstanding * 12
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_monthly_apr_proxy AS
SELECT
    i.year_month,
    i.month_end,
    i.currency,
    i.product_type,
    i.interest_collected,
    b.total_outstanding                                                    AS avg_outstanding,
    CASE WHEN b.total_outstanding > 0
         THEN ROUND(12.0 * i.interest_collected / b.total_outstanding * 100, 2)
    END                                                                    AS apr_proxy_pct
FROM v_monthly_income    i
LEFT JOIN v_monthly_outstanding_balance b
       ON  b.year_month    = i.year_month
       AND b.currency      = i.currency
       AND b.product_type  = i.product_type;

-- ---------------------------------------------------------------------------
-- v_kpi_summary
-- One-row-per-month executive KPI summary
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_kpi_summary AS
SELECT
    t.year_month,
    t.snapshot_month,
    -- Disbursements
    COALESCE(d.new_loans,          0)             AS new_loans,
    COALESCE(d.total_disbursed,    0)             AS total_disbursed,
    -- Portfolio
    COALESCE(b.active_loans,       0)             AS active_loans,
    COALESCE(b.total_outstanding,  0)             AS total_outstanding,
    COALESCE(b.total_overdue,      0)             AS total_overdue,
    -- PAR (averaged across dimensions)
    COALESCE(par.par_30_pct,       0)             AS par_30_pct,
    COALESCE(par.par_90_pct,       0)             AS par_90_pct,
    -- Income
    COALESCE(inc.interest_collected, 0)           AS interest_collected,
    COALESCE(inc.total_collected,    0)           AS total_collected,
    -- APR proxy (averaged across dimensions)
    apr.apr_proxy_pct
FROM dim_time t
LEFT JOIN (
    SELECT
        year_month,
        SUM(new_loans)        AS new_loans,
        SUM(total_disbursed)  AS total_disbursed
    FROM v_monthly_disbursements
    GROUP BY year_month
) d
    ON d.year_month = t.year_month
LEFT JOIN (
    SELECT
        year_month,
        SUM(active_loans)      AS active_loans,
        SUM(total_outstanding) AS total_outstanding,
        SUM(total_overdue)     AS total_overdue
    FROM v_monthly_outstanding_balance
    GROUP BY year_month
) b
    ON b.year_month = t.year_month
LEFT JOIN (
    SELECT
        year_month,
        AVG(par_30_pct) AS par_30_pct,
        AVG(par_90_pct) AS par_90_pct
    FROM v_par_monthly
    GROUP BY year_month
) par
    ON par.year_month = t.year_month
LEFT JOIN (
    SELECT
        year_month,
        SUM(interest_collected) AS interest_collected,
        SUM(total_collected)    AS total_collected
    FROM v_monthly_income
    GROUP BY year_month
) inc
    ON inc.year_month = t.year_month
LEFT JOIN (
    SELECT
        year_month,
        AVG(apr_proxy_pct) AS apr_proxy_pct
    FROM v_monthly_apr_proxy
    GROUP BY year_month
) apr
    ON apr.year_month = t.year_month
ORDER BY t.snapshot_month;
