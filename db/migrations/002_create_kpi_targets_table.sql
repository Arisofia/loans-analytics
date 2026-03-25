-- Migration: Create KPI Targets Table for 2026 Portfolio Goals
-- Purpose: Store projected portfolio targets by month for variance tracking
-- Date: 2026-03-25

CREATE TABLE IF NOT EXISTS kpi_targets_2026 (
  id BIGSERIAL PRIMARY KEY,
  month_number INT NOT NULL CHECK (month_number >= 1 AND month_number <= 12),
  month_name VARCHAR(3) NOT NULL CHECK (month_name IN ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec')),
  
  -- Portfolio targets (in USD)
  portfolio_target NUMERIC(15, 2) NOT NULL,
  aum_target NUMERIC(15, 2),
  
  -- Risk targets
  npl_target_pct NUMERIC(5, 2),
  default_rate_target_pct NUMERIC(5, 2),
  
  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(255),
  notes TEXT,
  
  UNIQUE(month_number, month_name)
);

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_kpi_targets_2026_month ON kpi_targets_2026(month_number);
CREATE INDEX IF NOT EXISTS idx_kpi_targets_2026_month_name ON kpi_targets_2026(month_name);

-- Enable RLS (Row Level Security) for multi-tenant safety
ALTER TABLE kpi_targets_2026 ENABLE ROW LEVEL SECURITY;

-- Seed 2026 targets
INSERT INTO kpi_targets_2026 (month_number, month_name, portfolio_target, created_by)
VALUES
  (1, 'Jan', 8500000.00, 'system'),
  (2, 'Feb', 9000000.00, 'system'),
  (3, 'Mar', 9300000.00, 'system'),
  (4, 'Apr', 9600000.00, 'system'),
  (5, 'May', 9900000.00, 'system'),
  (6, 'Jun', 10200000.00, 'system'),
  (7, 'Jul', 10500000.00, 'system'),
  (8, 'Aug', 10800000.00, 'system'),
  (9, 'Sep', 11100000.00, 'system'),
  (10, 'Oct', 11400000.00, 'system'),
  (11, 'Nov', 11700000.00, 'system'),
  (12, 'Dec', 12000000.00, 'system')
ON CONFLICT (month_number, month_name) DO UPDATE SET
  portfolio_target = EXCLUDED.portfolio_target,
  updated_at = CURRENT_TIMESTAMP;

-- Create view for easy variance calculation
CREATE OR REPLACE VIEW kpi_targets_with_variance AS
SELECT 
  t.month_number,
  t.month_name,
  t.portfolio_target,
  COALESCE(k.aum, 0) AS actual_portfolio,
  (COALESCE(k.aum, 0) - t.portfolio_target) AS variance_amount,
  CASE 
    WHEN t.portfolio_target = 0 THEN 0
    ELSE ROUND(((COALESCE(k.aum, 0) - t.portfolio_target) / t.portfolio_target * 100)::NUMERIC, 2)
  END AS variance_pct,
  CASE 
    WHEN COALESCE(k.aum, 0) >= (t.portfolio_target * 0.95) THEN 'ON_TRACK'
    WHEN COALESCE(k.aum, 0) < (t.portfolio_target * 0.90) THEN 'AT_RISK'
    ELSE 'MONITOR'
  END AS status
FROM kpi_targets_2026 t
LEFT JOIN kpi_timeseries_daily k 
  ON EXTRACT(MONTH FROM k.date) = t.month_number 
  AND EXTRACT(YEAR FROM k.date) = 2026
  AND k.kpi_name = 'total_aum'
  AND k.date = (
    SELECT MAX(date) FROM kpi_timeseries_daily k2
    WHERE EXTRACT(MONTH FROM k2.date) = t.month_number
    AND EXTRACT(YEAR FROM k2.date) = 2026
    AND k2.kpi_name = 'total_aum'
  )
ORDER BY t.month_number;
