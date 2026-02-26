# Code Optimizer Agent - Usage Examples

## Overview

The code_optimizer agent is now available for use in VS Code with GitHub Copilot.

## How to Invoke

In GitHub Copilot Chat (VS Code), use the `@code_optimizer` prefix:

### Example 1: Performance Review

```
@code_optimizer Review this function for performance bottlenecks
```

### Example 2: Financial Accuracy Check

```
@code_optimizer Check if this calculation is using Decimal properly for financial precision
```

### Example 3: Database Query Optimization

```
@code_optimizer Find N+1 query problems in this Supabase code
```

### Example 4: Security Review

```
@code_optimizer Review this code for PII leakage and security vulnerabilities
```

### Example 5: Code Quality

```
@code_optimizer Optimize this pandas DataFrame operation for large datasets
```

## Agent Capabilities

### Performance Optimization

- Identifies slow operations in data pipelines
- Suggests vectorization over iteration
- Recommends polars for large datasets (>10k rows)
- Detects N+1 database query patterns
- Suggests caching strategies

### Financial Accuracy

- Enforces Decimal usage for all monetary values
- Flags float arithmetic in financial calculations
- Validates proper rounding methods
- Checks currency code formats (ISO 4217)
- Ensures interest rate precision

### Security & Compliance

- Detects PII in logs
- Identifies missing input validation
- Checks for SQL injection vulnerabilities
- Validates secret management
- Reviews audit trail implementation

### Code Quality

- Enforces type hints
- Validates structured logging
- Checks error handling patterns
- Reviews test coverage
- Suggests refactoring opportunities

## Domain Context

The agent is aware of:

- Abaco Loans Analytics architecture (4-phase ETL pipeline)
- Financial domain knowledge (PAR-30, PAR-90, DPD, NPL)
- Existing tooling (black, ruff, mypy, pylint)
- Compliance requirements for fintech
- Project structure and conventions

## Best Practices

1. **Be Specific**: Provide context about what you're trying to optimize
2. **Show Code**: Include the code snippet you want reviewed
3. **State Goals**: Mention performance targets or constraints
4. **Provide Metrics**: Share current performance if available

## Example Conversation

**User:**

```
@code_optimizer I have this KPI calculation that takes 30 seconds to process
50k loans. Can you help optimize it?

def calculate_par30(loans):
    total = 0.0
    at_risk = 0.0
    for loan in loans:
        total += loan['balance']
        if loan['dpd'] >= 30:
            at_risk += loan['balance']
    return (at_risk / total) * 100
```

**Agent Response:**

````
I see several optimization opportunities and critical issues:

1. **CRITICAL - Float Precision Error**:
   Using float (0.0) for financial calculations will cause precision loss.
   Replace with Decimal.

2. **Performance Issue**:
   Row-by-row iteration is slow. Use vectorization with pandas/polars.

3. **Missing Type Hints**:
   No type hints for function parameters or return value.

Optimized version:

```python
from decimal import Decimal
from typing import Any, Dict, List
import polars as pl

def calculate_par30(loans: List[Dict[str, Any]]) -> Decimal:
    """Calculate Portfolio at Risk 30 days.

    Args:
        loans: List of loan dictionaries

    Returns:
        PAR-30 percentage as Decimal
    """
    df = pl.DataFrame(loans)

    total_balance = df.select(
        pl.col('balance').cast(pl.Decimal(38, 4)).sum()
    ).item()

    at_risk_balance = df.filter(
        pl.col('dpd') >= 30
    ).select(
        pl.col('balance').cast(pl.Decimal(38, 4)).sum()
    ).item()

    if total_balance == Decimal('0'):
        return Decimal('0')

    return (at_risk_balance / total_balance * Decimal('100')).quantize(
        Decimal('0.01')
    )
````

This should reduce execution time from 30s to <1s for 50k loans.

```

## Integration with CI/CD

The agent recommendations align with automated checks:
- CodeRabbit PR reviews
- SonarQube quality gates (95% coverage)
- Bandit security scanning
- Ruff, flake8, pylint linting
- mypy type checking

## Feedback & Improvements

To suggest improvements to the agent:
1. Open an issue with `[Agent]` prefix
2. Describe the scenario where the agent could be more helpful
3. Provide example code and desired behavior

Agent configuration: `.github/agents/code_optimizer.md`
```
