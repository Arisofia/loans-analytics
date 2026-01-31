# Testing Documentation

This directory contains test plans, test cases, and testing documentation for the Abaco Loans Analytics platform.

## Directory Structure

```
docs/testing/
├── README.md (this file)
├── test_plans/          # Test plan documents
│   └── [feature]_test_plan.md
├── test_cases/          # Detailed test case documents
│   └── [feature]_test_cases.md
└── reports/             # Test execution reports (optional)
    └── [date]_test_report.md
```

## Test Planning Process

### 1. Generate Test Plan

Use the TestCraftPro QA Engineer agent to generate comprehensive test plans:

```
@qa_engineer Generate a test plan for [feature name]
```

The agent will:
1. Ask clarifying questions about requirements
2. Generate a structured test plan
3. Save to `docs/testing/test_plans/[feature]_test_plan.md`

### 2. Create Test Cases

After test plan approval, generate detailed test cases:

```
@qa_engineer Create test cases for [feature name]
```

Test cases are organized by category:
- Functional Testing
- Error Handling & Edge Cases
- Security Testing
- Performance Testing
- Integration Testing
- Compliance & Financial Accuracy

### 3. Implement Tests

Convert test cases to automated tests using pytest:

```python
# tests/test_[feature].py
import pytest
from decimal import Decimal

def test_feature_happy_path():
    """TC-F-001: Test main success scenario"""
    # Arrange
    input_data = setup_test_data()
    
    # Act
    result = feature_function(input_data)
    
    # Assert
    assert result.status == "success"
    assert isinstance(result.amount, Decimal)  # Financial accuracy

@pytest.mark.integration
def test_feature_database_integration():
    """TC-I-001: Test database integration"""
    # Requires test database credentials
    pass

@pytest.mark.performance
def test_feature_performance():
    """TC-P-001: Test response time"""
    import time
    start = time.time()
    
    result = feature_function(large_dataset)
    
    duration = time.time() - start
    assert duration < 30.0, f"Took {duration}s, expected <30s"
```

### 4. Execute Tests

Run tests with pytest:

```bash
# Run all tests
pytest

# Run specific test suite
pytest tests/test_[feature].py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only integration tests
pytest -m integration

# Run performance tests
pytest -m performance
```

## Templates

Test plan and test case templates are available in `docs/templates/`:

- `test_plan_template.md` - Comprehensive test plan template
- `test_cases_template.md` - Detailed test case template

## Testing Standards

### Financial Accuracy
- **ALWAYS** use `Decimal` for monetary values (never `float`)
- Verify calculations against known baselines
- Test rounding rules (ROUND_HALF_UP for currency)

### Security & Compliance
- Test PII protection (masking in logs and outputs)
- Verify authentication and authorization
- Test for common vulnerabilities (SQL injection, XSS)
- Validate audit trail for sensitive operations

### Performance
- Test with realistic data volumes (10k, 100k, 1M records)
- Verify memory usage within constraints (typically 2GB for CI)
- Measure response times (p50, p95, p99)
- Check for memory leaks

### Integration
- Test with Supabase database
- Test external API integrations (with mocks for unit tests)
- Verify error handling for integration failures
- Test connection pooling and retry logic

## Test Markers

Use pytest markers to organize tests:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests (require external services)
- `@pytest.mark.performance` - Performance/load tests
- `@pytest.mark.security` - Security-focused tests
- `@pytest.mark.slow` - Tests that take >1 second

## Coverage Requirements

- **New Code**: ≥95% coverage
- **Critical Paths**: 100% coverage (financial calculations, security)
- **Existing Code**: Maintain or improve current coverage

## CI/CD Integration

Tests run automatically in GitHub Actions:

- **On PR**: Unit tests + linting
- **On Merge**: Full test suite including integration tests
- **Nightly**: Performance tests and security scans

## References

- **QA Engineer Agent**: `.github/agents/qa_engineer.md`
- **Test Templates**: `docs/templates/test_plan_template.md`, `test_cases_template.md`
- **Pytest Documentation**: https://docs.pytest.org/
- **Repository Testing Guide**: See existing test files in `tests/` and `python/tests/`

## Examples

Existing test plans in this repository:

- `fi-analytics/analytics_pipeline_test_plan.md` - Analytics pipeline testing
- More examples coming soon...

## Questions?

Use the TestCraftPro QA Engineer agent for test planning assistance:

```
@qa_engineer [Your question about testing]
```

Or contact the QA team for guidance.

---

**Last Updated**: 2026-01-31  
**Created by**: TestCraftPro (QA Engineer Agent)
