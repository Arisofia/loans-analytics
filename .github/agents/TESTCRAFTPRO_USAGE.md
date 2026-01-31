# TestCraftPro Usage Examples

This document demonstrates how to use the TestCraftPro QA Engineer agent to generate test plans and test cases.

## Example 1: Generate Test Plan for KPI Calculation Feature

### Invocation

In GitHub Copilot Chat (VS Code):
```
@qa_engineer I need to generate a test plan for our new KPI calculation feature that processes loan portfolio data and calculates performance metrics.
```

### Expected Agent Response

The agent will first ask clarifying questions:

**TestCraftPro**: "I'd like to understand the KPI calculation feature better before creating a test plan. Let me ask a few clarifying questions:

1. **Feature Purpose & Target Users**
   - What specific KPIs are being calculated? (e.g., PAR-30, PAR-90, default rate, collection efficiency)
   - Who are the primary users? (Portfolio Managers, Risk Analysts, Operations team)
   - What business decisions will these KPIs support?

2. **Key Integration Points & Dependencies**
   - What data sources does this feature depend on? (CSV files, Supabase database, external APIs)
   - Does it integrate with the existing data pipeline (`src/pipeline/`)?
   - Are there any external dependencies or third-party services?

3. **Specific Concerns & Requirements**
   - **Performance**: What's the expected data volume? (number of loans, frequency of calculations)
   - **Security**: What sensitive data is involved? (PII in loan records)
   - **Compliance**: Any regulatory requirements for financial calculations?
   - **Accuracy**: Are there verified baseline values to test against?

4. **Test Environment & Constraints**
   - What test environments are available? (local development, CI/CD, staging)
   - Any resource constraints? (memory limits for CI, API rate limits)
   - Existing test infrastructure? (pytest, specific test data)"

After receiving answers, the agent generates a comprehensive test plan saved to `docs/testing/test_plans/kpi_calculation_test_plan.md`.

## Example 2: Create Test Cases for API Endpoint

### Invocation

```
@qa_engineer Create detailed test cases for our loan approval API endpoint (POST /api/v1/loans/approve). The endpoint requires authentication, validates loan data, and returns approval/rejection decision.
```

### Expected Agent Response

The agent will ask:

**TestCraftPro**: "Let me gather some details about the loan approval API endpoint:

1. **Feature Purpose & Target Users**
   - What criteria determine loan approval vs. rejection?
   - Who calls this API? (Internal services, external partners, UI applications)
   - What's the expected response time SLA?

2. **Key Integration Points & Dependencies**
   - Does this endpoint call external credit scoring APIs?
   - Does it update a database or queue?
   - Any notification services triggered (email, SMS)?

3. **Specific Concerns**
   - **Security**: What authentication method? (JWT, API keys, OAuth)
   - **Authorization**: What role-based permissions are required?
   - **PII**: What sensitive data is in the request/response?
   - **Idempotency**: Can the same request be safely retried?

4. **Test Environment**
   - Is there an API sandbox or mock service available?
   - Any rate limiting to consider in tests?"

After receiving answers, generates test cases saved to `docs/testing/test_cases/loan_approval_api_test_cases.md`.

## Example 3: Review Existing Test Plan

### Invocation

```
@qa_engineer Review this test plan and suggest improvements: [paste test plan content]
```

### Expected Agent Response

The agent will:
1. Analyze the test plan structure
2. Check for missing sections or gaps in coverage
3. Suggest improvements for:
   - Risk assessment (are top risks identified?)
   - Security and compliance testing
   - Performance testing with realistic data volumes
   - Financial accuracy testing (Decimal usage)
   - Integration test coverage
4. Provide specific recommendations

## Example 4: Design Performance Test Scenarios

### Invocation

```
@qa_engineer What performance tests should I include for a data pipeline that processes CSV files with loan payment data? The pipeline has 4 phases: ingestion, transformation, calculation, and output.
```

### Expected Agent Response

**TestCraftPro**: "For performance testing a 4-phase data pipeline, I recommend these test scenarios:

### Performance Test Scenarios

**TC-P-001: Baseline Performance Test**
- **Data Volume**: 10,000 records (typical daily volume)
- **Expected**: Complete processing in <30 seconds
- **Measure**: End-to-end time, phase breakdowns, memory usage

**TC-P-002: Load Test**
- **Data Volume**: 100,000 records (peak load scenario)
- **Expected**: Complete processing in <5 minutes, memory <2GB
- **Measure**: Processing throughput (records/second), memory profile

**TC-P-003: Stress Test**
- **Data Volume**: 1,000,000 records (extreme scenario)
- **Expected**: Graceful handling (streaming, batching, or failure with clear message)
- **Measure**: Memory usage, error handling, recovery

**TC-P-004: Memory Profiling**
- **Focus**: Identify memory leaks across multiple runs
- **Method**: Process 10k records 100 times, monitor memory growth
- **Expected**: Stable memory usage (no unbounded growth)

**TC-P-005: Phase-Specific Performance**
- **Test each phase individually**:
  - Ingestion: CSV parsing speed
  - Transformation: PII masking overhead
  - Calculation: KPI computation time
  - Output: File write performance
- **Goal**: Identify bottlenecks

### Test Implementation Example

```python
import pytest
import time
import tracemalloc
from decimal import Decimal

@pytest.mark.performance
def test_pipeline_baseline_performance():
    \"\"\"TC-P-001: Baseline with 10k records\"\"\"
    test_data = generate_loan_data(count=10000)
    
    tracemalloc.start()
    start_time = time.time()
    
    result = run_pipeline(test_data)
    
    duration = time.time() - start_time
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    assert result.status == "success"
    assert duration < 30.0, f"Pipeline took {duration:.2f}s, expected <30s"
    assert peak / (1024**3) < 2.0, f"Peak memory {peak/(1024**3):.2f}GB, expected <2GB"
    
    # Log metrics for trending
    print(f"Performance: {duration:.2f}s, {peak/(1024**2):.2f}MB peak memory")
```

Would you like me to generate a complete performance test plan?"

## Example 5: Security Testing for Payment Feature

### Invocation

```
@qa_engineer What security tests should I include for a payment processing feature that handles credit card transactions?
```

### Expected Agent Response

**TestCraftPro**: "For payment processing with credit card transactions, security testing is CRITICAL. Here are the essential security test cases:

### Critical Security Tests

**TC-S-001: PII Protection**
- Verify credit card numbers are masked in all logs (`****-****-****-1234`)
- Verify no PII in error messages or stack traces
- Verify PII encrypted at rest in database (PCI-DSS requirement)

**TC-S-002: Authentication & Authorization**
- Verify payment endpoint requires valid authentication token
- Verify users can only process payments for their own accounts
- Verify admin privileges required for refunds

**TC-S-003: Input Validation**
- Test for SQL injection: `' OR '1'='1`
- Test for XSS: `<script>alert('xss')</script>`
- Test for command injection: `; rm -rf /`
- Verify all inputs sanitized before processing

**TC-S-004: Idempotency**
- Verify duplicate payment requests are handled safely (idempotency keys)
- Test retry scenarios (network failures, timeouts)
- Verify no double-charging

**TC-S-005: Rate Limiting**
- Verify rate limiting on payment endpoints (prevent abuse)
- Test behavior when limit exceeded (429 Too Many Requests)

**TC-S-006: Data Integrity**
- Verify payment amounts use `Decimal` type (no float precision errors)
- Verify atomic transactions (all-or-nothing for multi-step operations)
- Verify audit trail captured (who, what, when, amount)

**TC-S-007: Secure Communication**
- Verify HTTPS only (no HTTP)
- Verify TLS 1.2+ (no outdated protocols)
- Verify certificate validation

**TC-S-008: Error Handling**
- Verify no sensitive data in error responses
- Verify errors logged securely (not exposed to users)
- Verify graceful degradation on payment gateway failures

### PCI-DSS Compliance Checklist

For credit card processing, you MUST comply with PCI-DSS:

- [ ] Cardholder data encrypted in transit (TLS 1.2+)
- [ ] Cardholder data encrypted at rest (AES-256)
- [ ] PAN (Primary Account Number) masked in logs/UI
- [ ] No storage of CVV/CVC2 after authorization
- [ ] Implement strong access controls
- [ ] Maintain audit logs for all card transactions
- [ ] Regular vulnerability scans
- [ ] Annual penetration testing

Would you like me to generate a complete security test plan with detailed test cases?"

## Best Practices for Using TestCraftPro

### 1. Start with Requirements
Always provide context when invoking the agent:
- Feature description
- User stories or acceptance criteria
- Known constraints or dependencies

### 2. Answer Clarifying Questions
The agent will ask 3-4 questions - provide detailed answers for best results.

### 3. Review and Customize
Generated test plans and cases are templates - review and customize for your specific needs.

### 4. Iterate
Use the agent multiple times:
- First for test plan
- Then for detailed test cases
- Finally for test implementation guidance

### 5. Integrate with CI/CD
Convert test cases to automated pytest tests and run in CI/CD pipeline.

## Common Use Cases

1. **New Feature Testing**: Generate comprehensive test plan for upcoming features
2. **Test Coverage Gaps**: Identify and fill gaps in existing test coverage
3. **Security Review**: Ensure adequate security and PII testing
4. **Performance Testing**: Design load and stress test scenarios
5. **Compliance Testing**: Validate regulatory requirements (PCI-DSS, GDPR, SOC 2)
6. **Integration Testing**: Plan testing for service integrations
7. **Test Improvement**: Review and enhance existing test plans

## Tips for Getting Best Results

✅ **DO**:
- Provide feature context and business requirements
- Answer clarifying questions thoroughly
- Specify any known constraints or risks
- Mention existing test infrastructure
- Include compliance or regulatory requirements

❌ **DON'T**:
- Skip the clarifying questions phase
- Provide vague or incomplete requirements
- Forget to mention security or compliance needs
- Ignore fintech-specific requirements (PII, Decimal for money)

## Next Steps

1. Try the agent in VS Code with GitHub Copilot
2. Generate a test plan for your next feature
3. Create test cases and implement with pytest
4. Review test coverage and iterate

---

**Last Updated**: 2026-01-31  
**Created by**: TestCraftPro (QA Engineer Agent)
