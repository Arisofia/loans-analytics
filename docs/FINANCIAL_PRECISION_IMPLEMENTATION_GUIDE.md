# Financial Precision Implementation Guide

**Quick Reference for KPI Engineers & Backend Developers**

This guide shows how to apply the Financial Precision Policy (`docs/FINANCIAL_PRECISION_GOVERNANCE.md`) in real code.

---

## Checklist Before Writing KPI Code

- [ ] Read `docs/FINANCIAL_PRECISION_GOVERNANCE.md`
- [ ] Review `backend/python/financial_precision.py` API
- [ ] Run `tests/unit/test_financial_precision.py` locally
- [ ] Check existing KPI implementations for patterns
- [ ] Plan: Which values are monetary? Which are rates?

---

## Pattern 1: Ingesting Loan Data from CSV

### ❌ WRONG: Float columns from CSV

```python
import polars as pl

# Raw CSV load - unsafe
df = pl.read_csv("loans.csv")  # loan_amount is Float64!
# Downstream: float drift accumulates
total = df["loan_amount"].sum()  # ❌ Imprecise
```

### ✅ CORRECT: Convert on ingestion

```python
import polars as pl
from backend.python.financial_precision import dollars_to_cents
from backend.python.schemas import validate_ingestion_contract

# Load CSV with strings for monetary columns
df = pl.read_csv(
    "loans.csv",
    dtypes={
        "loan_amount": pl.String,
        "principal_balance": pl.String,
    },
)

# Convert string amounts to cents (Int64)
df = df.with_columns([
    pl.col("loan_amount")
        .map_elements(dollars_to_cents, return_dtype=pl.Int64)
        .alias("loan_amount"),
    pl.col("principal_balance")
        .map_elements(dollars_to_cents, return_dtype=pl.Int64)
        .alias("principal_balance"),
])

# Validate schema (fails if Float64 found)
validate_ingestion_contract(df)  # ✅ Passes

# Now safe to aggregate
print(f"Total Balance: ${df['principal_balance'].sum() / 100:.2f}")
```

---

## Pattern 2: Computing KPI - Total Portfolio Balance

### ❌ WRONG: Float aggregation (accumulates drift)

```python
def get_portfolio_balance(loans_df):
    """BAD: Uses float sum."""
    total_cents = 0.0  # Float!
    for row in loans_df.iter_rows(named=True):
        total_cents += float(row["principal_balance"])  # ❌ Drift!
    return total_cents / 100
```

### ✅ CORRECT: Decimal sum with precision

```python
from decimal import Decimal
from backend.python.financial_precision import (
    cents_to_dollars,
    safe_decimal_sum,
)

def get_portfolio_balance(loans_df) -> Decimal:
    """GOOD: Uses Decimal sum for precision."""
    # Extract principal_balance (Int64 cents)
    balances_cents = loans_df["principal_balance"].to_list()
    
    # Convert to dollars for calculation
    balances_dollars = [cents_to_dollars(c) for c in balances_cents]
    
    # Sum with Decimal (no drift)
    total_dollars = safe_decimal_sum(balances_dollars)
    
    return total_dollars

# Usage
total = get_portfolio_balance(loans_df)
print(f"Portfolio Balance: ${total:.2f}")
```

---

## Pattern 3: Computing KPI - Weighted Average Interest Rate

### ❌ WRONG: Float interest rate arithmetic

```python
def weighted_avg_rate(loans_df):
    """BAD: Float rate math."""
    total_balance = 0.0
    weighted_amount = 0.0
    
    for row in loans_df.iter_rows(named=True):
        balance = float(row["principal_balance"]) / 100
        rate = float(row["interest_rate"]) / 10_000  # ❌ Float!
        total_balance += balance
        weighted_amount += balance * rate  # ❌ Accumulation drift
    
    return weighted_amount / total_balance  # ❌ Another float division
```

### ✅ CORRECT: Decimal rate arithmetic

```python
from decimal import Decimal
from backend.python.financial_precision import (
    cents_to_dollars,
    basis_points_to_interest_rate,
    safe_decimal_sum,
    safe_decimal_divide,
)

def weighted_avg_rate(loans_df) -> Decimal:
    """GOOD: Uses Decimal for rate calculations."""
    # Initialize lists for accumulation
    weighted_sums = []
    total_balance_dollars = Decimal(0)
    
    # Process each loan
    for row in loans_df.iter_rows(named=True):
        balance_cents = row["principal_balance"]
        rate_bp = row["interest_rate"]
        
        # Convert to Decimal
        balance_dollars = cents_to_dollars(balance_cents)
        rate_decimal = basis_points_to_interest_rate(rate_bp)
        
        # Accumulate weight (balance * rate)
        weighted_sums.append(balance_dollars * rate_decimal)
        total_balance_dollars += balance_dollars
    
    # Sum with precision, then divide
    total_weighted = safe_decimal_sum(weighted_sums)
    avg_rate = safe_decimal_divide(
        total_weighted,
        total_balance_dollars,
        precision=4  # 4 decimals = 0.01% precision
    )
    
    return avg_rate

# Usage
avg = weighted_avg_rate(loans_df)
print(f"Weighted Avg Rate: {float(avg) * 100:.2f}%")
```

---

## Pattern 4: Computing KPI - Past Due Rate (PAR-30)

### ❌ WRONG

```python
def par_30_rate(loans_df):
    """BAD: Float-based calculation."""
    par_30_balance = float(loans_df.filter(
        pl.col("days_past_due") >= 30
    )["principal_balance"].sum())
    
    total_balance = float(loans_df["principal_balance"].sum())
    
    # ❌ Float division → precision loss
    return par_30_balance / total_balance
```

### ✅ CORRECT

```python
from decimal import Decimal
from backend.python.financial_precision import (
    cents_to_dollars,
    safe_decimal_divide,
)

def par_30_rate(loans_df) -> Decimal:
    """GOOD: Precise PAR-30 rate calculation."""
    # Filter with Polars (fast), sum stays Int64
    par_30_df = loans_df.filter(pl.col("days_past_due") >= 30)
    par_30_cents = par_30_df["principal_balance"].sum()
    
    # Totals in Int64 (cents)
    total_cents = loans_df["principal_balance"].sum()
    
    # Convert to Decimal, then divide with precision
    par_30_dollars = cents_to_dollars(par_30_cents)
    total_dollars = cents_to_dollars(total_cents)
    
    # 4 decimal places = rate accurate to 0.01%
    rate = safe_decimal_divide(par_30_dollars, total_dollars, precision=4)
    
    return rate

# Usage
par_rate = par_30_rate(loans_df)
print(f"PAR-30 Rate: {float(par_rate):.4f}")
```

---

## Pattern 5: Interest Accrual Calculation

### ❌ WRONG: Float multiplication

```python
def accrue_interest(loan_amount, annual_rate, days):
    """BAD: Float math."""
    daily_rate = float(annual_rate) / 365  # ❌ Float division
    accrued = float(loan_amount) * daily_rate * days  # ❌ Float multiplication
    return accrued
```

### ✅ CORRECT: Decimal multiplication

```python
from decimal import Decimal
from backend.python.financial_precision import (
    cents_to_dollars,
    basis_points_to_interest_rate,
)

def accrue_interest(
    principal_cents: int,
    annual_rate_bp: int,
    days: int
) -> Decimal:
    """GOOD: Decimal interest accrual."""
    # Convert from cents and basis points
    principal = cents_to_dollars(principal_cents)
    annual_rate = basis_points_to_interest_rate(annual_rate_bp)
    
    # Interest accrual with Decimal
    daily_rate = annual_rate / Decimal(365)
    accrued_interest = principal * daily_rate * Decimal(days)
    
    return accrued_interest

# Usage
accrued = accrue_interest(1_050, 500, 30)  # $10.50 @ 5% for 30 days
print(f"Accrued Interest: ${accrued:.4f}")
```

---

## Pattern 6: Unit Testing Your KPI

Use `safe_decimal_sum()` and `safe_decimal_divide()` in tests to verify precision:

```python
import pytest
from decimal import Decimal
from backend.python.financial_precision import safe_decimal_sum

def test_portfolio_balance_no_drift():
    """Verify aggregation doesn't accumulate float drift."""
    # Create 1000 loans of $1.05 each
    loan_amounts = [Decimal('1.05')] * 1_000
    
    # Sum with Decimal (expected)
    expected = Decimal('1050.00')
    
    # Actual calculation (from your KPI)
    actual = safe_decimal_sum(loan_amounts)
    
    # Must be exact
    assert actual == expected, f"Drift detected: {actual} != {expected}"
```

---

## API Reference: Key Functions

### Monetary Conversions

```python
from backend.python.financial_precision import dollars_to_cents, cents_to_dollars

# String → cents (validated)
cents = dollars_to_cents("10.50")  # 1050

# Cents → Decimal
dollars = cents_to_dollars(1050)  # Decimal('10.50')
```

### Interest Rate Conversions

```python
from backend.python.financial_precision import (
    interest_rate_to_basis_points,
    basis_points_to_interest_rate,
)

# Decimal → basis points
bp = interest_rate_to_basis_points(0.05)  # 500 (for 5%)

# Basis points → Decimal
rate = basis_points_to_interest_rate(500)  # Decimal('0.05')
```

### Aggregation & Division (Precision-Safe)

```python
from backend.python.financial_precision import safe_decimal_sum, safe_decimal_divide

# Sum with Decimal (no float drift)
total = safe_decimal_sum([10.50, 20.25, 5.33])

# Divide with precision control
percentage = safe_decimal_divide(100, 250, precision=4)  # Decimal('0.4000')
```

---

## Code Review Checklist

When reviewing KPI code, verify:

```
□ No Float64 in monetary DataFrame columns (check schema before sum/divide)
□ No float() casts on monetary values
□ All CSV ingestion uses dollars_to_cents() conversion
□ All rate calculations use basis_points_to_interest_rate()
□ All aggregations use safe_decimal_sum() (not DataFrame.sum() on floats)
□ All divisions use safe_decimal_divide() with explicit precision
□ No float() arithmetic in monetary calculations
□ Tests exist for aggregation precision (at least one test with 1000+ items)
□ Financial precision tests pass locally before pushing
```

---

## Common Mistakes & Fixes

| Mistake | Fix |
|---------|-----|
| `df["amount"].sum()` on Float64 | Convert to Int64 (cents) first, use `safe_decimal_sum()` |
| `amount1 / amount2` (float division) | Use `safe_decimal_divide(amount1, amount2, precision=4)` |
| `rate * principal` (float math) | Convert to Decimal, use Decimal multiplication |
| `df["amount"].astype(int)` (silent truncation) | Use `dollars_to_cents()` with validation |
| Testing with ~10 values | Test aggregation with 1000+ values to catch drift |
| Forgetting to convert CSV | Use `with_columns(pl.col(...).map_elements(dollars_to_cents))` |

---

## Resources

- **Full Policy**: [docs/FINANCIAL_PRECISION_GOVERNANCE.md](../FINANCIAL_PRECISION_GOVERNANCE.md)
- **API Docs**: [backend/python/financial_precision.py](../../backend/python/financial_precision.py)
- **Test Examples**: [tests/unit/test_financial_precision.py](../../tests/unit/test_financial_precision.py)
- **Schema Validation**: [backend/python/schemas.py](../../backend/python/schemas.py)

---

**Questions?**  
Reach out to `@backend` or `@data-engineering` in PRs. Precision is non-negotiable.
