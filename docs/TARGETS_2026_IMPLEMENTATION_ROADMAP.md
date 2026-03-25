# 2026 Portfolio Targets — Implementation Roadmap

## ✅ Completed

### Infrastructure (Commit: 161451c76)

- ✅ **TargetLoader Class** (`backend/python/kpis/target_loader.py`)
  - Hardcoded 2026 targets: Jan $8.5M → Dec $12M
  - Methods for target retrieval, variance calculation, DataFrame operations
  - Variance status: ON_TRACK (≥95%), MONITOR (90-95%), AT_RISK (<90%), EXCEEDED, NO_DATA
  
- ✅ **Database Schema** (`db/migrations/002_create_kpi_targets_table.sql`)
  - Table `kpi_targets_2026` with all 12 months pre-seeded
  - View `kpi_targets_with_variance` for automatic variance calculation
  - Row Level Security enabled for multi-tenant safety
  
- ✅ **Pipeline Configuration** (`config/pipeline.yml`)
  - Google Sheets integration
  - Targets ingestion config (source, worksheet, columns, persistence)
  
- ✅ **Documentation** (`docs/TARGETS_2026.md`)
  - Target plan table (Jan-Dec with growth analysis)
  - System architecture overview
  - SQL/Python usage examples
  
---

## 🚀 RECOMMENDED: What to Add Next

### **PHASE 1: Database & Basic Reporting** (1-2 hours)

#### 1.1 Run Database Migration
```bash
# Apply SQL migration to create tables
export DATABASE_URL="postgresql://user:pass@host/db"
psql -f db/migrations/002_create_kpi_targets_table.sql
```

**Verify:**
```sql
-- Check tables created
SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'kpi%';

-- Verify seed data (12 rows Jan-Dec)
SELECT month_name, portfolio_target FROM kpi_targets_2026 ORDER BY month_number;
```

#### 1.2 Create Test Report (Python Script)
File: `scripts/reports/monthly_targets_report.py`

```python
#!/usr/bin/env python3
"""Monthly targets vs actuals report."""

import os
import sys
from decimal import Decimal
import psycopg
import pandas as pd
from backend.python.kpis.target_loader import TargetLoader

def generate_report(report_date: str):
    """Generate monthly variance report (date format: YYYY-MM-DD)."""
    loader = TargetLoader()
    
    with psycopg.connect(os.getenv("DATABASE_URL")) as conn:
        with conn.cursor(row_factory=dict_factory) as cur:
            # Get actuals
            cur.execute("""
                SELECT 
                    EXTRACT(MONTH FROM date) as month_num,
                    TO_CHAR(date, 'Mon') as month_name,
                    ROUND(SUM(principal_balance)::numeric, 2) as actual_aum
                FROM loan_transactions
                WHERE date <= %s AND status != 'CLOSED'
                GROUP BY EXTRACT(MONTH FROM date), TO_CHAR(date, 'Mon')
                ORDER BY month_num
            """, (report_date,))
            actuals = {row['month_name']: Decimal(str(row['actual_aum'])) for row in cur.fetchall()}
    
    # Calculate variances
    comparison = loader.compare_actuals_vs_targets(actuals)
    
    # Display report
    print("=" * 80)
    print(f"PORTFOLIO TARGETS VARIANCE REPORT - {report_date}")
    print("=" * 80)
    print(f"\n{'Month':<8} {'Target':>15} {'Actual':>15} {'Variance $':>15} {'%':>8} {'Status':<12}")
    print("-" * 80)
    
    for _, row in comparison.iterrows():
        month = row['month_name']
        target = row['portfolio_target']
        actual = row['actual_portfolio'] or 0
        var_amt = row.get('variance_amount', 0)
        var_pct = row.get('variance_pct', 0)
        status = row.get('status', 'NO_DATA')
        
        print(f"{month:<8} ${target:>14,.0f} ${actual:>14,.0f} ${var_amt:>14,.0f} {var_pct:>7.1f}% {status:<12}")
    
    print("=" * 80)

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    report_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    generate_report(report_date)
```

**usage:**
```bash
python scripts/reports/monthly_targets_report.py 2026-01-31
```

---

### **PHASE 2: API Endpoints** (3-4 hours)

#### 2.1 Create Targets API Service
File: `backend/python/apps/analytics/api/targets_service.py`

```python
"""API service for portfolio targets and variance tracking."""

from typing import dict
from decimal import Decimal
import psycopg
from fastapi import HTTPException
from pydantic import BaseModel
from backend.python.kpis.target_loader import TargetLoader

class MonthlyTargetResponse(BaseModel):
    month_number: int
    month_name: str
    portfolio_target: float
    npl_target_pct: float
    default_rate_target_pct: float

class VarianceResponse(BaseModel):
    month_name: str
    portfolio_target: float
    actual_portfolio: float | None
    variance_amount: float
    variance_pct: float
    status: str  # ON_TRACK, MONITOR, AT_RISK, EXCEEDED, NO_DATA

class TargetsService:
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.loader = TargetLoader()
    
    async def get_all_targets(self) -> list[MonthlyTargetResponse]:
        """Get all 2026 targets."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_factory) as cur:
                cur.execute("SELECT * FROM kpi_targets_2026 ORDER BY month_number")
                return [MonthlyTargetResponse(**row) for row in cur.fetchall()]
    
    async def get_target(self, month: int) -> MonthlyTargetResponse:
        """Get target for specific month (1-12)."""
        if not 1 <= month <= 12:
            raise HTTPException(status_code=400, detail="Month must be 1-12")
        
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_factory) as cur:
                cur.execute("SELECT * FROM kpi_targets_2026 WHERE month_number = %s", (month,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail=f"No target for month {month}")
                return MonthlyTargetResponse(**row)
    
    async def get_variance(self, month: int | None = None) -> list[VarianceResponse] | VarianceResponse:
        """Get variance data (all months or specific month)."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_factory) as cur:
                if month:
                    cur.execute("SELECT * FROM kpi_targets_with_variance WHERE month_number = %s", (month,))
                    row = cur.fetchone()
                    return VarianceResponse(**row) if row else []
                else:
                    cur.execute("SELECT * FROM kpi_targets_with_variance ORDER BY month_number")
                    return [VarianceResponse(**row) for row in cur.fetchall()]
    
    async def get_summary(self) -> dict:
        """Get summary statistics."""
        with psycopg.connect(self.db_url) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_factory) as cur:
                cur.execute("""
                    SELECT
                      COUNT(*) as months_tracked,
                      COUNT(CASE WHEN actual_portfolio IS NOT NULL THEN 1 END) as months_with_actuals,
                      SUM(portfolio_target) as total_target,
                      SUM(actual_portfolio) as total_actual,
                      COUNT(CASE WHEN status = 'ON_TRACK' THEN 1 END) as on_track_count,
                      COUNT(CASE WHEN status = 'AT_RISK' THEN 1 END) as at_risk_count
                    FROM kpi_targets_with_variance
                """)
                return cur.fetchone()
```

#### 2.2 Add FastAPI Routes
File: `backend/python/apps/analytics/api/main.py` (update)

```python
# Add to FastAPI app

from fastapi import APIRouter
from backend.python.apps.analytics.api.targets_service import TargetsService

router = APIRouter(prefix="/api/targets", tags=["targets"])
targets_service = TargetsService(os.getenv("DATABASE_URL"))

@router.get("/")
async def list_targets():
    """List all 2026 portfolio targets."""
    return await targets_service.get_all_targets()

@router.get("/{month}")
async def get_month_target(month: int):
    """Get target for specific month (1-12)."""
    return await targets_service.get_target(month)

@router.get("/variance/all")
async def list_variance():
    """List variance for all months (actual vs target)."""
    return await targets_service.get_variance()

@router.get("/variance/{month}")
async def get_month_variance(month: int):
    """Get variance for specific month."""
    return await targets_service.get_variance(month)

@router.get("/summary")
async def get_targets_summary():
    """Get summary statistics (on-track count, target progress, etc)."""
    return await targets_service.get_summary()

# Include router
app.include_router(router)
```

**Test endpoints:**
```bash
curl http://localhost:8000/api/targets/
curl http://localhost:8000/api/targets/1
curl http://localhost:8000/api/targets/variance/all
curl http://localhost:8000/api/targets/summary
```

---

### **PHASE 3: Grafana Dashboard** (2-3 hours)

#### 3.1 Create Grafana Dashboard JSON
File: `config/grafana/dashboards/targets_2026.json`

Dashboard includes:
- **Actual vs Target**: Dual-line chart (actual AUM vs 2026 target line)
- **Monthly Variance**: Bar chart (-5% to +5% band, show variance %)
- **Achievement Gauge**: Overall % of Dec target achieved (0-100%)
- **Months Summary Table**: Month | Target | Actual | Variance | Status
- **Risk Alerts**: List months with status = AT_RISK (highlighted red)
- **Growth Analysis**: Month-over-month growth rate vs plan

#### 3.2 Create Datasource Config
File: `config/grafana/provisioning/datasources/supabase.yml`

```yaml
apiVersion: 1

datasources:
  - name: "Supabase PostgreSQL"
    type: "postgres"
    access: "proxy"
    url: "${SUPABASE_DB_HOST}:5432"
    database: "${SUPABASE_DB_NAME}"
    user: "${SUPABASE_DB_USER}"
    secureJsonData:
      password: "${SUPABASE_DB_PASSWORD}"
    isDefault: true
```

#### 3.3 Provision via Script
File: `scripts/monitoring/provision_targets_dashboard.py`

---

### **PHASE 4: CI/CD Integration** (1-2 hours)

#### 4.1 Add Target Validation to Tests
File: `tests/integration/test_targets_validation.py`

```python
import pytest
from decimal import Decimal
from backend.python.kpis.target_loader import TargetLoader

class TestTargetValidation:
    """Validate 2026 targets are loaded and accessible."""
    
    def test_targets_hardcoded(self):
        """Verify hardcoded targets exist."""
        loader = TargetLoader()
        assert loader.get_target(1) == Decimal("8500000")  # Jan
        assert loader.get_target(12) == Decimal("12000000")  # Dec
    
    def test_variance_status_mapping(self):
        """Verify variance status calculation."""
        loader = TargetLoader()
        
        # ON_TRACK test
        result = loader.calculate_variance(Decimal("8550000"), Decimal("8500000"))
        assert result["status"] == "ON_TRACK"  # +0.59% (within ±5%)
        
        # AT_RISK test
        result = loader.calculate_variance(Decimal("8000000"), Decimal("8500000"))
        assert result["status"] == "AT_RISK"  # -5.88% (below -5%)
        
        # EXCEEDED test
        result = loader.calculate_variance(Decimal("9000000"), Decimal("8500000"))
        assert result["status"] == "EXCEEDED"  # +5.88% (above +5%)
```

#### 4.2 CI Workflow for Monthly Validation
File: `.github/workflows/validate-monthly-targets.yml`

```yaml
name: Monthly Target Validation

on:
  schedule:
    - cron: '0 5 1 * *'  # First day of month at 5 AM
  workflow_dispatch:

jobs:
  validate-targets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run targets report
        env:
          DATABASE_URL: ${{ secrets.DATA BASE_URL }}
        run: |
          python scripts/reports/monthly_targets_report.py
      
      - name: Check for AT_RISK status
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          python -c "
          import psycopg
          import os
          conn = psycopg.connect(os.getenv('DATABASE_URL'))
          cur = conn.cursor()
          cur.execute('SELECT COUNT(*) FROM kpi_targets_with_variance WHERE status = \\'AT_RISK\\'')
          at_risk = cur.fetchone()[0]
          if at_risk > 0:
              print(f'::warning::Portfolio is AT_RISK for {at_risk} month(s)')
          "
```

---

## 📋 Detailed Implementation Checklist

### Tier 1: Essential (Do First)

- [ ] **Run Database Migration**
  - Command: `psql -f db/migrations/002_create_kpi_targets_table.sql`
  - Verify: 12 rows in `kpi_targets_2026`, views created

- [ ] **Add Monthly Report Script** (`scripts/reports/monthly_targets_report.py`)
  - Queries actual AUM from database
  - Calculates variances using TargetLoader
  - Prints console output
  - Test with: `python scripts/reports/monthly_targets_report.py 2026-01-31`

- [ ] **Create Unit Tests** 
  - File: `tests/unit/kpis/test_target_loader.py`
  - Test target retrieval, variance calculation, status mapping
  - Run: `pytest tests/unit/kpis/test_target_loader.py -v`

### Tier 2: High Value (Do Second)

- [ ] **Create API Service** (`backend/python/apps/analytics/api/targets_service.py`)
  - Services for targets, variance, summary
  - Pydantic models for responses

- [ ] **Add API Routes**
  - `/api/targets/` — List all
  - `/api/targets/{month}` — Get specific month
  - `/api/targets/variance/all` — All variances
  - `/api/targets/summary` — Summary stats

- [ ] **Create Basic Grafana Dashboard**
  - Actual vs Target line chart
  - Variance bar chart
  - Summary table
  - At-risk alerts

### Tier 3: Nice to Have (Do Last)

- [ ] **Advanced CI/CD**
  - Monthly target validation workflow
  - Auto-alerts for AT_RISK status
  - Report publishing to GitHub summaries

- [ ] **Enhanced Features**
  - Target adjustment endpoint (POST /api/targets/{month})
  - Historical target comparison (2024, 2025 vs 2026)
  - Variance forecasting (project trajectory)
  - Export variance report as PDF

---

## 🎯 What Each Component Does

| Component | Purpose | When to Use |
|-----------|---------|------------|
| **TargetLoader** | In-memory target management & variance calculation | Python scripts, API services, batch jobs |
| **kpi_targets_2026 Table** | Persistent target storage | Query actuals, audit trail, reporting |
| **kpi_targets_with_variance View** | Real-time variance calculation | Dashboards, reports, alerts |
| **Monthly Report Script** | Human-readable variance summary | End-of-month reviews, stakeholder reports |
| **API Service** | Programmatic targets access | Dashboards, mobile apps, integrations |
| **Grafana Dashboard** | Visual target tracking | Product team reviews, leadership visibility |

---

## 📞 Questions to Answer

Before implementing, confirm:

1. **Who monitors targets?** (Product, Finance, Leadership?)
   - Determines dashboard access, alert recipients

2. **What's "actual AUM"?** (Total principal balance? Disbursed only?)
   - Affects which SQL query to use in report script

3. **Monthly vs. End-of-Month reporting?**
   - Do variance checks daily? Weekly? Only at month-end?

4. **Alert thresholds correct?**
   - Currently: ON_TRACK ≥95%, AT_RISK <90%
   - OK or should be tighter (e.g., ≥98%, <85%)?

5. **Google Sheets as source of truth?**
   - Should targets be editable via API?
   - Or always loaded from hardcoded + Google Sheets?

---

## 🚀 Quick Start Order

1. **Today**: Run migration, test report script → Verify data integrity
2. **Tomorrow**: Create API service & routes → Enable programmatic access
3. **This Week**: Build Grafana dashboard → Enable visual tracking
4. **Next Week**: Set up CI/CD alerts → Automate target monitoring

---

## 📚 Related Documentation

- `docs/TARGETS_2026.md` — Details of system architecture & usage
- `docs/GOOGLE_SHEETS_SETUP.md` — Google Sheets integration guide
- `config/pipeline.yml` — Targets ingestion configuration
- `backend/python/kpis/engine.py` — KPI calculation engine in which to integrate targets

---

**Next Question:** Which Tier should we start with? (Tier 1 is ~2 hours, Tier 1+2 is ~6 hours total)
