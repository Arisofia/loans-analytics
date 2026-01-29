# G4.2 Deployment Guide - Historical KPIs Integration

**Version:** G4.2  
**Status:** Ship-Ready  
**Deployment Date:** TBD  
**Owner:** Data Engineering + Platform Team

---

## Executive Summary

G4.2 introduces production-ready historical KPI storage and integration for the multi-agent analytics system. This deployment includes:

1. **Supabase Schema Migration** - `historical_kpis` table with optimized indices
2. **Integration Tests** - Optional real Supabase validation suite
3. **GitHub Actions Workflow** - Automated integration testing
4. **Documentation** - Comprehensive schema and usage guides

**Deployment Risk:** LOW  
**Rollback Complexity:** LOW  
**Downtime Required:** NONE

---

## Pre-Deployment Checklist

### 1. Environment Verification

- [ ] **Supabase Project:** Accessible and healthy
- [ ] **Database Access:** Service role credentials configured
- [ ] **Backup Status:** Recent backup completed (< 24 hours)
- [ ] **Database Version:** PostgreSQL 14+ (Supabase default)
- [ ] **Available Disk Space:** > 10GB free for table + indices

### 2. Configuration Verification

- [ ] **Environment Variables Set:**
  - `SUPABASE_URL` - Project URL (e.g., https://xxx.supabase.co)
  - `SUPABASE_ANON_KEY` - Anonymous/service key
  - `SUPABASE_HISTORICAL_KPI_TABLE` - Table name (default: `historical_kpis`)

- [ ] **GitHub Secrets Configured (for integration tests):**
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`

### 3. Code Review & Testing

- [ ] **All Tests Passing:** 38/38 multi-agent tests GREEN
- [ ] **Code Review:** Approved by 2+ reviewers
- [ ] **Security Scan:** CodeQL clean (no critical/high alerts)
- [ ] **Linters:** Black, isort, ruff, flake8 passing
- [ ] **Type Checking:** Mypy passing

---

## Deployment Steps

### Stage 1: Database Schema Migration (Staging)

**Duration:** ~5 minutes  
**Risk:** LOW (non-destructive, creates new table)

1. **Connect to Staging Supabase:**
   ```bash
   # Via Supabase Dashboard: SQL Editor
   # OR via psql CLI:
   psql "postgresql://postgres:[PASSWORD]@[PROJECT].supabase.co:5432/postgres"
   ```

2. **Run Migration Script:**
   ```bash
   # Copy migration file
   cat supabase/migrations/20260128_create_historical_kpis_table.sql | pbcopy
   
   # Execute in Supabase SQL Editor or psql
   \i supabase/migrations/20260128_create_historical_kpis_table.sql
   ```

3. **Verify Table Creation:**
   ```sql
   -- Check table exists
   SELECT tablename FROM pg_tables WHERE tablename = 'historical_kpis';
   
   -- Check columns
   SELECT column_name, data_type, is_nullable 
   FROM information_schema.columns 
   WHERE table_name = 'historical_kpis'
   ORDER BY ordinal_position;
   
   -- Check indices
   SELECT indexname, indexdef 
   FROM pg_indexes 
   WHERE tablename = 'historical_kpis';
   
   -- Check constraints
   SELECT constraint_name, constraint_type 
   FROM information_schema.table_constraints 
   WHERE table_name = 'historical_kpis';
   ```

4. **Expected Output:**
   ```
   ✅ Table: historical_kpis created
   ✅ Columns: 8 columns (id, kpi_id, value, date, timestamp, created_at, updated_at, metadata)
   ✅ Indices: 2 indices (kpi_date, lookup)
   ✅ Constraints: Primary key on id, UNIQUE(kpi_id, date)
   ```

### Stage 2: Integration Test Validation (Staging)

**Duration:** ~2 minutes  
**Risk:** ZERO (read-only tests, isolated test data)

1. **Run Integration Tests Locally (Optional):**
   ```bash
   cd /path/to/abaco-loans-analytics
   
   # Set environment variables
   export RUN_REAL_SUPABASE_TESTS=1
   export SUPABASE_URL="https://xxx.supabase.co"
   export SUPABASE_ANON_KEY="eyJ..."
   
   # Run integration tests
   pytest tests/integration/test_historical_kpis_real.py -v --timeout=60
   ```

2. **Expected Output:**
   ```
   tests/integration/test_historical_kpis_real.py::test_supabase_backend_connection PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_provider_real_mode PASSED
   tests/integration/test_historical_kpis_real.py::test_fetch_historical_kpis_empty_range PASSED
   tests/integration/test_historical_kpis_real.py::test_fetch_historical_kpis_with_data PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_kpis_query_performance PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_context_provider_cache_behavior PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_trend_analysis_with_real_data PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_moving_average_with_real_data PASSED
   tests/integration/test_historical_kpis_real.py::test_historical_kpis_data_integrity PASSED
   
   =============================== 9 passed in 12.34s ===============================
   ```

3. **Run Integration Tests via GitHub Actions (Recommended):**
   ```bash
   # Navigate to GitHub Actions UI
   # Actions → Integration Tests (Optional) → Run workflow
   
   # Select branch: main (or staging)
   # Select test_target: all
   # Click "Run workflow"
   ```

### Stage 3: Smoke Test with Sample Data (Staging)

**Duration:** ~5 minutes  
**Risk:** LOW (test data only)

1. **Insert Sample KPI Data:**
   ```sql
   -- Insert test KPI records
   INSERT INTO historical_kpis (kpi_id, value, date, timestamp, metadata)
   VALUES 
       ('default_rate', 0.0245, '2026-01-01', '2026-01-01 00:00:00+00', '{"test": true}'),
       ('disbursements', 1500000.50, '2026-01-15', '2026-01-15 00:00:00+00', '{"test": true}'),
       ('portfolio_balance', 125000000.00, '2026-01-01', '2026-01-01 00:00:00+00', '{"test": true}');
   
   -- Verify insertion
   SELECT * FROM historical_kpis WHERE metadata->>'test' = 'true';
   ```

2. **Test HistoricalContextProvider in REAL Mode:**
   ```python
   from datetime import date
   from python.multi_agent.historical_context import HistoricalContextProvider
   from python.multi_agent.historical_backend_supabase import SupabaseHistoricalBackend
   
   # Initialize
   backend = SupabaseHistoricalBackend()
   provider = HistoricalContextProvider(mode="REAL", backend=backend)
   
   # Test query
   history = provider.get_kpi_history(
       kpi_id="default_rate",
       start_date=date(2026, 1, 1),
       end_date=date(2026, 1, 31)
   )
   
   print(f"✅ Retrieved {len(history)} KPI records")
   ```

3. **Clean Up Test Data:**
   ```sql
   DELETE FROM historical_kpis WHERE metadata->>'test' = 'true';
   ```

### Stage 4: Production Deployment

**Duration:** ~10 minutes  
**Risk:** LOW (same process as staging)

1. **Pre-Production Checkpoint:**
   - [ ] Staging tests passed
   - [ ] Integration tests passed
   - [ ] Sample data inserted and queried successfully
   - [ ] Performance SLOs met (< 500ms query time)
   - [ ] Rollback plan reviewed

2. **Deploy to Production:**
   ```bash
   # Connect to Production Supabase
   psql "postgresql://postgres:[PASSWORD]@[PROD-PROJECT].supabase.co:5432/postgres"
   
   # Run migration
   \i supabase/migrations/20260128_create_historical_kpis_table.sql
   
   # Verify (same verification queries as staging)
   ```

3. **Configure Production Secrets (GitHub Actions):**
   - Repository Settings → Secrets and variables → Actions
   - Add: `SUPABASE_URL` (production URL)
   - Add: `SUPABASE_ANON_KEY` (production key)

4. **Enable Row-Level Security (Optional):**
   ```sql
   -- Enable RLS for multi-tenant security
   ALTER TABLE historical_kpis ENABLE ROW LEVEL SECURITY;
   
   -- Add policies based on your authentication model
   -- See docs/historical-kpis-schema.md for examples
   ```

### Stage 5: Post-Deployment Validation

**Duration:** ~5 minutes  
**Risk:** ZERO (monitoring only)

1. **Monitor Query Performance:**
   ```sql
   -- Check query execution time
   SELECT 
       query,
       mean_exec_time,
       calls
   FROM pg_stat_statements
   WHERE query LIKE '%historical_kpis%'
   ORDER BY mean_exec_time DESC
   LIMIT 10;
   ```

2. **Verify Index Usage:**
   ```sql
   -- Check if indices are being used
   SELECT 
       indexname,
       idx_scan,
       idx_tup_read
   FROM pg_stat_user_indexes
   WHERE tablename = 'historical_kpis';
   ```

3. **Set Up Monitoring Alerts:**
   - **Query Performance:** Alert if p95 > 500ms
   - **Table Size:** Alert if > 80% disk capacity
   - **Failed Inserts:** Alert if > 1% error rate

---

## Rollback Procedures

### Scenario 1: Migration Failed (Table Creation Error)

**Impact:** NONE (table doesn't exist yet)  
**Action:** Fix migration script and re-run

```sql
-- Drop table if partially created
DROP TABLE IF EXISTS historical_kpis CASCADE;

-- Fix migration script
-- Re-run corrected migration
```

### Scenario 2: Performance Issues (Slow Queries)

**Impact:** MODERATE (degraded performance)  
**Action:** Optimize indices or rollback table

```sql
-- Option 1: Add missing indices
CREATE INDEX idx_missing ON historical_kpis(...);

-- Option 2: Disable table (stop writes)
ALTER TABLE historical_kpis RENAME TO historical_kpis_backup;

-- Option 3: Complete rollback
DROP TABLE historical_kpis CASCADE;
```

### Scenario 3: Data Corruption

**Impact:** HIGH (data integrity compromised)  
**Action:** Restore from backup

```bash
# Restore from most recent backup
pg_restore -U postgres -d abaco_loans -t historical_kpis /backups/latest.dump

# Verify data integrity
SELECT COUNT(*) FROM historical_kpis;
```

---

## Monitoring & Alerting

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|----------------|
| Query Response Time (p95) | < 200ms | > 500ms |
| Query Response Time (p99) | < 500ms | > 1s |
| Table Size | < 5GB | > 10GB |
| Insert Error Rate | < 0.1% | > 1% |
| Index Hit Rate | > 99% | < 95% |

### Monitoring Queries

```sql
-- Query performance dashboard
SELECT 
    DATE_TRUNC('hour', NOW()) AS hour,
    COUNT(*) AS query_count,
    AVG(mean_exec_time) AS avg_time_ms,
    MAX(max_exec_time) AS max_time_ms
FROM pg_stat_statements
WHERE query LIKE '%historical_kpis%'
GROUP BY hour
ORDER BY hour DESC;

-- Table growth rate
SELECT 
    pg_size_pretty(pg_total_relation_size('historical_kpis')) AS total_size,
    (SELECT COUNT(*) FROM historical_kpis) AS row_count,
    (pg_total_relation_size('historical_kpis')::NUMERIC / 
     NULLIF((SELECT COUNT(*) FROM historical_kpis), 0)) / 1024 AS avg_row_size_kb
;
```

---

## Support & Escalation

### Issue Tiers

**Tier 1 (Low):** Documentation questions, usage help  
**Contact:** Slack #data-engineering  
**SLA:** 24 hours

**Tier 2 (Medium):** Performance degradation, non-critical errors  
**Contact:** Slack #incidents + PagerDuty  
**SLA:** 4 hours

**Tier 3 (High):** Data corruption, service outage  
**Contact:** PagerDuty → On-call engineer  
**SLA:** 30 minutes

### Runbook Links

- [Historical KPIs Schema Documentation](./historical-kpis-schema.md)
- [HistoricalContextProvider API Reference](../python/multi_agent/README.md)
- [Integration Tests Guide](../tests/integration/README.md)

---

## Post-Deployment Tasks

### Immediate (Day 1)

- [ ] Monitor query performance for first 24 hours
- [ ] Verify no alerts triggered
- [ ] Document any issues encountered
- [ ] Update team on deployment status

### Short-Term (Week 1)

- [ ] Run integration tests daily
- [ ] Analyze query patterns
- [ ] Optimize indices if needed
- [ ] Train team on HistoricalContextProvider usage

### Long-Term (Month 1)

- [ ] Review data retention policy
- [ ] Evaluate partitioning need (if > 1M rows)
- [ ] Benchmark query performance trends
- [ ] Plan for G4.3 enhancements

---

## Appendix

### A. Migration Script

**File:** `supabase/migrations/20260128_create_historical_kpis_table.sql`  
**Size:** ~6KB  
**Estimated Execution Time:** < 10 seconds

### B. Integration Test Suite

**File:** `tests/integration/test_historical_kpis_real.py`  
**Tests:** 9 tests covering connectivity, queries, performance, caching  
**Execution Time:** ~15 seconds  
**Coverage:** HistoricalContextProvider + SupabaseHistoricalBackend

### C. GitHub Actions Workflow

**File:** `.github/workflows/integration-tests.yml`  
**Trigger:** Manual (workflow_dispatch) or Daily (2am UTC)  
**Duration:** ~3 minutes  
**Purpose:** Validate real Supabase integration

---

**Deployment Sign-Off:**

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Engineering Lead | | | |
| Platform Engineer | | | |
| Data Engineer | | | |
| QA Lead | | | |

---

**Deployment Log:**

| Date | Environment | Status | Notes |
|------|-------------|--------|-------|
| | Staging | | |
| | Production | | |

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-28  
**Next Review:** Post-deployment (Week 1)
