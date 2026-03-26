# KPI SSOT Registry & Consolidation Framework

**Effective Date**: 2026-03-19  
**Status**: Foundation Document for Workstream 4 (KPI SSOT Consolidation)  
**Purpose**: Establish single source of truth for all KPI definitions and prevent duplicate/conflicting implementations

---

## Executive Summary

This document establishes the KPI SSOT (Single Source of Truth) Registry—a unified, version-controlled, audit-logged system for defining, calculating, and governing KPIs across Loans Loans Analytics.

**Problem Solved**:
- ❌ Multiple implementations of the same KPI across 14+ Python modules
- ❌ No centralized change control for KPI formula updates
- ❌ Inconsistent rounding, denominators, date boundaries between implementations
- ❌ No audit trail linking data → formula → output → dashboard
- ❌ Risk: Dashboard KPI differs from API KPI differs from batch export

**Solution**:
- ✅ Single canonical YAML registry (`config/kpis/kpi_definitions.yaml`)
- ✅ All implementations must reference registry (no hardcoded formulas)
- ✅ Change control: PRs must update registry + formula engine + tests
- ✅ Audit trail: Every KPI calculation logs formula version + source data + actor
- ✅ Lineage: Full trace from raw data column → normalized → calculated KPI

---

## 1. KPI SSOT Architecture

### 1.1 Three-Layer Model

```
Layer 1: DEFINITIONS (config/kpis/kpi_definitions.yaml)
├─ Canonical formula for each KPI
├─ Unit, description, thresholds
├─ Owner, calculation frequency, dependencies
└─ Change log with version history

Layer 2: ENGINE (backend/python/kpis/formula_engine.py)
├─ Parser: Converts formula text → executable code
├─ Executor: Runs formula on DataFrame with precision guards
├─ Auditor: Logs formula invocation + timestamp + actor
└─ Validator: Checks result sanity (bounds, NaN, etc.)

Layer 3: CONSUMERS (APIs, Dashboards, Batch Exports)
├─ Must query engine, not hardcode formulas
├─ All report: KPI name + formula version + execution time
└─ Fail if engine returns stale/uncalculated value
```

### 1.2 Registry Structure

```yaml
# config/kpis/kpi_definitions.yaml (single source)
kpi:
  portfolio_kpis:
    total_outstanding_balance:
      formula: "SUM(outstanding_balance WHERE status != 'closed')"
      unit: "USD"                              # Canonical unit
      grain: "portfolio"                       # Aggregation level
      calculation_frequency: "daily"           # When it can refresh
      owner: "@data-engineering"               # Who maintains
      dependencies:                            # Data it needs
        - "outstanding_balance"
        - "status"
      thresholds:                              # Alert bounds
        warning: 10_000_000
        critical: 50_000_000
      version: "1.2"                           # Formula version
      changed_by: "PR#1234"                    # Audit trail
      version_date: "2026-03-19"
      notes: "Excludes closed loans"
      alternative_names:                       # Backwards compat
        - "portfolio_balance"
        - "outstanding_principal"
```

---

## 2. The Problem: Current Fragmentation

### 2.1 Multiple Implementations (Before Consolidation)

**Example: PAR-30 Rate**

```python
# ❌ Implementation 1: backend/python/kpis/advanced_risk.py
def calculate_par_30(df):
    total = df[df['status'] != 'closed']['outstanding'].sum()
    par = df[df['dpd'] >= 30]['outstanding'].sum()
    return (par / total * 100) if total > 0 else 0

# ❌ Implementation 2: backend/python/kpis/portfolio_analytics.py
def par_30_ratio(loans_df):
    par_amount = loans_df[loans_df['days_past_due'] >=30]['balance'].sum()
    total_balance = loans_df['balance'].sum()
    return round((par_amount / total_balance) * 100, 2)

# ❌ Implementation 3: SQL View in Postgres
CREATE VIEW analytics.par_30 AS
SELECT 
  SUM(CASE WHEN dpd >= 30 THEN outstanding_balance ELSE 0 END) / 
  SUM(outstanding_balance) * 100
FROM public.loan_month;

# ❌ Implementation 4: Frontend dashboard (JavaScript)
const par30 = useMemo(() => {
  const par = loans.filter(l => l.dpd >= 30).reduce((s, l) => s + l.outstandingBalance, 0);
  const total = loans.reduce((s, l) => s + l.outstandingBalance, 0);
  return (par / total * 100).toFixed(2);
}, [loans]);
```

**Problems**:
1. **Column naming**: Implementation 1 uses `outstanding`, Impl 2 uses `balance`, Impl 3 uses `outstanding_balance`
2. **Rounding**: Impl 2 rounds to 2 decimals, Impl 4 uses 2 decimals with toFixed(), others don't round
3. **Boundaries**: Impl 1 excludes closed loans, others don't specify
4. **Division by zero**: Implementation 1 checks, others don't
5. **Status filtering**: Impl 1 checks status, others filter only on DPD

**Result**: Dashboard shows 3.50%, API shows 3.49%, Batch export shows 3.5%, SQL view shows 3.503%.

### 2.2 Impact

| Risk | Impact | Example |
|------|--------|---------|
| **Reporting discrepancy** | Board receives different KPI values from different sources | "Risk dashboard shows 5% NPL but monthly report shows 4.8%" |
| **Audit failure** | Cannot trace which formula was used for a specific KPI value | "Auditors ask for formula used in March PAR-30 value" |
| **Change chaos** | Updating formula requires finding/updating 4+ locations | 15% of KPI bug fixes don't get deployed everywhere |
| **Slow debugging** | Product teams debug KPI issues by comparing 4 implementations | Average 4-hour debugging session for a 5-minute bug |

---

## 3. SSOT Registry: Canonical Source

### 3.1 Registry File (`config/kpis/kpi_definitions.yaml`)

Location: `config/kpis/kpi_definitions.yaml` (version-controlled, code review required)

**Governance**:
- All KPI changes must update this file
- PR must include: formula change + unit tests + impact analysis
- Merge requires: 2 code reviews + data engineering sign-off
- Tag release (e.g., `kpi-v1.3.0`) when KPI definitions change

### 3.2 Registry Metadata

Each KPI entry includes:

```yaml
kpi_name:
  formula: "Executable formula string"         # REQUIRED: No natural language
  unit: "USD|percentage|count|bps|etc"         # REQUIRED: Prevents unit confusion
  grain: "portfolio|segment|loan|daily"        # REQUIRED: Aggregation level
  calculation_frequency: "real-time|daily|monthly|quarterly" # REQUIRED
  owner: "@team-name"                          # REQUIRED: Who maintains
  dependencies:                                 # REQUIRED: Source columns
    - "column_name"
    - "column_name"
  thresholds:                                   # OPTIONAL: Alert bounds
    warning: 5.0
    critical: 10.0
  version: "1.2"                               # REQUIRED: Incremented on change
  changed_by: "PR#1234"                        # REQUIRED: Audit trail
  version_date: "YYYY-MM-DD"                   # REQUIRED: When changed
  rollback_safe: true                          # REQUIRED: Can dashboard revert?
  alternative_names:                           # OPTIONAL: Backwards compatibility
    - "old_kpi_name"
    - "legacy_name"
  notes: "Business definition and edge cases"  # Operational notes
  examples:                                     # Test data
    input: { outstanding_balance: [100, 200], dpd: [0, 35], status: ["active", "active"] }
    expected_output: 50.0
```

---

## 4. Formula Engine: Single Execution

### 4.1 API Contract

All KPI implementations must use this interface:

```python
from backend.python.kpis.formula_engine import KPIFormulaEngine

# Usage (same everywhere)
engine = KPIFormulaEngine(
    df=loan_data,
    kpi_name="par_30",                    # References registry
    registry_version="1.2",                # Ensures consistency
    actor="api_server",                    # Audit trail
    run_id="20260319_143022"               # Batch identifier
)

par_30_value = engine.calculate()  # Returns (value, context)
# Result: {
#   "value": 3.50,
#   "unit": "percentage",
#   "formula_version": "1.2",
#   "execution_time_ms": 145,
#   "data_rows": 5218,
#   "actor": "api_server",
#   "timestamp": "2026-03-19T14:30:22Z"
# }
```

### 4.2 Engine Features

**Precision Preservation** (Workstream 3 integration)
```python
# Uses Decimal arithmetic, no float drift
# Validates column types (Int64 for monetary)
# Follows ROUND_HALF_UP always
```

**Audit Trail**
```python
# Every calculation logged:
{
  "timestamp": "2026-03-19T14:30:22.123Z",
  "kpi_name": "par_30",
  "formula_version": "1.2",
  "actor": "api_server",
  "run_id": "20260319_143022",
  "result": 3.50,
  "data_rows": 5218,
  "columns_used": ["outstanding_balance", "dpd", "status"],
  "execution_ms": 145,
  "status": "success"
}
```

**Validation**
```python
# Fails if:
# 1. Formula references undefined column
# 2. Result is NaN or infinite
# 3. Result outside reasonable thresholds (e.g., PAR > 100%)
# 4. Data rows < minimum (empty data check)
```

---

## 5. Consolidation Strategy

### 5.1 Phases

**Phase 1: Registry Definition (Done)** ✅
- loc: `config/kpis/kpi_definitions.yaml`
- All KPIs defined with formulas, units, dependencies
- All thresholds, examples, backward-compat names

**Phase 2: Formula Engine (In Progress)**
- loc: `backend/python/kpis/formula_engine.py`
- Executor that reads registry, calculates KPIs, logs audit trail
- Type validation, bounds checking, precision guards
- Expected completion: 1-2 weeks

**Phase 3: Implementation Consolidation (Planned)**
- Migrate all 14+ module KPI functions to use engine
- Remove duplicate implementations
- Test each against historical data for precision match
- Expected completion: 2-3 weeks

**Phase 4: Consumer Migration (Planned)**
- Update APIs to use engine results
- Update dashboards to query engine
- Update batch exports to use engine
- Expected completion: 1 week

**Phase 5: Sunsetting (Planned)**
- Deprecate old KPI functions
- Remove dead code after 6-month grace period
- Expected completion: 6 months

### 5.2 Testing Strategy

**Unit Tests**
```python
# tests/unit/test_kpi_par_30.py
def test_par_30_matches_definition():
    """PAR-30 matches config/kpis/kpi_definitions.yaml"""
    df = pd.DataFrame({
        'outstanding_balance': [100, 200, 300],
        'dpd': [0, 35, 45],
        'status': ['active', 'active', 'active']
    })
    
    expected = (500/600) * 100  # (200+300)/600
    actual = engine.calculate(df, 'par_30')
    assert_precision_equal(actual, expected, decimals=2)
```

**Regression Tests**
```python
# For each KPI, verify against historical data
# Example: "PAR-30 on 2026-02-28 should match original calculation"
def test_par_30_historical():
    df = load_historical_data('2026-02-28')
    result = engine.calculate(df, 'par_30')
    assert_close_to(result, expected_value=2.45, tolerance=0.01)
```

**Integration Tests**
```python
# Verify engine → API → dashboard end-to-end
def test_par_30_api_to_dashboard():
    api_response = requests.get('/api/kpis/par_30')
    assert api_response['formula_version'] == engine.registry_version
    assert api_response['timestamp'] is not None
    assert api_response['actor'] is not None
```

---

## 6. Governance & Change Control

### 6.1 KPI Formula Change Workflow

1. **Issue Creation**
   - Issue title: "KPI Change: [KPI name] - [reason]"
   - Label: `kpi-change`
   - Include: Current formula, proposed change, rationale, impact estimate

2. **PR Requirements**
   ```
   PR Title: "KPI: Update [name] formula to [summary]"
   
   Files Changed:
     - config/kpis/kpi_definitions.yaml (update formula + version + date)
     - backend/python/kpis/test_kpi_[name].py (update unit tests)
     - docs/KPI_CATALOG.md (update documentation)
   
   PR Checklist:
     - [ ] Formula version incremented
     - [ ] Regression test added (historical data match)
     - [ ] Impact analysis included (which dashboards/APIs affected)
     - [ ] Data engineering review
     - [ ] Finance sign-off (if materiality > X%)
   ```

3. **Code Review**
   - 2 reviewers minimum
   - 1 must be from data engineering (formula correctness)
   - 1 can be from product/analytics (business impact)
   - Check: formula syntax, test coverage, documentation

4. **Merge & Deploy**
   - CI/CD runs full KPI test suite
   - Staging environment tests against historical data
   - Production tagged with `kpi-v[version]` release
   - Changelog entry: `CHANGELOG.md`

5. **Rollback Ready**
   - Every KPI change must be rollback-safe
   - If not: flag in PR, require FFaaS plan
   - Dashboard can revert to previous formula version

### 6.2 Code Review Checklist for KPI Changes

```markdown
## KPI Formula Change Review

- [ ] **Formula Syntax**
  - [ ] Formula is valid SQL-like syntax
  - [ ] Column names match schema (exact case)
  - [ ] WHERE clauses use correct operators (>=, >, <=, IN, etc.)
  
- [ ] **Precision & Rounding**
  - [ ] Uses Decimal arithmetic (no float)
  - [ ] Rounding specified (default: ROUND_HALF_UP)
  - [ ] Unit conversion correct (e.g., % not decimal)
  
- [ ] **Boundaries & Edge Cases**
  - [ ] Division by zero handled (fallback: Decimal('0.0'))
  - [ ] Status filtering specified (active/closed/defaulted)
  - [ ] Date boundaries clear (month-end, snapshot date, etc.)
  
- [ ] **Testing**
  - [ ] Unit test with synthetic data
  - [ ] Regression test with historical data (last 3 months)
  - [ ] Precision matches to specified decimals
  
- [ ] **Documentation**
  - [ ] Business definition updated in KPI_CATALOG.md
  - [ ] Edge cases documented (why certain loans excluded)
  - [ ] Owner/contact listed
  
- [ ] **Impact Analysis**
  - [ ] Dashboards affected (list names)
  - [ ] APIs affected (list endpoints)
  - [ ] % change from previous formula (magnitude of impact)
  - [ ] Backwards compatibility: is old name still valid?
  
- [ ] **Governance**
  - [ ] No hardcoded formula duplication elsewhere
  - [ ] All implementations removed or redirected to engine
```

---

## 7. Audit & Compliance

### 7.1 Audit Trail Requirements

Every KPI calculation must be logged:

```json
{
  "audit_id": "aud_20260319_par30_001",
  "timestamp": "2026-03-19T14:30:22.123456Z",
  "kpi_name": "par_30",
  "formula_id": "par_30_v1.2",
  "formula_version": "1.2",
  "formula_changed_by": "PR#1234",
  "formula_change_date": "2026-03-19",
  "actor": "api_server",
  "run_id": "batch_20260319_143022",
  "data_hash": "sha256:abc123...",
  "data_rows": 5218,
  "data_snapshot_date": "2026-03-19",
  "columns_used": ["outstanding_balance", "dpd", "status"],
  "execution_milliseconds": 145,
  "result_value": 3.50,
  "result_unit": "percentage",
  "result_precision": 2,
  "validation_passed": true,
  "validation_checks": [
    {"check": "no_nan", "passed": true},
    {"check": "within_bounds", "passed": true},
    {"check": "data_rows_min", "passed": true}
  ],
  "notes": "Monthly portfolio KPI calculation"
}
```

### 7.2 Audit Retention

- **Logs**: Retain 2 years in CloudSQL/production database
- **Searchable by**: `kpi_name`, `timestamp`, `actor`, `run_id`
- **Access**: Role-based (audit team, compliance, data engineering)
- **Compliance**: SOC 2 Type II requirement

---

## 8. Implementation Checklist

- [ ] **Phase 1: Registry Definition** (DONE)
  - [ ] `config/kpis/kpi_definitions.yaml` complete ✅
  - [ ] All ~50 KPIs defined with formulas ✅
  - [ ] Thresholds, units, dependencies documented ✅

- [ ] **Phase 2: Formula Engine** (IN PROGRESS)
  - [ ] Parser for formula syntax
  - [ ] Executor with Decimal arithmetic
  - [ ] Audit trail logging
  - [ ] Validation (NaN, bounds, column checks)
  - [ ] 100% test coverage for engine
  
- [ ] **Phase 3: Implementation Consolidation** (PLANNED)
  - [ ] Migrate all 14+ KPI modules to use engine
  - [ ] Remove duplicate implementations
  - [ ] Historical data regression tests
  - [ ] Accept/document any precision adjustments

- [ ] **Phase 4: Consumer Migration** (PLANNED)
  - [ ] API endpoints return formula version + audit ID
  - [ ] Dashboards query engine results
  - [ ] Batch exports include audit metadata

- [ ] **Phase 5: Sunsetting** (PLANNED)
  - [ ] Deprecate warnings on old functions
  - [ ] Migrate remaining consumers
  - [ ] Remove dead code

---

## 9. References

- **Registry**: [config/kpis/kpi_definitions.yaml](../config/kpis/kpi_definitions.yaml)
- **Engine**: [backend/python/kpis/formula_engine.py](../backend/python/kpis/formula_engine.py)
- **KPI Catalog**: [KPI_CATALOG.md](KPI_CATALOG.md)
- **KPI Operating Model**: [KPI-Operating-Model.md](KPI-Operating-Model.md)
- **Lineage**: [kpi_lineage.md](kpi_lineage.md)

---

**Version**: 1.0  
**Status**: Effective 2026-03-19  
**Approval**: Institutional Audit & Remediation (Workstream 4)
