# TestCraftPro v2.0 Enhancements

This document outlines the v2.0 enhancements for TestCraftPro, adding advanced test automation capabilities and integrations.

## Version History

- **v1.0.0** (2026-01-31): Initial release - Core test planning and test case generation
- **v2.0.0** (2026-01-31): Advanced integrations and automation features

---

## New Features in v2.0

### 1. Test Management Tool Integration (TestRail, Zephyr)

**Purpose**: Export test plans and test cases to external test management systems.

**Usage**:

```
@qa_engineer Export this test plan to TestRail format
@qa_engineer Generate Zephyr-compatible test cases for [feature]
```

**Capabilities**:

- Convert test plans to TestRail/Zephyr CSV import format
- Generate test case IDs compatible with external systems
- Map test priorities and statuses to external tool formats
- Include traceability links to requirements

**Output Format**:

**TestRail CSV Export**:

```csv
Section,Title,Priority,Type,Estimate,References,Custom Field,Steps,Expected Result
Functional,TC-F-001: User Login,Critical,Functional,5m,REQ-123,,1. Navigate to login page,Login page displays
Functional,TC-F-001: User Login,Critical,Functional,5m,REQ-123,,2. Enter valid credentials,Credentials accepted
Functional,TC-F-001: User Login,Critical,Functional,5m,REQ-123,,3. Click login button,User redirected to dashboard
```

**Zephyr JSON Export**:

```json
{
  "project": "ABACO",
  "testCases": [
    {
      "key": "TC-F-001",
      "name": "User Login",
      "priority": "Critical",
      "status": "Draft",
      "labels": ["authentication", "functional"],
      "steps": [
        {
          "step": "Navigate to login page",
          "result": "Login page displays",
          "data": ""
        }
      ]
    }
  ]
}
```

**Implementation**:
See `docs/templates/testrail_export_template.csv` and `docs/templates/zephyr_export_template.json`

---

### 2. OpenAPI/Swagger Test Case Generation

**Purpose**: Automatically generate API test cases from OpenAPI/Swagger specifications.

**Usage**:

```
@qa_engineer Generate API test cases from openapi.yaml
@qa_engineer Create pytest tests for /api/loans endpoint from OpenAPI spec
```

**Capabilities**:

- Parse OpenAPI 3.0+ specifications
- Generate test cases for all endpoints (GET, POST, PUT, DELETE, PATCH)
- Include authentication/authorization tests
- Validate request/response schemas
- Generate positive and negative test cases
- Include edge cases (boundary values, invalid types)

**Example Output**:

From OpenAPI spec:

```yaml
paths:
  /api/loans:
    post:
      summary: Create new loan
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [amount, apr, term]
              properties:
                amount:
                  type: number
                  minimum: 1000
                  maximum: 50000
```

Generated pytest test:

```python
# tests/api/test_loans_api.py
import pytest
from decimal import Decimal

class TestLoansAPI:
    """Generated from OpenAPI spec: /api/loans"""

    @pytest.mark.api
    def test_create_loan_happy_path(self, api_client, auth_token):
        """TC-API-001: POST /api/loans - Valid loan creation"""
        payload = {
            "amount": Decimal("10000.00"),
            "apr": Decimal("0.1500"),
            "term": 12
        }

        response = api_client.post(
            "/api/loans",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201
        assert "loan_id" in response.json()

    @pytest.mark.api
    @pytest.mark.security
    def test_create_loan_no_auth(self, api_client):
        """TC-API-002: POST /api/loans - Missing authentication"""
        payload = {"amount": Decimal("10000.00"), "apr": Decimal("0.1500"), "term": 12}

        response = api_client.post("/api/loans", json=payload)

        assert response.status_code == 401

    @pytest.mark.api
    def test_create_loan_amount_boundary_min(self, api_client, auth_token):
        """TC-API-003: POST /api/loans - Minimum amount boundary"""
        payload = {"amount": Decimal("1000.00"), "apr": Decimal("0.1500"), "term": 12}

        response = api_client.post(
            "/api/loans",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 201

    @pytest.mark.api
    def test_create_loan_amount_below_min(self, api_client, auth_token):
        """TC-API-004: POST /api/loans - Amount below minimum"""
        payload = {"amount": Decimal("999.99"), "apr": Decimal("0.1500"), "term": 12}

        response = api_client.post(
            "/api/loans",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "amount" in response.json()["errors"]

    @pytest.mark.api
    def test_create_loan_missing_required_field(self, api_client, auth_token):
        """TC-API-005: POST /api/loans - Missing required field"""
        payload = {"amount": Decimal("10000.00"), "term": 12}  # Missing 'apr'

        response = api_client.post(
            "/api/loans",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 400
        assert "apr" in response.json()["errors"]
```

**Implementation**:
See `scripts/generate_api_tests_from_openapi.py`

---

### 3. Test Data Generation Templates

**Purpose**: Generate realistic synthetic test data for various testing scenarios.

**Usage**:

```
@qa_engineer Generate test data for loan portfolio testing (1000 loans)
@qa_engineer Create synthetic user data for authentication testing
```

**Capabilities**:

- Generate loan portfolio data with realistic distributions
- Create user/customer data with PII masking
- Generate payment transaction data
- Support various data formats (CSV, JSON, SQL)
- Configurable data volumes and distributions
- Preserve referential integrity

**Example Generator**:

```python
# docs/templates/test_data_generators.py
from decimal import Decimal
from datetime import datetime, timedelta
import random
import json
import csv

class LoanDataGenerator:
    """Generate synthetic loan data for testing"""

    def __init__(self, seed=42):
        random.seed(seed)

    def generate_loans(self, count=1000, output_format='csv'):
        """
        Generate synthetic loan data

        Args:
            count: Number of loans to generate
            output_format: 'csv', 'json', or 'sql'

        Returns:
            Generated data in specified format
        """
        loans = []
        statuses = ['current', 'late', 'default', 'paid_off']
        status_weights = [0.75, 0.15, 0.05, 0.05]  # Realistic distribution

        for i in range(count):
            loan = {
                'loan_id': f'LOAN-{i:06d}',
                'borrower_id': f'BORR-{random.randint(1, count//2):06d}',
                'amount': Decimal(str(random.uniform(1000, 50000))).quantize(Decimal('0.01')),
                'apr': Decimal(str(random.uniform(0.15, 0.45))).quantize(Decimal('0.0001')),
                'term_months': random.choice([6, 12, 24, 36, 48]),
                'status': random.choices(statuses, weights=status_weights)[0],
                'dpd': self._calculate_dpd(random.choices(statuses, weights=status_weights)[0]),
                'origination_date': self._random_date(365),
                'outstanding_balance': Decimal(str(random.uniform(0, 50000))).quantize(Decimal('0.01')),
                'segment': random.choice(['consumer', 'sme', 'auto'])
            }
            loans.append(loan)

        if output_format == 'csv':
            return self._to_csv(loans)
        elif output_format == 'json':
            return self._to_json(loans)
        elif output_format == 'sql':
            return self._to_sql(loans)

    def _calculate_dpd(self, status):
        """Calculate Days Past Due based on status"""
        if status == 'current':
            return 0
        elif status == 'late':
            return random.randint(1, 89)
        elif status == 'default':
            return random.randint(90, 180)
        else:
            return 0

    def _random_date(self, days_back):
        """Generate random date within last N days"""
        return datetime.now() - timedelta(days=random.randint(1, days_back))

    def _to_csv(self, loans):
        """Convert to CSV format"""
        # Implementation details...
        pass

    def _to_json(self, loans):
        """Convert to JSON format"""
        return json.dumps(loans, indent=2, default=str)

    def _to_sql(self, loans):
        """Convert to SQL INSERT statements"""
        # Implementation details...
        pass

# Usage example
generator = LoanDataGenerator(seed=42)
test_data = generator.generate_loans(count=1000, output_format='csv')
with open('data/test/loans_test_data.csv', 'w') as f:
    f.write(test_data)
```

**Available Generators**:

- `LoanDataGenerator` - Loan portfolio data
- `UserDataGenerator` - User/customer data with PII masking
- `PaymentDataGenerator` - Payment transaction data
- `KPIBaselineGenerator` - Expected KPI baseline values

**Implementation**:
See `docs/templates/test_data_generators.py`

---

### 4. Visual Regression Testing Guidance

**Purpose**: Provide comprehensive guidance for implementing visual regression testing.

**Usage**:

```
@qa_engineer How do I set up visual regression testing for the dashboard?
@qa_engineer Generate visual regression test cases for UI components
```

**Capabilities**:

- Integration with Playwright (screenshot comparison)
- Percy.io integration guidance
- Applitools Eyes integration
- Baseline image management
- Responsive design testing
- Cross-browser testing

**Visual Regression Test Example**:

```python
# tests/visual/test_dashboard_visual.py
import pytest
from playwright.sync_api import Page, expect
from pathlib import Path

class TestDashboardVisual:
    """Visual regression tests for loan portfolio dashboard"""

    @pytest.mark.visual
    def test_dashboard_landing_page_baseline(self, page: Page):
        """TC-VIS-001: Dashboard landing page visual baseline"""
        # Navigate to dashboard
        page.goto("http://localhost:3000/dashboard")

        # Wait for content to load
        page.wait_for_selector("[data-testid='kpi-cards']")

        # Take screenshot and compare to baseline
        screenshot_path = Path("tests/visual/baselines/dashboard_landing.png")
        page.screenshot(path=screenshot_path, full_page=True)

        # Visual comparison (using Percy or similar)
        # percy_snapshot(page, "Dashboard Landing Page")

    @pytest.mark.visual
    def test_dashboard_responsive_mobile(self, page: Page):
        """TC-VIS-002: Dashboard responsive layout - mobile"""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})

        page.goto("http://localhost:3000/dashboard")
        page.wait_for_selector("[data-testid='kpi-cards']")

        # Verify mobile layout adaptations
        expect(page.locator("[data-testid='sidebar']")).not_to_be_visible()
        expect(page.locator("[data-testid='mobile-menu']")).to_be_visible()

        # Visual snapshot
        page.screenshot(path="tests/visual/baselines/dashboard_mobile.png")

    @pytest.mark.visual
    def test_dashboard_kpi_card_hover_state(self, page: Page):
        """TC-VIS-003: KPI card hover state visual"""
        page.goto("http://localhost:3000/dashboard")

        # Hover over KPI card
        kpi_card = page.locator("[data-testid='kpi-par-30']")
        kpi_card.hover()

        # Wait for hover animation
        page.wait_for_timeout(500)

        # Capture hover state
        page.screenshot(path="tests/visual/baselines/kpi_card_hover.png")

    @pytest.mark.visual
    @pytest.mark.cross_browser
    def test_dashboard_cross_browser_chrome(self, browser_context):
        """TC-VIS-004: Dashboard rendering - Chrome"""
        # Test in Chrome browser
        page = browser_context.new_page()
        page.goto("http://localhost:3000/dashboard")
        page.screenshot(path="tests/visual/baselines/dashboard_chrome.png")

# Percy.io Integration Example
"""
# Install: pip install percy-playwright

from percy import percy_snapshot

@pytest.mark.visual
def test_dashboard_percy(page: Page):
    page.goto("http://localhost:3000/dashboard")

    # Automatically compares to baseline in Percy.io
    percy_snapshot(page, "Dashboard - Main View")
"""

# Applitools Eyes Integration Example
"""
# Install: pip install eyes-playwright

from applitools.playwright import Eyes, Target

@pytest.mark.visual
def test_dashboard_applitools(page: Page):
    eyes = Eyes()
    eyes.api_key = os.getenv("APPLITOOLS_API_KEY")

    try:
        eyes.open(page, "Abaco Loans", "Dashboard Test")
        page.goto("http://localhost:3000/dashboard")
        eyes.check("Dashboard Main", Target.window().fully())
        eyes.close()
    finally:
        eyes.abort()
"""
```

**Configuration**:

```yaml
# playwright.config.ts
import { defineConfig } from '@playwright/test';

export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
});
```

**Implementation**:
See `docs/templates/visual_regression_testing_guide.md`

---

### 5. Load Testing with k6/Locust Integration

**Purpose**: Generate load testing scripts for performance validation.

**Usage**:

```
@qa_engineer Generate k6 load test for loan approval API
@qa_engineer Create Locust test for dashboard with 1000 concurrent users
```

**Capabilities**:

- Generate k6 JavaScript test scripts
- Generate Locust Python test scripts
- Define load profiles (ramp-up, steady-state, spike)
- Set performance thresholds
- Monitor key metrics (response time, throughput, error rate)

**k6 Load Test Example**:

```javascript
// tests/load/loan_approval_load_test.js
// Generated by TestCraftPro for loan approval API endpoint
// Run: k6 run loan_approval_load_test.js

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

// Custom metrics
const errorRate = new Rate("errors");

// Test configuration
export const options = {
  stages: [
    { duration: "2m", target: 50 }, // Ramp up to 50 users over 2 minutes
    { duration: "5m", target: 50 }, // Stay at 50 users for 5 minutes
    { duration: "2m", target: 100 }, // Ramp up to 100 users over 2 minutes
    { duration: "5m", target: 100 }, // Stay at 100 users for 5 minutes
    { duration: "2m", target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"], // 95% of requests should be below 500ms
    http_req_failed: ["rate<0.01"], // Error rate should be less than 1%
    errors: ["rate<0.05"], // Custom error rate threshold
  },
};

// Test data
const BASE_URL = "http://localhost:3000";
const AUTH_TOKEN = __ENV.AUTH_TOKEN || "test-token";

export default function () {
  // Test: Create loan approval request
  const loanPayload = JSON.stringify({
    borrower_id: `BORR-${Math.floor(Math.random() * 10000)}`,
    amount: 10000 + Math.random() * 40000,
    apr: 0.15 + Math.random() * 0.3,
    term_months: [6, 12, 24, 36, 48][Math.floor(Math.random() * 5)],
  });

  const params = {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${AUTH_TOKEN}`,
    },
  };

  const response = http.post(
    `${BASE_URL}/api/loans/approve`,
    loanPayload,
    params,
  );

  // Validate response
  const checkResult = check(response, {
    "status is 200 or 201": (r) => r.status === 200 || r.status === 201,
    "response has loan_id": (r) => r.json("loan_id") !== undefined,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });

  errorRate.add(!checkResult);

  // Think time between requests
  sleep(1);
}

// Setup function (runs once)
export function setup() {
  console.log("Load test starting...");
  console.log(`Target: ${BASE_URL}`);
}

// Teardown function (runs once at end)
export function teardown(data) {
  console.log("Load test completed.");
}
```

**Locust Load Test Example**:

```python
# tests/load/dashboard_load_test.py
# Generated by TestCraftPro for dashboard performance testing
# Run: locust -f dashboard_load_test.py --host=http://localhost:3000

from locust import HttpUser, task, between
from decimal import Decimal
import random
import json

class DashboardUser(HttpUser):
    """Simulates user behavior on loan portfolio dashboard"""

    # Wait 1-3 seconds between tasks
    wait_time = between(1, 3)

    def on_start(self):
        """Called when a simulated user starts"""
        # Login and get auth token
        response = self.client.post("/api/auth/login", json={
            "username": f"testuser{random.randint(1, 100)}",
            "password": "testpass123"
        })

        if response.status_code == 200:
            self.token = response.json()["token"]
        else:
            self.token = None

    @task(3)
    def view_dashboard(self):
        """Most common task: View main dashboard"""
        if self.token:
            self.client.get(
                "/dashboard",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(2)
    def fetch_kpi_data(self):
        """Fetch KPI calculations"""
        if self.token:
            self.client.get(
                "/api/kpis/portfolio",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def drill_down_par_30(self):
        """Drill down into PAR-30 details"""
        if self.token:
            self.client.get(
                "/api/drilldowns/par-30",
                headers={"Authorization": f"Bearer {self.token}"}
            )

    @task(1)
    def export_report(self):
        """Export CSV report"""
        if self.token:
            self.client.post(
                "/api/reports/export",
                json={"format": "csv", "report_type": "portfolio"},
                headers={"Authorization": f"Bearer {self.token}"}
            )

# Run configurations
# Ramp up: locust -f dashboard_load_test.py --users 1000 --spawn-rate 10
# Spike test: locust -f dashboard_load_test.py --users 2000 --spawn-rate 100 --run-time 5m
# Stress test: locust -f dashboard_load_test.py --users 5000 --spawn-rate 50 --run-time 30m
```

**Implementation**:
See `docs/templates/load_testing_guide.md`

---

### 6. Test Metrics Dashboard Templates

**Purpose**: Visualize test execution results and quality metrics.

**Usage**:

```
@qa_engineer Generate test metrics dashboard configuration
@qa_engineer Create Grafana dashboard for test results
```

**Capabilities**:

- Grafana dashboard templates
- Test execution metrics (pass rate, duration, coverage)
- Quality trends over time
- Defect density tracking
- Integration with pytest-html, Allure, pytest-cov

**Grafana Dashboard Configuration**:

```json
{
  "dashboard": {
    "title": "TestCraftPro - Test Execution Metrics",
    "panels": [
      {
        "id": 1,
        "title": "Test Pass Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(tests_passed_total[5m]) / rate(tests_total[5m]) * 100"
          }
        ],
        "yaxes": [
          {
            "label": "Pass Rate %",
            "format": "percent",
            "min": 0,
            "max": 100
          }
        ]
      },
      {
        "id": 2,
        "title": "Test Execution Duration",
        "type": "graph",
        "targets": [
          {
            "expr": "test_duration_seconds"
          }
        ],
        "yaxes": [
          {
            "label": "Duration (seconds)",
            "format": "s"
          }
        ]
      },
      {
        "id": 3,
        "title": "Code Coverage Trend",
        "type": "graph",
        "targets": [
          {
            "expr": "code_coverage_percent"
          }
        ],
        "yaxes": [
          {
            "label": "Coverage %",
            "format": "percent",
            "min": 0,
            "max": 100
          }
        ]
      },
      {
        "id": 4,
        "title": "Test Categories Breakdown",
        "type": "piechart",
        "targets": [
          {
            "expr": "tests_by_category"
          }
        ]
      },
      {
        "id": 5,
        "title": "Failed Tests",
        "type": "table",
        "targets": [
          {
            "expr": "failed_tests_list"
          }
        ],
        "columns": ["Test Name", "Category", "Duration", "Error Message"]
      },
      {
        "id": 6,
        "title": "Defect Density",
        "type": "singlestat",
        "targets": [
          {
            "expr": "defects_found / lines_of_code * 1000"
          }
        ],
        "format": "none",
        "postfix": " defects/KLOC"
      }
    ]
  }
}
```

**Pytest Integration**:

```python
# conftest.py - Export metrics for Grafana
import pytest
import json
import time
from pathlib import Path

# Store test results
test_results = []

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results for metrics"""
    outcome = yield
    result = outcome.get_result()

    if result.when == 'call':
        test_results.append({
            'name': item.nodeid,
            'outcome': result.outcome,
            'duration': result.duration,
            'timestamp': time.time(),
            'category': item.get_closest_marker('category').args[0] if item.get_closest_marker('category') else 'uncategorized'
        })

def pytest_sessionfinish(session, exitstatus):
    """Export metrics after test run"""
    metrics = {
        'total_tests': len(test_results),
        'passed': sum(1 for r in test_results if r['outcome'] == 'passed'),
        'failed': sum(1 for r in test_results if r['outcome'] == 'failed'),
        'skipped': sum(1 for r in test_results if r['outcome'] == 'skipped'),
        'total_duration': sum(r['duration'] for r in test_results),
        'timestamp': time.time(),
        'pass_rate': sum(1 for r in test_results if r['outcome'] == 'passed') / len(test_results) * 100 if test_results else 0,
        'by_category': {}
    }

    # Group by category
    for result in test_results:
        cat = result['category']
        if cat not in metrics['by_category']:
            metrics['by_category'][cat] = {'total': 0, 'passed': 0, 'failed': 0}
        metrics['by_category'][cat]['total'] += 1
        if result['outcome'] == 'passed':
            metrics['by_category'][cat]['passed'] += 1
        elif result['outcome'] == 'failed':
            metrics['by_category'][cat]['failed'] += 1

    # Export to JSON for Prometheus/Grafana
    metrics_file = Path('test-results/metrics.json')
    metrics_file.parent.mkdir(exist_ok=True)
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
```

**Implementation**:
See `docs/templates/test_metrics_dashboard_config.json` and `docs/templates/test_metrics_integration.md`

---

## Usage Examples for v2.0 Features

### Example 1: OpenAPI Test Generation

```
@qa_engineer Generate pytest tests from openapi.yaml for the /api/loans endpoints
```

Expected output: Complete pytest test file with test cases for all CRUD operations, authentication, validation, and error handling.

### Example 2: Load Testing

```
@qa_engineer Create a k6 load test for the dashboard that simulates 500 concurrent users with a 5-minute ramp-up
```

Expected output: k6 JavaScript file with load profile, assertions, and performance thresholds.

### Example 3: Test Data Generation

```
@qa_engineer Generate 10,000 loan records with realistic distributions for performance testing
```

Expected output: CSV/JSON file with synthetic loan data preserving referential integrity.

### Example 4: TestRail Export

```
@qa_engineer Export the loan approval test plan to TestRail CSV format
```

Expected output: CSV file compatible with TestRail import function.

---

## Installation & Setup

### Additional Dependencies

```bash
# OpenAPI test generation
pip install openapi-spec-validator prance

# k6 (load testing)
brew install k6  # macOS
# or download from https://k6.io/docs/getting-started/installation/

# Locust (load testing)
pip install locust

# Visual regression testing
pip install playwright percy-playwright
playwright install

# Test metrics
pip install pytest-html pytest-json-report allure-pytest
```

### Configuration Files

All v2.0 templates and scripts are located in:

- `docs/templates/` - Templates for test plans, test cases, data generation
- `scripts/` - Automation scripts for test generation
- `tests/` - Example test implementations

---

## Migration from v1.0 to v2.0

**v2.0 is backward compatible** - all v1.0 features continue to work as before.

New features are opt-in and can be used by:

1. Installing additional dependencies (see above)
2. Using new invocation patterns (e.g., "@qa_engineer Generate from OpenAPI...")
3. Referencing new templates and scripts

**No changes required to existing test plans or test cases.**

---

## Support & Documentation

- **Full Guide**: `.github/agents/qa_engineer.md` (updated with v2.0 features)
- **Templates**: `docs/templates/` (all v2.0 templates)
- **Scripts**: `scripts/` (automation utilities)
- **Examples**: `.github/agents/TESTCRAFTPRO_USAGE.md` (updated)

---

**Version**: 2.0.0  
**Release Date**: 2026-01-31  
**Status**: Production Ready ✅
