-- Add KPI definitions required by current pipeline output
-- so all calculated KPIs can be persisted to monitoring.kpi_values.

BEGIN;

INSERT INTO monitoring.kpi_definitions (name, category, description, unit) VALUES
('loss_rate', 'Asset Quality', 'Outstanding balance at risk as percentage of disbursed principal', 'percent'),
('cash_on_hand', 'Cash Flow', 'Total current cash position across portfolio', 'currency'),
('customer_lifetime_value', 'Customer Metrics', 'Average total processed value per customer', 'currency')
ON CONFLICT (name) DO NOTHING;

COMMIT;
