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
  ('cost_of_risk', 'cost_of_risk', 'Cost Of Risk', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Cost of risk as a percentage of portfolio'),
  ('cure_rate', 'cure_rate', 'Cure Rate', 'Risk', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Share of delinquent loans returning to current'),
  ('delinq_1_30_rate', 'delinq_1_30_rate', 'Delinq 1-30 Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Outstanding exposure in 1-30 DPD bucket'),
  ('delinq_31_60_rate', 'delinq_31_60_rate', 'Delinq 31-60 Rate', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Outstanding exposure in 31-60 DPD bucket'),
  ('lgd', 'lgd', 'LGD', 'Risk', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Loss given default'),
  ('net_interest_margin', 'net_interest_margin', 'Net Interest Margin', 'Profitability', 'percent', 'higher_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Net interest margin'),
  ('npl_ratio', 'npl_ratio', 'NPL Ratio', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Non-performing loans ratio'),
  ('par_60', 'par_60', 'PAR 60', 'Asset Quality', 'percent', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Portfolio at risk 60+ days'),
  ('payback_period', 'payback_period', 'Payback Period', 'Unit Economics', 'months', 'lower_is_better', 'current', 'portfolio', 'monitoring', ARRAY['loan_tape'], 'v1', 'Payback period in months')
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