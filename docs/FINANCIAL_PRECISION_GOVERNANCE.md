# Financial Precision Policy & Governance

**Effective Date**: 2026-03-19  
**Status**: MANDATORY (Non-negotiable for fintech operations)  
**Applies To**: All monetary calculations, schema definitions, and KPI computations

## Executive Summary

Loans Analytics REQUIRES zero financial data drift. All monetary values must be stored and computed using precision-safe representations to prevent floating-point accumulation errors that are inevitable with IEEE 754 float arithmetic.

**Non-Negotiable Rule**: Never use Float64 for monetary values. Always use Int64 with scaling (cents, basis points) + Decimal for calculations.

---

## 1. Monetary Value Representation

### 1.1 Storage Format: Scaled Integers (Cents)

All monetary amounts are stored as **Int64 (cents)** in the database and data pipelines:

| Amount | Internal Representation | Range | Precision |
|--------|------------------------|-------|-----------|
| $10.50 | 1,050 cents | $0.01 to $100,000,000 | Exact (to 1 cent) |
| $100.01 | 10,001 cents | 1 to 10,000,000,000 | No rounding needed |
| $0.01 | 1 cent | Min value valid | Minimum unit |

**Why Int64 (Cents)?**
- Eliminates floating-point rounding errors
- Natural fit for financial rounding (always to nearest cent)
- Exact arithmetic (no accumulation drift)
- Compatible with database  backends (PostgreSQL, Polars, etc.)

### 1.2 Interest Rates: Basis Points (0.01% units)

Interest rates are stored as **Int64 (basis points)**:

| Rate | Basis Points | Range | Precision |
|------|--------------|-------|-----------|
| 5.00% | 500 | 0 to 20,000,000 | 0.01% (1 basis point) |
| 5.25% | 525 | 0% to 2000% valid range | Exact |
| 0.01% | 1 | Min rate | 1 basis point = 0.01% |

**Conversion**:
- 1 basis point (bp) = 0.01%
- Rate as decimal (0.05) → 500 basis points
- 500 basis points → 0.05 rate for display

### 1.3 Decimal Arithmetic for Calculations

All financial calculations (sums, divisions, percentages) use Python `Decimal` with:
- Mode: `ROUND_HALF_UP` (standard banker's rounding)
- Precision: Configurable per operation
  - Monetary sums: Exact to nearest cent
  - Rates: 4 decimal places (0.0001%)
  - Percentages: Variable (usually 2-4 decimals)

**Why Decimal?**
- No floating-point drift in aggregations
- Exact representation of decimal numbers
- Banker's rounding for financial standards
- Transparent in code (no surprises)

---

## 2. Data Ingestion: Float → Int64 Conversion

### 2.1 Conversion Function: dollars_to_cents()

When monetary data enters the system (from CSV, API, etc.), it MUST be converted:

```python
from backend.python.financial_precision import dollars_to_cents

# CSV input: "10.50"
amount_str = "10.50"
cents = dollars_to_cents(amount_str)  # Returns: 1050

# From float (less ideal, but supported with validation)
amount_float = 10.50
cents = dollars_to_cents(amount_float)  # Returns: 1050
```

**Validation Rules** (triggered automatically):
1. **Precision Check**: Rejects values with >2 decimal places
   - `dollars_to_cents("10.001")` → ❌ ValueError (3 decimal places)
   - `dollars_to_cents("10.50")` → ✅ 1050 cents

2. **Bounds Check**: Rejects values outside valid range
   - Minimum: $0.01 (1 cent)
   - Maximum: $100,000,000 (10 billion cents)
   - Out of range → ❌ ValueError

3. **Precision Preservation**:
   - Input: "10.50" → Int: 1050 → Output: $10.50 (exact round-trip)
   - No rounding error accumulation

### 2.2 Validation on Ingestion

Use `validate_monetary_field()` for error logging + conversion:

```python
from backend.python.financial_precision import validate_monetary_field

try:
    loan_amount_cents = validate_monetary_field("loan_amount", "10.50")
    # Returns 1050, logs warnings for suspicious values
except ValueError as e:
    # Logs: "Validation failed for loan_amount: ..."
    raise
```

---

## 3. Schema Contracts: Int64 Non-Negotiable

### 3.1 LOAN_SCHEMA (Updated)

```python
# ✅ CORRECT (Int64 with cents/basis points)
LOAN_SCHEMA = pl.Schema([
    ("loan_id", pl.String),
    ("loan_amount", pl.Int64),        # Cents!
    ("principal_balance", pl.Int64),  # Cents!
    ("interest_rate", pl.Int64),      # Basis points!
    ("measurement_date", pl.String),
])

# ❌ WRONG (Float64 - DO NOT USE)
WRONG_SCHEMA = pl.Schema([
    ("loan_amount", pl.Float64),      # ❌ Floating-point drift risk
    ("interest_rate", pl.Float64),    # ❌ Accumulation errors
])
```

### 3.2 Type Enforcement in Validation

`validate_ingestion_contract()` **FAILS** if:
- Monetary column is not Int64
  - Message: `"loan_amount must be Int64 (cents), found Float64"`
  - Action: Use `dollars_to_cents()` during ingestion

- Interest rate column is not Int64
  - Message: `"interest_rate must be Int64 (basis points), found Float64"`
  - Action: Use `interest_rate_to_basis_points()` during ingestion

---

## 4. Calculation Guidelines

### 4.1 Summation (Aggregation)

❌ **WRONG**: Using float sum (accumulates drift)
```python
total_balance = 0.0
for loan in loans:
    total_balance += float(loan.principal_balance)  # ❌ Drift!
```

✅ **CORRECT**: Using Decimal sum
```python
from backend.python.financial_precision import safe_decimal_sum

# Convert cents back to Decimal for calculation
balances_decimal = [cents_to_dollars(loan.principal_balance) for loan in loans]
total_balance = safe_decimal_sum(balances_decimal)  # ✅ Exact
```

### 4.2 Division (Rates, Percentages)

❌ **WRONG**: Float division (loses precision)
```python
par_rate = float(par_amount) / float(total_balance)  # ❌ Drift in rate calculation
```

✅ **CORRECT**: Decimal division
```python
from backend.python.financial_precision import safe_decimal_divide

par_rate = safe_decimal_divide(par_amount, total_balance, precision=4)
# Returns: Decimal('0.0400') for exact 4% (no drift)
```

### 4.3 Interest Accrual (Multiplication)

❌ **WRONG**: Float multiplication
```python
accrued_interest = float(principal) * float(rate)  # ❌ Drift
```

✅ **CORRECT**: Decimal multiplication
```python
from backend.python.financial_precision import (
    cents_to_dollars,
    basis_points_to_interest_rate,
    safe_decimal_divide,
)

principal_dec = cents_to_dollars(principal_cents)
rate_dec = basis_points_to_interest_rate(rate_bp)
accrued_interest = principal_dec * rate_dec  # ✅ Exact
```

---

## 5. Output & Display

### 5.1 Convert Back to User-Facing Formats

When returning data to API / Dashboard:

```python
from backend.python.financial_precision import cents_to_dollars, basis_points_to_interest_rate

# Internal: Int64 (cents + basis points)
internal_amount = 1050
internal_rate = 500

# For API/display: Back to decimal for readability
display_amount = float(cents_to_dollars(internal_amount))  # 10.50
display_rate = float(basis_points_to_interest_rate(internal_rate))  # 0.05
```

### 5.2 Rounding for Display

Use Decimal's quantize for consistent display rounding:

```python
from decimal import Decimal, ROUND_HALF_UP

result = Decimal('0.3333333333')
display = result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)  # 0.33
```

---

## 6. Testing & Validation

### 6.1 Regression Test Suite

**File**: `tests/unit/test_financial_precision.py`

**Coverage**:
- ✅ Monetary conversions (dollars ↔ cents round-trip)
- ✅ Interest rate conversions (decimal ↔ basis points)
- ✅ Aggregation precision (no float drift in sums)
- ✅ Division precision (rates computed exactly)
- ✅ Boundary conditions (min/max values)
- ✅ Rounding behavior (ROUND_HALF_UP)

**Running Tests**:
```bash
# Run all precision tests
pytest tests/unit/test_financial_precision.py -v

# Run specific test class
pytest tests/unit/test_financial_precision.py::TestAggregationPrecision -v

# CI/CD constraint: MUST PASS
# Failure blocks merge
```

### 6.2 CI/CD Enforcement

**Workflow**: `.github/workflows/pr-checks.yml`

```yaml
- name: Run financial precision regression tests
  run: |
    pytest tests/unit/test_financial_precision.py -v --tb=short
  continue-on-error: false  # ❌ Blocks merge on failure
```

**Consequence**: Any PR that introduces float arithmetic in monetary code → CI failures → merge blocked.

### 6.3 Schema Validation on Load

Every ingestion validates schema immediately:

```python
from backend.python.schemas import validate_ingestion_contract

df = load_csv("loans.csv")
validate_ingestion_contract(df)  # ❌ Fails if monetary columns are Float64
```

---

## 7. Governance & Approval

### 7.1 Who Enforces This Policy?

1. **Data Engineering**: Ensures CSV ingestion converts float → cents
2. **Backend Developers**: Schema contracts use Int64 for monetary fields
3. **KPI Engineers**: All calculations use Decimal arithmetic
4. **QA/Testing**: Regression tests must pass
5. **Ops/DevOps**: No schema changes without precision review

### 7.2 Code Review Checklist

Before approving any PR that touches monetary code:

- [ ] No `Float64` in schemas for monetary columns
- [ ] No `float()` arithmetic in KPI calculations
- [ ] All conversions use `dollars_to_cents()` / `cents_to_dollars()`
- [ ] All aggregations use `safe_decimal_sum()`
- [ ] All divisions use `safe_decimal_divide()`
- [ ] Financial precision tests pass
- [ ] No regressions in test suite

### 7.3 Escalation Path

**Violation Found** (e.g., code review detects `Float64`):
1. Comment: "This violates Financial Precision Policy (docs/GOVERNANCE.md, Section 2.1)"
2. Require changes before approval
3. If unsure about guidance, ping: `@data-engineering`, `@backend`

---

## 8. Common Patterns & Recipes

### 8.1 Ingesting CSV with Monetary Data

```python
import polars as pl
from backend.python.financial_precision import dollars_to_cents
from backend.python.schemas import LOAN_SCHEMA, validate_ingestion_contract

# Load CSV (initially as strings to preserve precision)
raw_df = pl.read_csv("loans.csv", dtypes={
    "loan_amount": pl.String,  # Keep as string initially
    "principal_balance": pl.String,
})

# Convert to cents (Int64)
df = raw_df.with_columns([
    pl.col("loan_amount").map_elements(dollars_to_cents).cast(pl.Int64).alias("loan_amount"),
    pl.col("principal_balance").map_elements(dollars_to_cents).cast(pl.Int64).alias("principal_balance"),
])

# Validate schema
validate_ingestion_contract(df)  # ✅ Passes

# Now process...
```

### 8.2 Computing PAR Rates

```python
from backend.python.financial_precision import (
    cents_to_dollars,
    safe_decimal_divide,
)

def compute_par_rate(par_amount_cents: int, total_balance_cents: int) -> Decimal:
    """Compute Past Due rate with precision."""
    # Convert to Decimal for calculation
    par_amount_dec = cents_to_dollars(par_amount_cents)
    total_dec = cents_to_dollars(total_balance_cents)
    
    # Divide with 4 decimal places (0.01% granularity)
    return safe_decimal_divide(par_amount_dec, total_dec, precision=4)

# Example: $1,000 PAR / $25,000 total = 4.00%
par_rate = compute_par_rate(100_000, 2_500_000)  # Returns Decimal('0.0400')
```

### 8.3 Aggregating Loan Balances

```python
from backend.python.financial_precision import safe_decimal_sum, cents_to_dollars

def total_portfolio_balance(loans_df: pl.DataFrame) -> Decimal:
    """Sum all loan balances with precision."""
    # Extract balance column (in cents)
    balances_cents = loans_df["principal_balance"].to_list()
    
    # Convert to dollars + sum with Decimal
    balances_dollars = [cents_to_dollars(c) for c in balances_cents]
    total = safe_decimal_sum(balances_dollars)
    
    return total
```

---

## 9. Exceptions & Special Cases

### 9.1 When Float Storage is Acceptable

**Only** for non-financial, non-contractual values:
- Model coefficients (e.g., ML risk weights)
- Temporary calculation intermediates (before final rounding)
- Feature scaling in ML pipelines

**NOT acceptable** for:
- Loan amounts
- Balances
- Interest earned
- Payments received
- Any balance sheet item

### 9.2 Legacy Code Transition

If encountering old `Float64` code:
1. Open issue to track refactoring
2. Label: `precision-debt`
3. Plan migration in roadmap
4. No NEW code can use Float64 for monetary

---

## 10. References & Resources

- **Implementation**: `backend/python/financial_precision.py`
- **Schemas**: `backend/python/schemas.py` (LOAN_SCHEMA)
- **Tests**: `tests/unit/test_financial_precision.py`
- **Governance**: `docs/GOVERNANCE.md` (this file)

---

**Version**: 1.0  
**Last Updated**: 2026-03-19  
**Status**: Effective Immediately  
**Approval**: Institutional Audit & Remediation (Workstream 3)
