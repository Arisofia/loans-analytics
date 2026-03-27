-- Ensure all pipeline-calculated KPIs have definitions in monitoring.kpi_definitions.
-- This is required so that the output phase can map every kpi_name → kpi_key
-- when writing to monitoring.kpi_values.
--
-- Uses ON CONFLICT (kpi_key) DO UPDATE to reconcile metadata without
-- losing existing rows.

BEGIN;

INSERT INTO monitoring.kpi_definitions (
  kpi_key,
  name,
  display_name,
  category,
  unit,
  direction,
  "window",
  basis,
  owner_agent,
  source_tables,
  version,
  description
)
VALUES
  -- Portfolio Performance
  ('total_outstanding_balance', 'total_outstanding_balance', 'Total Outstanding Balance', 'Portfolio Performance', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total outstanding principal across all non-closed loans'),
  ('total_loans_count', 'total_loans_count', 'Total Loans Count', 'Portfolio Performance', 'count', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Number of active loans in portfolio'),
  ('average_loan_size', 'average_loan_size', 'Average Loan Size', 'Portfolio Performance', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average original loan amount'),
  ('portfolio_yield', 'portfolio_yield', 'Portfolio Yield', 'Portfolio Performance', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average annualized interest rate across portfolio'),
  ('total_aum', 'total_aum', 'Total AUM', 'Portfolio Performance', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total assets under management'),
  ('loan_count', 'loan_count', 'Loan Count', 'Portfolio Performance', 'count', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total number of loans'),

  -- Asset Quality
  ('par_30', 'par_30', 'PAR 30', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at Risk 30+ days past due'),
  ('par_60', 'par_60', 'PAR 60', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at Risk 60+ days past due'),
  ('par_90', 'par_90', 'PAR 90', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at Risk 90+ days past due'),
  ('npl_ratio', 'npl_ratio', 'NPL Ratio', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Non-performing loans ratio (DPD >= 30 or delinquent/defaulted)'),
  ('npl_90_ratio', 'npl_90_ratio', 'NPL 90 Ratio', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Non-performing loans ratio (strict Basel 90-day)'),
  ('npl_rate', 'npl_rate', 'NPL Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Non-performing loan rate'),
  ('default_rate', 'default_rate', 'Default Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Percentage of loans in default'),
  ('delinq_1_30_rate', 'delinq_1_30_rate', 'Delinq 1-30 Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Outstanding exposure in 1-30 DPD bucket'),
  ('delinq_31_60_rate', 'delinq_31_60_rate', 'Delinq 31-60 Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Outstanding exposure in 31-60 DPD bucket'),
  ('loss_rate', 'loss_rate', 'Loss Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Outstanding balance at risk as % of disbursed principal'),
  ('lgd', 'lgd', 'LGD', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Loss given default'),
  ('cost_of_risk', 'cost_of_risk', 'Cost Of Risk', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Expected credit loss as % of total portfolio balance'),
  ('cure_rate', 'cure_rate', 'Cure Rate', 'Risk', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Share of delinquent loans returning to current'),
  ('defaulted_outstanding_ratio', 'defaulted_outstanding_ratio', 'Defaulted Outstanding Ratio', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Defaulted outstanding balance as % of total'),

  -- Cash Flow
  ('collections_rate', 'collections_rate', 'Collections Rate', 'Cash Flow', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Collection efficiency (payments received vs scheduled)'),
  ('collection_rate_6m', 'collection_rate_6m', 'Collection Rate 6m', 'Cash Flow', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', '6-month collection rate'),
  ('recovery_rate', 'recovery_rate', 'Recovery Rate', 'Cash Flow', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Recovery rate on defaulted loans'),
  ('cash_on_hand', 'cash_on_hand', 'Cash On Hand', 'Cash Flow', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total current cash position'),
  ('net_interest_margin', 'net_interest_margin', 'Net Interest Margin', 'Profitability', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Net interest margin'),
  ('payback_period', 'payback_period', 'Payback Period', 'Unit Economics', 'months', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Payback period proxy'),

  -- Growth
  ('disbursement_volume_mtd', 'disbursement_volume_mtd', 'Disbursement Volume MTD', 'Growth', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total disbursements month-to-date'),
  ('disbursement_volume', 'disbursement_volume', 'Disbursement Volume', 'Growth', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Total disbursement volume'),
  ('new_loans_count_mtd', 'new_loans_count_mtd', 'New Loans Count MTD', 'Growth', 'count', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Number of new loans originated this month'),
  ('new_loans', 'new_loans', 'New Loans', 'Growth', 'count', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'New loans originated'),
  ('portfolio_growth_rate', 'portfolio_growth_rate', 'Portfolio Growth Rate', 'Growth', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Month-over-month portfolio growth'),
  ('portfolio_rotation', 'portfolio_rotation', 'Portfolio Rotation', 'Growth', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio rotation rate'),

  -- Customer Metrics
  ('active_borrowers', 'active_borrowers', 'Active Borrowers', 'Customer Metrics', 'count', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Number of active borrowers'),
  ('repeat_borrower_rate', 'repeat_borrower_rate', 'Repeat Borrower Rate', 'Customer Metrics', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Percentage of repeat borrowers'),
  ('customer_lifetime_value', 'customer_lifetime_value', 'Customer Lifetime Value', 'Customer Metrics', 'currency', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average total processed value per customer'),

  -- Operational Metrics
  ('processing_time_avg', 'processing_time_avg', 'Processing Time Avg', 'Operational Metrics', 'months', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average loan term duration'),
  ('processing_time', 'processing_time', 'Processing Time', 'Operational Metrics', 'days', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average processing time'),
  ('automation_rate', 'automation_rate', 'Automation Rate', 'Operational Metrics', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Automation rate'),

  -- Derived Risk (from KPIEngineV2._calculate_derived_risk_kpis)
  ('top_10_borrower_concentration', 'top_10_borrower_concentration', 'Top 10 Borrower Concentration', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Top 10 borrower concentration ratio'),
  ('velocity_of_default', 'velocity_of_default', 'Velocity Of Default', 'Risk', 'bps', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Month-over-month change in default ratio'),
  ('ltv_sintetico_mean', 'ltv_sintetico_mean', 'LTV Sintetico Mean', 'Risk', 'ratio', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average synthetic LTV across portfolio'),
  ('ltv_sintetico_high_risk_pct', 'ltv_sintetico_high_risk_pct', 'LTV Sintetico High Risk %', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Percentage of loans with LTV > 1.0'),

  -- Enriched KPIs
  ('collections_eligible_rate', 'collections_eligible_rate', 'Collections Eligible Rate', 'Collections', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Percentage of balance eligible for active collection'),
  ('government_sector_exposure_rate', 'government_sector_exposure_rate', 'Government Sector Exposure Rate', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Percentage of balance concentrated in government sector'),
  ('avg_credit_line_utilization', 'avg_credit_line_utilization', 'Avg Credit Line Utilization', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Average credit line utilization across borrowers'),
  ('capital_collection_rate', 'capital_collection_rate', 'Capital Collection Rate', 'Collections', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Ratio of principal collected to total outstanding'),

  -- Standard KPIs from engine.calculate_all()
  ('PAR30', 'PAR30', 'PAR 30 (Standard)', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at Risk 30+ days (standard engine)'),
  ('PAR90', 'PAR90', 'PAR 90 (Standard)', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at Risk 90+ days (standard engine)'),
  ('COLLECTION_RATE', 'COLLECTION_RATE', 'Collection Rate (Standard)', 'Cash Flow', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Collection rate (standard engine)'),
  ('LTV', 'LTV', 'LTV (Standard)', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Loan-to-Value ratio (standard engine)'),
  ('write_off_rate', 'write_off_rate', 'Write-Off Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Write-off rate')

ON CONFLICT (kpi_key) DO UPDATE
SET
  name = EXCLUDED.name,
  display_name = EXCLUDED.display_name,
  category = EXCLUDED.category,
  unit = EXCLUDED.unit,
  direction = EXCLUDED.direction,
  "window" = EXCLUDED."window",
  basis = EXCLUDED.basis,
  owner_agent = EXCLUDED.owner_agent,
  source_tables = EXCLUDED.source_tables,
  version = EXCLUDED.version,
  description = EXCLUDED.description,
  updated_at = NOW();

COMMIT;
