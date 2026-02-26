# Create Monitoring Tables via Supabase Web UI

Since direct PostgreSQL connection is not available from your network, use the Supabase Web UI to create the monitoring tables.

## Steps

### 1. Open Supabase Dashboard
- Go to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte
- Login if needed

### 2. Create Tables Using SQL Editor

Click **SQL Editor** in the left sidebar, then **New Query**

#### Query 1: Create monitoring schema

```sql
CREATE SCHEMA IF NOT EXISTS monitoring;
```

Click **Run** ✅

#### Query 2: Create kpi_definitions table

```sql
CREATE TABLE monitoring.kpi_definitions (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    unit TEXT,
    red_threshold NUMERIC,
    yellow_threshold NUMERIC,
    owner_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Click **Run** ✅

#### Query 3: Create kpi_values table

```sql
CREATE TABLE monitoring.kpi_values (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),
    value NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    status TEXT CHECK (status IN ('green', 'yellow', 'red')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Click **Run** ✅

#### Query 4: Create indexes

```sql
CREATE INDEX idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);
CREATE INDEX idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);
```

Click **Run** ✅

#### Query 5: Insert KPI definitions

```sql
INSERT INTO monitoring.kpi_definitions (name, category, description, unit) VALUES
('par_30', 'Asset Quality', 'Portfolio % at risk 30+ days', 'percent'),
('par_90', 'Asset Quality', 'Portfolio % at risk 90+ days', 'percent'),
('npl_rate', 'Asset Quality', 'Non-performing loan rate', 'percent'),
('default_rate', 'Asset Quality', 'Default rate', 'percent'),
('write_off_rate', 'Asset Quality', 'Write-off rate', 'percent'),
('collection_rate_6m', 'Cash Flow', '6-month collection rate', 'percent'),
('recovery_rate', 'Cash Flow', 'Recovery rate on defaults', 'percent'),
('portfolio_rotation', 'Growth', 'Portfolio rotation rate', 'percent'),
('disbursement_volume', 'Growth', 'Total disbursement volume', 'units'),
('new_loans', 'Growth', 'New loans originated', 'count'),
('total_aum', 'Portfolio Performance', 'Total assets under management', 'currency'),
('average_loan_size', 'Portfolio Performance', 'Average loan size', 'currency'),
('loan_count', 'Portfolio Performance', 'Total number of loans', 'count'),
('portfolio_yield', 'Portfolio Performance', 'Portfolio yield', 'percent'),
('active_borrowers', 'Customer Metrics', 'Active borrowers', 'count'),
('repeat_borrower_rate', 'Customer Metrics', 'Repeat borrower rate', 'percent'),
('processing_time', 'Operational Metrics', 'Average processing time', 'days'),
('automation_rate', 'Operational Metrics', 'Automation rate', 'percent'),
('portfolio_ghg', 'Environmental', 'Portfolio GHG emissions', 'tons')
ON CONFLICT (name) DO NOTHING;
```

Click **Run** ✅

#### Query 6: Insert sample KPI values

```sql
INSERT INTO monitoring.kpi_values (kpi_id, value, timestamp, status) VALUES
(1, 5.2, NOW(), 'green'),
(2, 2.1, NOW(), 'green'),
(3, 7.3, NOW(), 'yellow'),
(4, 3.5, NOW(), 'green'),
(5, 1.2, NOW(), 'green'),
(6, 94.5, NOW(), 'green'),
(7, 68.2, NOW(), 'green'),
(8, 15.8, NOW(), 'green'),
(9, 12500000, NOW(), 'green'),
(10, 1250, NOW(), 'green'),
(11, 450000000, NOW(), 'green'),
(12, 18000, NOW(), 'green'),
(13, 25000, NOW(), 'green'),
(14, 8.5, NOW(), 'green'),
(15, 18000, NOW(), 'green'),
(16, 42.5, NOW(), 'green'),
(17, 2.3, NOW(), 'green'),
(18, 65.0, NOW(), 'green'),
(19, 15420, NOW(), 'green');
```

Click **Run** ✅

### 3. Verify Tables

Go to **Table Editor** in the sidebar

- Should see `monitoring.kpi_definitions` with 19 rows
- Should see `monitoring.kpi_values` with 19 rows

### 4. Verify in Grafana

1. Open Grafana: http://localhost:3001
2. Go to: Configuration → Data Sources
3. Select: Supabase PostgreSQL
4. Click: Test
5. Expected: ✅ "Data source is working"

### 5. View Dashboards

1. Go to: Dashboards → Browse
2. Select folder: KPI Monitoring
3. View: ABACO KPI Overview
4. Should see sample data displayed

---

**That's it!** Your Grafana is now connected to Supabase and showing data.

