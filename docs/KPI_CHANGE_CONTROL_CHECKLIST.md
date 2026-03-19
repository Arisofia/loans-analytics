# KPI Change Control Checklist

**Purpose**: Ensure every KPI change is governed, tested, and auditable  
**Usage**: Required for all PRs that modify KPI definitions or implementations  
**Approvers**: Data Engineering + Finance (if material impact)

---

## Quick Start

**For developers**: Copy the checklist below into your PR description and complete all checkboxes before requesting review.

**For reviewers**: Verify checklist completion; reject if any items unchecked per your approval authority.

---

## Pre-Submission Checklist (Before Opening PR)

### 1. Changes Classification

- [ ] **KPI Definition Change** (formula, unit, grain, threshold, owner)
  - Location: `config/kpis/kpi_definitions.yaml`
  - Requires: Data engineering review + 1 snapshot test
  
- [ ] **KPI Implementation Change** (code in `backend/python/kpis/`)
  - Requires: Regression test against historical data
  
- [ ] **Consumer Update** (API, dashboard, batch export)
  - Requires: Verify all consumers use same formula version

- [ ] **Documentation Only** (KPI_CATALOG.md, notes)
  - Requires: Business owner approval

### 2. Impact Analysis (REQUIRED)

- [ ] Identified affected systems:
  - [ ] APIs: List endpoints
  - [ ] Dashboards: List dashboard names
  - [ ] Batch exports: List export types
  - [ ] Reports: List report names
  
- [ ] Estimated change magnitude:
  - [ ] % change from previous KPI value: ___% (e.g., +0.5%, -2.3%)
  - [ ] Reason for change: ____________
  - [ ] Materiality: 🟢 Minor (<1%) / 🟡 Medium (1-5%) / 🔴 Major (>5%)

- [ ] Backwards compatibility:
  - [ ] Can old dashboards still use previous formula? ☐ Yes ☐ No
  - [ ] Do we need to maintain alternate_names for legacy consumers? ☐ Yes ☐ No

### 3. Data Validation (REQUIRED)

- [ ] Regression test passed:
  - [ ] Test file: `tests/unit/test_kpi_*.py` or `tests/integration/test_kpi_*.py`
  - [ ] Test coverage: Changed 3+ months of historical data? ☐ Yes ☐ No
  - [ ] Precision match: Within tolerance (decimal places specified in registry)? ☐ Yes ☐ No
  - [ ] No NaN/Inf/null results? ☐ Yes ☐ No

- [ ] Edge case testing:
  - [ ] Empty data (zero loans)? ☐ Tested
  - [ ] All delinquent status? ☐ Tested (if applicable)
  - [ ] Division by zero (if formula has division)? ☐ Handled
  - [ ] Status filtering (if applicable)? ☐ Verified

- [ ] Data quality checks:
  - [ ] No schema changes required? ☐ Yes ☐ No (if No, file separate schema change PR)
  - [ ] Column types match expected (Int64 for cents, etc.)? ☐ Yes ☐ No
  - [ ] Timezone handling (UTC only)? ☐ Yes ☐ No

### 4. Code Quality

- [ ] Formula syntax valid:
  - [ ] Double-checked for typos
  - [ ] Column names exact (case-sensitive)
  - [ ] Operators correct (>=, >, <=, <, IN, etc.)
  
- [ ] No hardcoded values:
  - [ ] Constants pulled from config? ☐ Yes ☐ N/A
  - [ ] Thresholds in registry (not code)? ☐ Yes ☐ N/A

- [ ] Precision requirements:
  - [ ] Uses Decimal (not float) for financial calcs? ☐ Yes ☐ Auto
  - [ ] Rounding specified (ROUND_HALF_UP)? ☐ Yes ☐ Default

---

## PR Description Template

Copy this into your PR description and complete all sections:

```markdown
## KPI Change: [KPI Name]

### 📋 Change Classification
- [ ] Definition change (formula/unit/grain/owner)
- [ ] Implementation change (code)
- [ ] Consumer update (API/dashboard)
- [ ] Documentation
- [ ] Other: ___

### 📊 Impact Analysis

**Affected Systems:**
- APIs: [list endpoints]
- Dashboards: [list names]
- Batch exports: [list types]

**Change Magnitude:** [±X.X%]  
**Materiality:** [Minor/Medium/Major]  
**Reason:** [Business justification]

### ✅ Testing

**Regression Test:**
- File: `tests/unit/test_kpi_*.py`
- Historical data: [X months tested]
- Precision: ±[X decimals]
- Status: [PASSED/FAILED]

**Edge Cases:**
- [ ] Empty data
- [ ] All delinquent
- [ ] Division by zero
- [ ] Status filtering

### 🔍 Validation

- [ ] Schema unchanged (no Int64/Float64 issues)
- [ ] All column names exact
- [ ] No hardcoded values (all in config/kpis/)
- [ ] Financial precision rules followed
- [ ] Backwards compatible (or alternate_names added)

### 📝 Documentation

- [ ] `config/kpis/kpi_definitions.yaml` updated
- [ ] Registry version incremented
- [ ] Changed_by: PR#[number]
- [ ] Version_date: [YYYY-MM-DD]
- [ ] `docs/KPI_CATALOG.md` updated
- [ ] `docs/KPI_IMPLEMENTATION_INVENTORY.md` updated (if applicable)

### 👤 Sign-offs

**Data Engineering:** ☐ Approved  
**Finance (if material):** ☐ Approved
```

---

## Reviewer Checklist (For Code Reviewers)

### Formula Review

- [ ] **Syntax Check**
  - [ ] Formula parses without errors
  - [ ] Column names match schema exactly
  - [ ] WHERE clauses use valid columns/operators

- [ ] **Logic Verification**
  - [ ] Formula matches business definition in KPI_CATALOG.md
  - [ ] Status filtering consistent with other KPIs
  - [ ] Date/timeline boundaries clear (month-end, snapshot date, etc.)

- [ ] **Precision Check**
  - [ ] Uses Decimal arithmetic (no float)
  - [ ] Rounding mode specified (default: ROUND_HALF_UP)
  - [ ] Denominators checked for zero with fallback

### Testing Rigor

- [ ] **Regression Test**
  - [ ] Test file exists and passes
  - [ ] Historical data >= 3 months
  - [ ] Precision tolerance reasonable
  - [ ] Expected value documented in test

- [ ] **Edge Case Coverage**
  - [ ] Empty data handled
  - [ ] Division by zero guarded
  - [ ] Status filtering tested (if applicable)
  - [ ] NaN/Inf/null results prevented

### Impact Assessment

- [ ] **Affected Systems Identified**
  - [ ] All APIs listed
  - [ ] All dashboards listed
  - [ ] All batch exports listed

- [ ] **Magnitude Reasonable**
  - [ ] Change % makes business sense
  - [ ] If >5% change, finance has approved
  - [ ] No unexplained jumps in KPI values

- [ ] **Backwards Compatibility**
  - [ ] Old formula deprecated gracefully (or alternate_names added)
  - [ ] No breaking changes for consumers (or coordinated release)

### Documentation Quality

- [ ] **Registry Update**
  - [ ] `config/kpis/kpi_definitions.yaml` updated
  - [ ] Formula version incremented (e.g., 1.0 → 1.1)
  - [ ] Change date recorded
  - [ ] PR reference included

- [ ] **External Docs**
  - [ ] KPI_CATALOG.md updated
  - [ ] KPI_IMPLEMENTATION_INVENTORY.md updated
  - [ ] Any related dashboards documented

### Governance

- [ ] **Audit Trail**
  - [ ] PR linked in registry
  - [ ] Author attribution clear
  - [ ] Change date recorded

- [ ] **Sign-offs**
  - [ ] Data engineering reviewed
  - [ ] Finance approved (if material >5%)
  - [ ] Product stakeholder aware (if customer-facing)

---

## Rejection Criteria (Auto-Reject without Changes)

**Auto-reject if:**
1. ❌ No regression test
2. ❌ Hardcoded formula (not in registry)
3. ❌ Float arithmetic for financial values
4. ❌ No impact analysis
5. ❌ Schema change required (separate PR needed first)
6. ❌ No affected systems documented
7. ❌ >5% change without finance approval
8. ❌ Duplicates existing implementation (should consolidate instead)

**Notify data engineering lead if:**
- 🔶 Precision adjustment > ±0.01
- 🔶 Status filtering changed
- 🔶 Date boundaries changed
- 🔶 ~Material impact >5%

---

## Examples

### ✅ Good Example: Fixing NPL Thresholds

```markdown
## KPI Change: Update NPL warning/critical thresholds

### Classification
- [x] Definition change (formula/unit/grain/owner)

### Impact
- Affected: "Portfolio Risk" dashboard, /api/kpis/npl
- Change: threshold warning 5% → 4%, critical 10% → 8%
- Magnitude: 0% (formula unchanged, only thresholds)
- Materiality: Minor (UI alerts only, no calculations changed)

### Testing
- Regression: tests/unit/test_kpi_npl.py - PASSED
- Historical data tested: 12 months
- Precision: 2 decimals ±0.01 - MATCH

### Documentation
- [x] config/kpis/kpi_definitions.yaml updated
- [x] version: 1.0 → 1.1
- [x] docs/KPI_CATALOG.md updated
- [x] changed_by: PR#1234, date: 2026-03-19

### Sign-offs
- Data Engineering: ✅
- Finance: ✅ (thresholds reviewed)
```

### ✅ Good Example: Adding Missing Status Filter

```markdown
## KPI Change: Add status filter to Collections Rate (exclude closed loans)

### Classification
- [x] Definition change (formula update)

### Impact
- Affected: Collections dashboard, /api/kpis/collections_rate, batch reports
- Change: SUM(last_payment_amount) / SUM(total_scheduled)
         → SUM(last_payment_amount WHERE status != 'closed') / SUM(total_scheduled WHERE status != 'closed')
- Magnitude: +1.2% (closed loans were bringing rate down)
- Materiality: Medium (affects KPI display)

### Testing
- Regression: tests/unit/test_kpi_collections.py - PASSED
- Historical: 12 months tested, precision ±0.1% (acceptable given status bucketing)
- Edge cases: All closed portfolio → returns 0 (correct)

### Documentation
- [x] config/kpis/kpi_definitions.yaml updated
- [x] version: 1.0 → 1.2 (reason: added status filter)
- [x] docs/KPI_CATALOG.md added note on closed loan exclusion
- [x] docs/KPI_IMPLEMENTATION_INVENTORY.md: marked advanced_risk.py as duplicate

### Sign-offs
- Data Engineering: ✅
- Finance: ✅ (1.2% change reviewed and approved)
```

### ❌ Bad Example (Would be rejected)

```markdown
## KPI Change: Improve PAR-30 calculation

### Impact
- Dashboards affected (not listed)
- ~2% change
- Testing: Tested on current month only
```

**Rejection reason:** No regression test on historical data, changed magnitude not explained, affected systems not all listed.

---

## Quick Reference: Decision Tree

```
Is this a KPI change?
├─ NO → Use standard code review
└─ YES
   ├─ Is it definition (formula/unit)? 
   │  ├─ YES → Requires registry update + regression test + finance approval (if >5%)
   │  └─ NO
   │     ├─ Is it implementation code?
   │     │  ├─ YES → Requires regression test + must use engine
   │     │  └─ NO
   │     │     ├─ Is it consumer update (API/dashboard)?
   │     │     │  ├─ YES → Verify uses same formula version
   │     │     │  └─ NO → Standard code review
```

---

## Approval Authorities

| Change Type | Who Must Approve |  Authority Level |
|------------|-----------------|------------------|
| Formula change | Data Engineering | ✅ Mandatory |
| Unit/grain change | Data Engineering | ✅ Mandatory |
| Threshold change (<5%) | Data Engineering | ✅ OK |
| Threshold change (≥5%) | Finance + Data Eng | ✅✅ Both required |
| Owner update | Previous owner | ⚠️ Good practice |
| New KPI | Data Eng + Product | ✅✅ Both required |

---

## Related Documents

- **Registry**: [config/kpis/kpi_definitions.yaml](../../config/kpis/kpi_definitions.yaml)
- **Framework**: [docs/KPI_SSOT_REGISTRY.md](KPI_SSOT_REGISTRY.md)
- **Inventory**: [docs/KPI_IMPLEMENTATION_INVENTORY.md](KPI_IMPLEMENTATION_INVENTORY.md)
- **Catalog**: [docs/KPI_CATALOG.md](KPI_CATALOG.md)
- **Financial Precision**: [docs/FINANCIAL_PRECISION_GOVERNANCE.md](FINANCIAL_PRECISION_GOVERNANCE.md)

