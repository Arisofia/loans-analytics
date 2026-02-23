# Grafana Data Setup Guide

**Status:** 🟡 IN PROGRESS  
**Issue Found:** Grafana showing no data (tables don't exist yet)  
**Last Updated:** 2026-02-21

---

## 🔍 Problem Analysis

### What Was Happening
Grafana was running but displaying no data because:

1. **Project Mismatch:** Grafana was pointing to production project (`goxdevkqozomyhsyxhte`) but your data is in development project (`sddviizcgheusvwqpthm`)
2. **Missing Tables:** Monitoring tables (`monitoring.kpi_definitions`, `monitoring.kpi_values`) don't exist in Supabase yet

### What We Fixed
✅ **Aligned Supabase Projects**
- Updated Grafana to use your development project: `sddviizcgheusvwqpthm`
- Updated `.env.monitoring` with correct credentials
- Restarted Grafana with new configuration

✅ **Prepared Table Creation Scripts**
- Created script to populate tables via Supabase UI
- Created Python script for future automated setup

---

## 📊 Create Tables in Supabase

Since you don't have direct PostgreSQL access from your network, use the **Supabase Web UI**:

### Quick Link
👉 **https://supabase.com/dashboard/project/sddviizcgheusvwqpthm/sql**

### Copy-Paste SQL Queries

Open that URL and run these queries in order:

**Query 1: Create Schema**
```sql
CREATE SCHEMA IF NOT EXISTS monitoring;
```

**Query 2: Create KPI Definitions Table**
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

**Query 3: Create KPI Values Table**
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

**Query 4: Create Indexes**
```sql
CREATE INDEX idx_kpi_values_timestamp ON monitoring.kpi_values(timestamp DESC);
CREATE INDEX idx_kpi_values_kpi_id ON monitoring.kpi_values(kpi_id);
```

**Query 5: Insert 19 KPI Definitions**
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

**Query 6: Insert Sample KPI Values**
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

---

## ✅ Verify in Grafana

### 1. Test Datasource Connection

1. Open: http://localhost:3001
2. Login: admin / admin123
3. Go to: **Configuration → Data Sources**
4. Select: **Supabase PostgreSQL**
5. Click: **Test** button
6. Expected: ✅ **"Data source is working"**

### 2. View KPI Dashboards

1. Click: **Dashboards → Browse**
2. Select folder: **KPI Monitoring**
3. Open: **ABACO KPI Overview**
4. Should see 19 KPI panels with data

### 3. Grafana URLs

| Component | URL |
|-----------|-----|
| **Grafana** | http://localhost:3001 |
| **Prometheus** | http://localhost:9090 |
| **Supabase SQL Editor** | https://supabase.com/dashboard/project/sddviizcgheusvwqpthm/sql |

---

## 📈 Next: Populate with Real Pipeline Data

After verifying the sample data works, populate with your real KPI data:

```bash
source .venv/bin/activate
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv
```

This will:
- ✅ Process your loan analytics data
- ✅ Calculate all 19 KPIs
- ✅ Write results to `monitoring.kpi_values` in Supabase
- ✅ Grafana will automatically refresh and show new data

---

## 📝 Configuration Files

### .env.monitoring (Updated)
```env
GRAFANA_ADMIN_PASSWORD=admin123
SUPABASE_URL=https://sddviizcgheusvwqpthm.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

### grafana/provisioning/datasources/supabase.yml (Updated)
- ✅ PostgreSQL host: `db.sddviizcgheusvwqpthm.supabase.co:5432`
- ✅ REST API endpoint: `https://sddviizcgheusvwqpthm.supabase.co/rest/v1`
- ✅ Authentication: Uses `SUPABASE_SERVICE_ROLE_KEY`

---

## 🔧 Troubleshooting

### Q: Grafana still shows "No data"
**A:** Run the SQL queries in Supabase UI to create the monitoring tables

### Q: "Data source is working" but no panels appear
**A:** Tables might not have data yet. Check:
```sql
SELECT COUNT(*) FROM monitoring.kpi_definitions;
SELECT COUNT(*) FROM monitoring.kpi_values;
```

Both should show `19` after running the SQL queries.

### Q: How to populate with real data?
**A:** 
```bash
python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv
```

### Q: Port 8501 (Streamlit) not accessible
**A:** Streamlit dashboard is separate from Grafana. To start it:
```bash
streamlit run streamlit_app.py
```

---

## 📚 Files Created

- ✅ `scripts/setup/check-supabase-data.sh` - Check which projects have data
- ✅ `scripts/setup/align-supabase-projects.sh` - Align Grafana to dev project
- ✅ `scripts/setup/create_monitoring_tables.py` - Python script for table creation
- ✅ `scripts/setup/create_tables_via_supabase_ui.md` - UI instructions
- ✅ `GRAFANA_DATA_SETUP.md` - This file

---

## 🎯 Summary

| Task | Status |
|------|--------|
| **Grafana installed** | ✅ Complete |
| **Supabase datasource configured** | ✅ Complete |
| **Projects aligned** | ✅ Complete |
| **Monitoring tables created** | ⏳ **Next: Create via Supabase UI** |
| **Sample data inserted** | ⏳ Will be done in step above |
| **Grafana showing data** | ⏳ Will complete after tables exist |
| **Real pipeline data** | ⏳ After verification |

---

## 🚀 Next Steps

1. **Copy the SQL queries above**
2. **Paste into:** https://supabase.com/dashboard/project/sddviizcgheusvwqpthm/sql
3. **Run each query** (Query 1 → 6 in order)
4. **Verify in Grafana:** http://localhost:3001
5. **Run pipeline:** `python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv`

**You're almost there!** 🎉

