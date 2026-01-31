# TestCraftPro Quick Start Guide

Get started with the TestCraftPro QA Engineer agent in 5 minutes.

## Prerequisites

- GitHub Copilot installed in VS Code
- Access to the Arisofia/abaco-loans-analytics repository
- Basic understanding of testing concepts

## Quick Start (3 Steps)

### Step 1: Invoke the Agent

Open GitHub Copilot Chat in VS Code and type:

```
@qa_engineer Generate a test plan for [your feature]
```

**Example:**
```
@qa_engineer Generate a test plan for the new loan portfolio KPI dashboard
```

### Step 2: Answer Questions

The agent will ask 3-4 clarifying questions. Answer them to get better results:

**Example Questions:**
1. What KPIs will the dashboard display?
2. Who are the primary users?
3. What data sources does it use?
4. Any performance requirements?

**Example Answers:**
1. PAR-30, PAR-90, default rate, collection efficiency
2. Portfolio Managers and Risk Analysts
3. Supabase database with loan transaction data
4. Should load within 2 seconds for 10k loans

### Step 3: Review & Use

The agent generates:
- Test plan: `docs/testing/test_plans/[feature]_test_plan.md`
- Test cases: `docs/testing/test_cases/[feature]_test_cases.md` (if requested)

Review, customize, and implement!

## Common Use Cases

### 1. New Feature Testing
```
@qa_engineer Generate a test plan for the credit scoring integration feature
```

### 2. API Endpoint Testing
```
@qa_engineer Create test cases for POST /api/v1/loans endpoint
```

### 3. Security Testing
```
@qa_engineer What security tests should I include for user authentication?
```

### 4. Performance Testing
```
@qa_engineer Help me design performance tests for batch loan processing
```

### 5. Review Existing Tests
```
@qa_engineer Review my test plan and suggest improvements: [paste test plan]
```

## Test Implementation Example

After getting test cases, implement with pytest:

```python
# tests/test_loan_portfolio_dashboard.py
import pytest
from decimal import Decimal

def test_dashboard_loads_kpis():
    """TC-F-001: Dashboard displays all required KPIs"""
    dashboard = LoanPortfolioDashboard()
    
    kpis = dashboard.load_kpis(loan_count=1000)
    
    assert 'par_30' in kpis
    assert 'par_90' in kpis
    assert 'default_rate' in kpis
    assert isinstance(kpis['par_30'], Decimal)  # Financial accuracy

@pytest.mark.performance
def test_dashboard_performance():
    """TC-P-001: Dashboard loads within 2 seconds"""
    import time
    
    dashboard = LoanPortfolioDashboard()
    start = time.time()
    
    kpis = dashboard.load_kpis(loan_count=10000)
    
    duration = time.time() - start
    assert duration < 2.0, f"Took {duration:.2f}s, expected <2s"

@pytest.mark.security
def test_dashboard_authentication():
    """TC-S-001: Unauthenticated users cannot access dashboard"""
    dashboard = LoanPortfolioDashboard()
    
    with pytest.raises(AuthenticationError):
        dashboard.load_kpis(auth_token=None)
```

Run tests:
```bash
pytest tests/test_loan_portfolio_dashboard.py
pytest tests/test_loan_portfolio_dashboard.py::test_dashboard_loads_kpis
pytest -m performance  # Run only performance tests
pytest --cov=src --cov-report=html  # With coverage
```

## Tips for Best Results

✅ **DO:**
- Provide detailed feature context
- Answer all clarifying questions thoroughly
- Mention security/compliance requirements
- Specify performance requirements
- Include integration points

❌ **DON'T:**
- Skip clarifying questions
- Provide vague requirements
- Forget about edge cases
- Ignore security testing
- Use float for money (use Decimal!)

## Fintech Testing Checklist

When testing financial features, ALWAYS include:

- [ ] **Financial Accuracy**: Use Decimal, not float
- [ ] **PII Protection**: Mask sensitive data in logs
- [ ] **Authentication**: Verify access controls
- [ ] **Authorization**: Test role-based permissions
- [ ] **Audit Trail**: Validate transaction logging
- [ ] **Performance**: Test with realistic data volumes
- [ ] **Error Handling**: Test failure scenarios
- [ ] **Compliance**: Verify regulatory requirements

## Templates Available

Use these templates for manual test planning:

1. **Test Plan**: `docs/templates/test_plan_template.md`
2. **Test Cases**: `docs/templates/test_cases_template.md`

Copy, fill in, and customize for your needs.

## Example Output

When you ask for a test plan, you'll get something like this:

```markdown
# Test Plan: Loan Portfolio KPI Dashboard

## 1. Objectives
- Validate accuracy of KPI calculations against verified baselines
- Ensure dashboard loads within 2 seconds for 10k loans
- Verify proper authentication and authorization

## 2. Scope
- Dashboard UI components
- KPI calculation engine
- Database queries (Supabase)
- API endpoints

## 3. Out of Scope
- Admin panel (separate test plan)
- Mobile responsive design (Phase 2)

[... continues with full structure ...]
```

## Need Help?

### Documentation
- **Full Agent Guide**: `.github/agents/qa_engineer.md`
- **Usage Examples**: `.github/agents/TESTCRAFTPRO_USAGE.md`
- **Testing Docs**: `docs/testing/README.md`

### Common Questions

**Q: How do I test financial calculations?**  
A: Always use `Decimal` type, never `float`. Verify against known baselines.

```python
from decimal import Decimal, ROUND_HALF_UP

amount = Decimal('1000.00')  # ✅ Correct
amount = 1000.00  # ❌ Wrong - float!
```

**Q: How do I test PII protection?**  
A: Verify masking in all outputs:

```python
def test_pii_masking():
    result = process_loan_data(ssn="123-45-6789")
    assert "***-**-6789" in result.log
    assert "123-45-6789" not in result.log
```

**Q: How do I run only fast tests?**  
A: Use pytest markers:

```bash
pytest -m "not slow"  # Skip slow tests
pytest -m unit  # Only unit tests
pytest -m "unit and not slow"  # Fast unit tests
```

**Q: How do I test database integration?**  
A: Use the `@pytest.mark.integration` marker:

```python
@pytest.mark.integration
def test_database_query():
    """Requires SUPABASE_URL and SUPABASE_ANON_KEY"""
    result = database.query_loans()
    assert result is not None
```

## Next Steps

1. ✅ Try the agent with a small feature
2. ✅ Review the generated test plan
3. ✅ Implement a few test cases with pytest
4. ✅ Run tests and check coverage
5. ✅ Iterate and improve

## Keyboard Shortcuts

In VS Code:
- `Ctrl+Shift+P` → "Copilot: Open Chat"
- Type `@qa_engineer` to invoke the agent
- `Enter` to send message
- `Ctrl+C` to copy response

## Success Metrics

You'll know TestCraftPro is working when:
- ✅ Test plans are comprehensive and well-structured
- ✅ Test cases cover functional, security, and performance
- ✅ Fintech-specific requirements are included
- ✅ Risk assessment focuses on top priorities
- ✅ Test cases can be directly converted to pytest

## Troubleshooting

**Issue**: Agent doesn't respond  
**Solution**: Ensure GitHub Copilot is enabled and you're using `@qa_engineer` prefix

**Issue**: Generated test plan is too generic  
**Solution**: Provide more detailed answers to clarifying questions

**Issue**: Missing security/compliance tests  
**Solution**: Explicitly mention security/compliance requirements when asking

**Issue**: Tests fail in CI/CD  
**Solution**: Ensure environment variables are set (SUPABASE_URL, etc.)

## Resources

- **GitHub Copilot Docs**: https://docs.github.com/en/copilot
- **Pytest Docs**: https://docs.pytest.org/
- **Repository Testing Guide**: `docs/testing/README.md`

---

**Ready to start? Try it now!**

```
@qa_engineer Generate a test plan for [your feature]
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-31  
**Status**: Production Ready ✅
