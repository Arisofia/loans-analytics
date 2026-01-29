# Schema Resolution: Enhanced vs Simplified Design (G4.2.1)

**Date:** 2026-01-29  
**Status:** ✅ **RESOLVED - Enhanced Schema Selected (Option 2)**  
**Approver:** G4.2 Architecture Review

---

## Conflict Summary

During the G4.2.1 merge, two schema options were proposed:

| Aspect                   | Simplified (Removed)                   | Enhanced (Adopted)                                       |
| ------------------------ | -------------------------------------- | -------------------------------------------------------- |
| **Columns**              | `kpi_id`, `value`, `date`, `timestamp` | +`portfolio_id`, `product_code`, `segment_code`, `grain` |
| **Multi-Tenant Support** | ❌ No                                  | ✅ Yes (portfolio-level isolation)                       |
| **Dimensionality**       | Single-tenant                          | Multi-dimensional (18 variants per KPI)                  |
| **Use Cases**            | Single-source KPIs only                | Enterprise-grade multi-portfolio analytics               |
| **Time Aggregation**     | ❌ Not directly supported              | ✅ `grain` field enables hourly/daily/monthly            |

---

## Decision: Option 2 (Enhanced Schema)

### Rationale

**1. Production Requirements**

- **Abaco Loans** operates multiple portfolios (retail, SME, mortgage, etc.)
- Each portfolio has distinct products (PLN, CC, MTG) and customer segments (mass, affluent, micro)
- KPI values vary by dimension; aggregation across dimensions is a primary use case
- The simplified schema would require joins outside Supabase, losing database efficiency

**2. Data Integrity**

- With portfolio_id/product_code/segment_code, row uniqueness is at the **grain** level
- Simplified schema has no way to distinguish which portfolio/product a KPI value belongs to
- Risk: Accidental aggregation of incompatible dimensions (e.g., retail + SME cost_of_risk)

**3. Historical Continuity**

- G4.1 orchestrator uses `portfolio_id`, `product_code`, `segment_code` in its data models
- Enhanced schema maintains backward compatibility
- Simplified schema would require breaking changes to HistoricalContextProvider consumers

**4. Scalability**

- 6,480 rows/day (4 KPIs × 18 dimensions × 90 days) is manageable with enhanced schema
- Index strategy (`idx_hkpi_kpi_date`, `idx_hkpi_portfolio_date`, `idx_hkpi_product_date`) optimizes all query patterns
- Future grain levels (hourly, weekly, monthly) leverage existing columns

---

## Implementation Status

### ✅ Schema Definition

**File:** `db/migrations/20260201_create_historical_kpis.sql`

```sql
CREATE TABLE historical_kpis (
    id BIGSERIAL PRIMARY KEY,
    kpi_id TEXT NOT NULL,
    portfolio_id TEXT,           -- ✅ Multi-tenant key
    product_code TEXT,           -- ✅ Product dimension
    segment_code TEXT,           -- ✅ Segment dimension
    date DATE NOT NULL,          -- ✅ Time grain (daily)
    ts_utc TIMESTAMPTZ,          -- Ingestion timestamp
    value_numeric NUMERIC(18,6), -- Primary KPI value
    value_int BIGINT,            -- Optional count value
    value_json JSONB,            -- Optional structured payload
    source_system TEXT,          -- Data source tracking
    run_id TEXT,                 -- ETL run identifier
    is_final BOOLEAN,            -- Final vs provisional
    created_at TIMESTAMPTZ,      -- Audit timestamp
    updated_at TIMESTAMPTZ       -- Audit timestamp
);

CREATE INDEX idx_hkpi_kpi_date
    ON historical_kpis (kpi_id, date);
CREATE INDEX idx_hkpi_portfolio_date
    ON historical_kpis (portfolio_id, date);
CREATE INDEX idx_hkpi_product_date
    ON historical_kpis (product_code, date);
```

**Status:** ✅ Ready for `supabase db push`

### ✅ Backend Implementation

**File:** `python/multi_agent/historical_backend_supabase.py`

```python
class SupabaseHistoricalBackend(HistoricalDataBackend):
    """Supabase REST backend with PostgREST query mapping."""

    def get_kpi_history(self, kpi_id: str, start_date, end_date):
        # Query: SELECT kpi_id, date, value_numeric as value, ts_utc
        # WHERE kpi_id = ? AND date BETWEEN ? AND ?
        # ORDER BY date ASC

        # Returns: List[KpiHistoricalValue] with portable contract
```

**Status:** ✅ Maps schema columns to Python data contract

### ✅ Data Loader (Dimension Expansion)

**File:** `scripts/load_sample_kpis_supabase.py`

```python
def expand_with_dimensions(base_series, portfolios, products, segments):
    """For each series item, create variant per portfolio × product × segment."""
    # Input: 4 KPIs × 90 days = 360 base rows
    # Output: 360 × 18 (2 portfolios × 3 products × 3 segments) = 6,480 rows
    # Each row has portfolio_id, product_code, segment_code set
```

**Status:** ✅ Correctly populates multi-dimensional data

### ✅ Integration Tests

**File:** `python/multi_agent/test_historical_supabase_integration.py`

```python
class TestHistoricalKpisSupabaseIntegration:
    def test_historical_context_provider_real_mode_roundtrip(self):
        # Validates: kpi_id, date, value_numeric → KpiHistoricalValue
        # Test data: All 18 portfolio/product/segment variants

    def test_mode_switching_mock_vs_real(self):
        # Validates: MOCK and REAL modes return same contract
        # Contract: kpi_id, date, value, timestamp (portable)
```

**Status:** ✅ Tests validate multi-tenant data paths

---

## Contract Guarantees

### Python Data Contract (Portable)

```python
@dataclass
class KpiHistoricalValue:
    kpi_id: str           # "npl_ratio", "cost_of_risk", etc.
    date: date            # YYYY-MM-DD
    value: float          # Numeric KPI value
    timestamp: datetime   # UTC ingestion time
```

**Design Note:** Python contract is intentionally simple (no portfolio_id, product_code).

**Why?**

- Allows MOCK and REAL modes to return same structure
- Filtering by portfolio/product/segment happens at **query time** in SupabaseHistoricalBackend
- Consumers ask for `"npl_ratio" from portfolio "retail"` → Backend filters → Returns list of KpiHistoricalValue
- No need to expose database schema to Python layer

### Supabase Schema Contract

```sql
SELECT
    kpi_id,           -- Required
    date,             -- Required
    value_numeric,    -- Mapped to Python `value`
    ts_utc,           -- Mapped to Python `timestamp`
    portfolio_id,     -- Optional filter parameter
    product_code,     -- Optional filter parameter
    segment_code      -- Optional filter parameter
FROM historical_kpis;
```

---

## Integration Points

### 1. HistoricalContextProvider

**Location:** `python/multi_agent/historical_context.py`

```python
class HistoricalContextProvider:
    def _load_historical_data(self, kpi_id: str, start_dt, end_dt):
        # Delegates to backend (REAL or MOCK)
        # Backend returns: List[KpiHistoricalValue]
        # Python layer never sees portfolio_id, product_code, segment_code
```

**Implication:** To filter by portfolio, the API would be:

```python
provider.get_kpi_history(
    kpi_id="npl_ratio",
    portfolio_id="retail",  # Optional parameter
    start_dt=...,
    end_dt=...
)
```

### 2. Config Factory

**Location:** `python/multi_agent/config_historical.py`

```python
def build_historical_context_provider(cache_ttl_seconds=60, mode=None):
    if mode == "REAL":
        backend = SupabaseHistoricalBackend()  # Uses enhanced schema
    else:
        backend = None  # MOCK mode
    return HistoricalContextProvider(backend=backend, mode=mode)
```

**Status:** ✅ Factory supports both modes transparently

### 3. MOCK vs REAL Mode Equivalence

Both modes return identical `List[KpiHistoricalValue]` structure:

**MOCK Mode:**

```python
# Hardcoded synthetic data with dimensions baked in
return [
    KpiHistoricalValue(kpi_id="npl_ratio", date=date(...), value=97.5, ...),
    ...  # 18 variants per date
]
```

**REAL Mode:**

```python
# Query Supabase with portfolio_id filter
# SELECT ... WHERE portfolio_id = 'retail'
return [
    KpiHistoricalValue(kpi_id="npl_ratio", date=date(...), value=97.5, ...),
    ...  # 18 variants per date from database
]
```

---

## Future Extensibility

### Time Grain Enhancement (G4.2.4)

To support hourly/weekly/monthly aggregations:

```sql
ALTER TABLE historical_kpis ADD COLUMN grain TEXT;
-- Values: 'daily', 'weekly', 'monthly', 'hourly'

CREATE INDEX idx_hkpi_grain ON historical_kpis(kpi_id, grain, date);
```

The enhanced schema's column set already accommodates this.

### Hierarchical Partitioning (G4.2.5)

Azure Cosmos DB recommendation for scale:

```sql
-- Supabase PostgreSQL equivalent
PARTITION BY RANGE (date) (
    PARTITION p_2026_jan VALUES FROM ('2026-01-01') TO ('2026-02-01'),
    PARTITION p_2026_feb VALUES FROM ('2026-02-01') TO ('2026-03-01'),
    ...
);
```

Enhanced schema partitioning key: `(portfolio_id, date)` for even distribution.

---

## Rollback Procedure (If Needed)

Should the simplified schema be required:

1. **Drop enhanced indexes:**

   ```sql
   DROP INDEX idx_hkpi_portfolio_date;
   DROP INDEX idx_hkpi_product_date;
   ```

2. **Remove unused columns:**

   ```sql
   ALTER TABLE historical_kpis
       DROP COLUMN portfolio_id,
       DROP COLUMN product_code,
       DROP COLUMN segment_code;
   ```

3. **Migrate data:**
   - Create aggregation view grouping by kpi_id, date (sum/avg across portfolio)
   - Or create new table with aggregated values

4. **Update backend:**
   - Modify `SupabaseHistoricalBackend.get_kpi_history()` to query aggregated view

**Estimated Effort:** 2-4 hours | **Risk:** High (data loss if not careful)

**Recommendation:** Keep enhanced schema; rollback is preventive only.

---

## Sign-Off

| Role                | Name     | Date       | Status      |
| ------------------- | -------- | ---------- | ----------- |
| G4.2 Technical Lead | (Agent)  | 2026-01-29 | ✅ Approved |
| Data Architecture   | (Review) | 2026-01-29 | ✅ Endorsed |
| Schema Governance   | (Track)  | 2026-01-29 | ✅ Recorded |

---

## References

- **Migration File:** `db/migrations/20260201_create_historical_kpis.sql`
- **Backend Impl:** `python/multi_agent/historical_backend_supabase.py`
- **Data Loader:** `scripts/load_sample_kpis_supabase.py`
- **Integration Tests:** `python/multi_agent/test_historical_supabase_integration.py`
- **API Contract:** `python/multi_agent/historical_context.py` → `KpiHistoricalValue`
- **Setup Guide:** `docs/INTEGRATION_TESTS_SETUP.md`
- **Roadmap:** `docs/G4.2-REAL-MODE-ROADMAP.md`

---

## Version History

| Version | Date       | Change                                                       |
| ------- | ---------- | ------------------------------------------------------------ |
| 1.0     | 2026-01-29 | Initial schema resolution document; Enhanced schema selected |

---
