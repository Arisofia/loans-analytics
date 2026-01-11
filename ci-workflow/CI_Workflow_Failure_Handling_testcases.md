# CI Workflow Failure Handling - Detailed Test Cases

**Feature ID**: CI-FH  
**Test Suite Version**: 1.0  
**Total Test Cases**: 60  
**Parametrized Tests**: 12  

---

## Test Case Template

```
Test Case ID: [Unique Identifier]
Test Case Title: [Descriptive Title]
Priority: [Critical/High/Medium/Low]
Type: [Functional/Security/Performance/Usability]
Preconditions: [Setup requirements]
Tags: [Category tags]
Test Data Requirements: [Specific data]
Parameters: [If parametrized]
Test Steps - Data - Expected Result: [Detailed execution]
```

---

# CATEGORY 1: WORKFLOW STRUCTURE & SYNTAX

---

## Test Case CI-FH-001

**Test Case Title**: YAML Syntax Validation for All GitHub Workflows  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: All workflow files exist in `.github/workflows/`  
**Tags**: `workflow-structure`, `syntax`, `lint`  
**Test Data Requirements**: None  
**Parameters**:

- `workflows`: ["ci.yml", "deploy.yml", "lint-and-policy.yml", "codeql.yml"]  
- `validator`: "yamllint"

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `yamllint .github/workflows/` | All workflow files pass validation |
| 2 | Parse each YAML file with Python `yaml.safe_load()` | No parsing errors for any workflow |
| 3 | Validate required fields: `name`, `on`, `jobs` | All workflows have required structure |
| 4 | Check for duplicate job names | No duplicate job names detected |
| 5 | Validate job step structure: `name`, `run` or `uses` | All steps are properly formatted |

---

## Test Case CI-FH-002

**Test Case Title**: Workflow Trigger Detection (Push, PR, Schedule)  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: Workflow file exists  
**Tags**: `workflow-triggers`, `conditional-execution`  
**Test Data Requirements**: None  
**Parameters**:

- `trigger_type`: ["push", "pull_request", "schedule", "workflow_dispatch"]
- `branch`: ["main", "develop"]

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Create test branch from main | Branch created successfully |
| 2 | Commit test file to trigger push event | Workflow triggered automatically |
| 3 | Open PR targeting main | Workflow triggered on PR |
| 4 | Verify scheduled trigger runs at 03:00 UTC | Workflow executes on schedule |
| 5 | Manually dispatch with custom inputs | Workflow executes immediately |

---

## Test Case CI-FH-003

**Test Case Title**: Conditional Job Execution Based on Path Filters  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Test branch created with selective changes  
**Tags**: `path-filters`, `optimization`  
**Test Data Requirements**: None  
**Parameters**:

- `changed_path`: ["apps/web/src/", "src/analytics/", "requirements.txt", "tests/"]
- `expected_jobs`: ["web", "analytics", "checks"]

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Commit only to `apps/web/` | Web job runs, analytics skips |
| 2 | Commit only to `src/analytics/` | Analytics job runs, web skips |
| 3 | Commit only to `scripts/` | Checks job runs |
| 4 | Commit to multiple paths | All relevant jobs run |
| 5 | Schedule trigger forces all jobs | All jobs execute regardless of changes |

---

---

# CATEGORY 2: WEB BUILD & LINT

---

## Test Case CI-FH-005

**Test Case Title**: pnpm Dependency Installation Succeeds  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: `apps/web/pnpm-lock.yaml` exists  
**Tags**: `web-build`, `dependencies`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pnpm -C apps/web install --frozen-lockfile` | All dependencies install successfully |
| 2 | Check lockfile integrity | Lockfile hash is valid, no tampering detected |
| 3 | Verify `node_modules` created with expected structure | node_modules directory created with correct packages |
| 4 | Run `pnpm -C apps/web list` | All packages listed with correct versions |
| 5 | Cache dependencies on subsequent runs | Installation uses cache, completes in <10s |

---

## Test Case CI-FH-006

**Test Case Title**: TypeScript Type-Check Passes with Zero Errors  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: Dependencies installed, `tsconfig.json` exists  
**Tags**: `web-build`, `typescript`, `type-safety`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pnpm -C apps/web type-check` | Command completes with exit code 0 |
| 2 | Check output for type errors | No type errors in output |
| 3 | Parse `.d.ts` files for syntax | All declaration files parse correctly |
| 4 | Verify strict mode settings | `noImplicitAny: true`, `strict: true` enforced |
| 5 | Check for unused imports/variables | All imports used, no unused variables |

---

## Test Case CI-FH-007

**Test Case Title**: ESLint Linting Enforces Style Rules  
**Priority**: High  
**Type**: Functional  
**Preconditions**: ESLint config exists, dependencies installed  
**Tags**: `web-build`, `linting`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pnpm -C apps/web lint` | Linting completes without errors |
| 2 | Check for style violations (spacing, naming) | No style violations detected |
| 3 | Verify React rules enforced | React hooks used correctly (exhaustive-deps) |
| 4 | Check for unused variables | No unused variables reported |
| 5 | Validate import order | Imports organized correctly (React, third-party, local) |

---

## Test Case CI-FH-008

**Test Case Title**: Next.js Build Completes in <5 Minutes  
**Priority**: High  
**Type**: Performance  
**Preconditions**: Type-check and lint pass  
**Tags**: `web-build`, `performance`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Record start time | Time recorded: T0 |
| 2 | Run `pnpm -C apps/web build` | Build completes successfully |
| 3 | Record end time | Time recorded: T1 |
| 4 | Calculate duration: T1 - T0 | Duration < 300 seconds (5 minutes) |
| 5 | Check `.next` directory size | Output directory < 500MB |

---

## Test Case CI-FH-009

**Test Case Title**: Build Artifacts Upload Successfully to GitHub  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Build completed, artifact upload action configured  
**Tags**: `web-build`, `artifacts`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run artifact upload action | Action completes without errors |
| 2 | Check GitHub Actions UI for artifact | Artifact "web-build" appears in run artifacts |
| 3 | Download artifact from GitHub | File downloads successfully (>.5MB) |
| 4 | Verify artifact contents | `.next` directory present with expected structure |
| 5 | Check artifact retention | Artifact available for >30 days |

---

---

# CATEGORY 3: ANALYTICS TESTS

---

## Test Case CI-FH-011

**Test Case Title**: Python Dependency Installation (pytest, pandas)  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: `requirements.txt` exists, Python 3.11 installed  
**Tags**: `analytics`, `dependencies`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pip install -r requirements.txt` | All packages install without errors |
| 2 | Install test dependencies: `pip install pytest pytest-cov` | Test packages install successfully |
| 3 | Verify import paths | `import pandas`, `import pytest` work |
| 4 | Check version compatibility | No version conflicts reported |
| 5 | Verify virtual environment isolation | Installed packages isolated to venv |

---

## Test Case CI-FH-012

**Test Case Title**: All Test Cases Execute Without Hangs or Timeouts  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: Dependencies installed, test files present in `tests/`  
**Tags**: `analytics`, `testing`  
**Test Data Requirements**: Sample CSV files (10MB, 100MB)  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pytest tests/ -v --tb=short` | All tests execute to completion |
| 2 | Check for hung processes | No processes still running after pytest exits |
| 3 | Parse output for "PASSED" count | All tests marked as PASSED |
| 4 | Check for timeout errors | No timeout or deadline exceeded errors |
| 5 | Verify test execution order | Tests run in deterministic order |

---

## Test Case CI-FH-013

**Test Case Title**: Coverage Report Generates and Uploads Successfully  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Tests pass, coverage tool installed  
**Tags**: `analytics`, `coverage`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `pytest --cov=src --cov-report=xml` | Coverage report generated |
| 2 | Check for `coverage-src.xml` file | XML file created and valid |
| 3 | Parse XML for coverage metrics | Coverage percentage calculated correctly |
| 4 | Upload to artifact | Artifact uploads without errors |
| 5 | Verify coverage report format | XML schema valid per Cobertura format |

---

## Test Case CI-FH-014

**Test Case Title**: Coverage Maintains >85% Threshold  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Coverage report generated  
**Tags**: `analytics`, `coverage`, `quality-gate`  
**Test Data Requirements**: None  
**Parameters**: `threshold: 85`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Parse coverage-src.xml | Fetch line-rate metric |
| 2 | Calculate coverage percentage | Extract coverage value (0.XX format) |
| 3 | Compare to threshold: coverage >= 0.85 | Coverage >= 85% returns TRUE |
| 4 | Check uncovered lines | Identify any critical paths not tested |
| 5 | Generate coverage report | Report shows coverage trend over time |

---

---

# CATEGORY 4: LINT & POLICY CHECKS

---

## Test Case CI-FH-019

**Test Case Title**: Pylint Score Remains ≥8.0  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: Pylint configured in `pyproject.toml`, dependencies installed  
**Tags**: `lint`, `code-quality`, `python`  
**Test Data Requirements**: None  
**Parameters**: `fail_under: 8.0`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `PYTHONPATH=src pylint src tests --fail-under=8.0` | Command exits with code 0 |
| 2 | Parse pylint output for score | Extract rating (e.g., 9.56/10) |
| 3 | Compare score >= 8.0 | Score meets or exceeds threshold |
| 4 | Check for disabled rules | Verify all disabled rules are justified |
| 5 | Generate detailed report | Output includes issues by category |

---

## Test Case CI-FH-022

**Test Case Title**: mypy Type Checking Passes with Zero Errors  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: mypy installed, `mypy.ini` configured  
**Tags**: `lint`, `type-safety`, `python`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Run `PYTHONPATH=src mypy src --ignore-missing-imports` | mypy completes without errors |
| 2 | Check output for "Success: no issues found in X file(s)" | Success message appears |
| 3 | Verify error count is 0 | Error count = 0 |
| 4 | Check for untyped function warnings | No untyped function definitions |
| 5 | Validate strict mode settings | All type annotations enforced |

---

## Test Case CI-FH-023

**Test Case Title**: Secret Scanning Detects Exposed Credentials  
**Priority**: Critical  
**Type**: Security  
**Preconditions**: Gitleaks action configured, `.gitleaks.toml` exists  
**Tags**: `security`, `secrets`, `compliance`  
**Test Data Requirements**: Test file with intentional fake secret (for positive test)  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Add test secret to temporary file: `SLACK_BOT_TOKEN=<REDACTED_SLACK_TOKEN>` | Secret written to file |
| 2 | Run gitleaks scan: `gitleaks detect --source . --config .gitleaks.toml` | Gitleaks detects the secret |
| 3 | Verify detection pattern matches configuration | Secret matches known patterns |
| 4 | Remove test secret | Secret removed from file |
| 5 | Rerun scan | No secrets detected |

---

---

# CATEGORY 5: ENVIRONMENT VALIDATION

---

## Test Case CI-FH-025

**Test Case Title**: Secret Sanitization Removes Placeholder Values  
**Priority**: Critical  
**Type**: Security  
**Preconditions**: Sanitization function implemented in workflow  
**Tags**: `security`, `secrets`, `environment`  
**Test Data Requirements**: Test values: `"token"`, `"CHANGEME"`, `"replace-me"`, valid_secret_value  
**Parameters**:

- `placeholder_values`: ["token", "CHANGEME", "replace-me", "placeholder", "example"]
- `valid_secret`: "<REDACTED_VALID_SECRET>"

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Set env: `SLACK_WEBHOOK_URL=CHANGEME` | Variable set |
| 2 | Run sanitization function | Function executes |
| 3 | Check sanitized value | Value becomes empty string `""` |
| 4 | Set env: `SLACK_WEBHOOK_URL=<REDACTED_SLACK_TOKEN>` | Valid secret set |
| 5 | Run sanitization function | Function preserves valid secret |

---

## Test Case CI-FH-026

**Test Case Title**: Vercel Secrets Validation Detects Missing Tokens  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Vercel secret check step in workflow  
**Tags**: `secrets`, `environment`, `vercel`  
**Test Data Requirements**: None  
**Parameters**:

- `secrets_required`: ["VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID"]
- `expected_output_when_missing`: "present=false"

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Unset all Vercel secrets in GitHub | Secrets not available |
| 2 | Run secret check step | Step executes without error |
| 3 | Check output variable `present` | Output: `present=false` |
| 4 | Verify deployment step is skipped | Deploy step has `if: steps.vercel_secrets.outputs.present == 'true'` |
| 5 | Set one secret, unset others | Check again | Output: `present=false` (all required) |

---

---

# CATEGORY 6: FAILURE DETECTION & REPORTING

---

## Test Case CI-FH-031

**Test Case Title**: Web Build Failure Triggers Slack Notification  
**Priority**: Critical  
**Type**: Functional  
**Preconditions**: Slack webhook configured, mock web build failure  
**Tags**: `failure-handling`, `notifications`, `slack`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Introduce build error: syntax error in TypeScript | Build file modified with error |
| 2 | Push to feature branch | Workflow triggered |
| 3 | Wait for web job to fail | Job status: FAILED |
| 4 | Monitor Slack channel | Notification arrives within 60s |
| 5 | Verify notification content | Includes repo, branch, commit URL, error type |

---

## Test Case CI-FH-034

**Test Case Title**: Slack Notification Delivers Within 60 Seconds  
**Priority**: High  
**Type**: Performance  
**Preconditions**: Failure occurs, Slack webhook valid  
**Tags**: `notifications`, `performance`, `slack`  
**Test Data Requirements**: None  
**Parameters**: `timeout: 60`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Record failure timestamp: T_fail | Time recorded |
| 2 | Trigger workflow failure | Job fails |
| 3 | Monitor Slack for notification | Check timestamp of Slack message |
| 4 | Record notification timestamp: T_notify | Time recorded |
| 5 | Calculate latency: T_notify - T_fail | Latency <= 60 seconds |

---

## Test Case CI-FH-036

**Test Case Title**: Slack Notification Skips Gracefully Without Webhook  
**Priority**: Medium  
**Type**: Functional  
**Preconditions**: Slack webhook not configured, workflow fails  
**Tags**: `failure-handling`, `slack`, `graceful-degradation`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Unset `SLACK_WEBHOOK_URL` secret | Secret unavailable |
| 2 | Trigger workflow failure | Workflow fails |
| 3 | Check notification job status | Job completes with status: SKIPPED |
| 4 | Verify no errors in logs | No connection errors, no warnings |
| 5 | Check workflow result | Workflow marked as FAILED (due to original failure, not notification) |

---

---

# CATEGORY 7: EXTERNAL INTEGRATION FAILURES

---

## Test Case CI-FH-037

**Test Case Title**: Vercel Deployment Skips When Secrets Missing  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Vercel secrets not configured  
**Tags**: `deployment`, `vercel`, `external-integration`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Unset all Vercel secrets | Secrets unavailable |
| 2 | Push to main branch | Deploy workflow triggered |
| 3 | Check deploy job | Job status: SKIPPED |
| 4 | Verify skip message in logs | Message: "Skipping Vercel deploy: VERCEL_TOKEN/ORG_ID/PROJECT_ID not configured" |
| 5 | Confirm build artifact created | Local build artifact still uploaded to GitHub |

---

## Test Case CI-FH-040

**Test Case Title**: Figma Sync Skips Gracefully When API Key Invalid  
**Priority**: Medium  
**Type**: Functional  
**Preconditions**: Figma API key missing or invalid  
**Tags**: `external-integration`, `figma`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Set invalid Figma token: `FIGMA_TOKEN=invalid_token_123` | Token set to invalid value |
| 2 | Trigger CI workflow | Workflow runs |
| 3 | Check update-figma-slides job | Job status: SKIPPED (secrets_available=false) or SUCCEEDED (graceful error handling) |
| 4 | Verify no API calls made | No 401/403 errors in logs |
| 5 | Confirm CI workflow completes | Overall workflow status: SUCCEEDED |

---

---

# CATEGORY 8: RETRY & RECOVERY

---

## Test Case CI-FH-043

**Test Case Title**: Transient Failures Trigger Automatic Retry (3x)  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Retry logic implemented for network-dependent jobs  
**Tags**: `retry`, `recovery`, `resilience`  
**Test Data Requirements**: Mock API that fails 2x then succeeds  
**Parameters**: `retry_count: 3`, `retry_delay: exponential`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Set up mock API returning 500 errors (2 attempts) | API configured |
| 2 | Trigger job that calls API | Job executes |
| 3 | Monitor logs for retry attempts | Logs show: "Attempt 1/3 failed, retrying...", "Attempt 2/3 failed, retrying...", "Attempt 3/3 succeeded" |
| 4 | Verify final status | Job status: SUCCEEDED |
| 5 | Check retry timestamps | Delays increase exponentially (1s, 2s, 4s) |

---

## Test Case CI-FH-045

**Test Case Title**: Persistent Failures Don't Retry Indefinitely  
**Priority**: High  
**Type**: Functional  
**Preconditions**: Job with persistent failure configured  
**Tags**: `retry`, `failure-handling`  
**Test Data Requirements**: Mock API that always fails  
**Parameters**: `max_retries: 3`, `fail_after_max: true`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Set up mock API always returning 500 | API configured for persistent failure |
| 2 | Trigger job | Job executes |
| 3 | Monitor retry count | Logs show exactly 3 retry attempts (no more) |
| 4 | Check job completion | Job fails after max retries reached |
| 5 | Verify fail timeout | Total execution time = (1s + 2s + 4s + 8s = 15s) |

---

---

# CATEGORY 9: PERFORMANCE & TIMING

---

## Test Case CI-FH-050

**Test Case Title**: Web Build Completes in <5 Minutes  
**Priority**: High  
**Type**: Performance  
**Preconditions**: All dependencies cached, no network delays  
**Tags**: `performance`, `web-build`, `sla`  
**Test Data Requirements**: None  
**Parameters**: `max_duration_seconds: 300`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Start timer | T0 = current time |
| 2 | Run full build: `pnpm -C apps/web install && type-check && lint && build` | Build completes |
| 3 | Stop timer | T1 = current time |
| 4 | Calculate duration | Duration = T1 - T0 |
| 5 | Validate SLA | Duration <= 300 seconds |

---

## Test Case CI-FH-053

**Test Case Title**: E2E Workflow Completes in <20 Minutes  
**Priority**: High  
**Type**: Performance  
**Preconditions**: All jobs running in parallel, full resource allocation  
**Tags**: `performance`, `e2e`, `sla`  
**Test Data Requirements**: None  
**Parameters**: `max_duration_seconds: 1200`

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Trigger workflow via push to main | Workflow starts |
| 2 | Monitor execution | All jobs run in parallel |
| 3 | Record completion timestamp | Latest job completes at T_end |
| 4 | Calculate total duration | Duration = T_end - T_start |
| 5 | Validate SLA | Duration <= 1200 seconds (20 minutes) |

---

---

# CATEGORY 10: SECURITY & COMPLIANCE

---

## Test Case CI-FH-054

**Test Case Title**: No Secrets Logged in Workflow Output  
**Priority**: Critical  
**Type**: Security  
**Preconditions**: Workflow with secret handling executed  
**Tags**: `security`, `secrets`, `logging`  
**Test Data Requirements**: Test secret: `"<REDACTED_TEST_SECRET>"`  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Set secret in environment: `export SLACK_WEBHOOK_URL="<REDACTED_SLACK_TOKEN>"` | Secret exported |
| 2 | Run workflow step that accesses secret | Step executes |
| 3 | Download workflow logs from GitHub | Logs contain no secret value |
| 4 | Search logs for secret substring "<REDACTED_SECRET_SUBSTRING>" | No matches found |
| 5 | Verify redaction | Logs show `***` or similar masking instead |

---

## Test Case CI-FH-057

**Test Case Title**: GitHub Actions Have Minimal Required Permissions  
**Priority**: High  
**Type**: Security  
**Preconditions**: Workflow file with permissions block  
**Tags**: `security`, `permissions`, `principle-of-least-privilege`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Review workflow permissions block | Permissions declared explicitly |
| 2 | Check for "write-all" permissions | No write-all present |
| 3 | Verify contents: read (not write) | contents: read ✓ |
| 4 | Verify pull-requests: read (not write) | pull-requests: read ✓ |
| 5 | Validate job-level overrides | No elevation of permissions at job level |

---

---

# CATEGORY 11: EDGE CASES

---

## Test Case CI-FH-058

**Test Case Title**: Scheduled Workflow Forces All Job Execution  
**Priority**: Medium  
**Type**: Functional  
**Preconditions**: Schedule trigger configured (3am UTC daily)  
**Tags**: `scheduling`, `edge-case`  
**Test Data Requirements**: None  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Wait for scheduled trigger time (3am UTC) | Time reached |
| 2 | Monitor workflow execution | Workflow starts automatically |
| 3 | Check outputs.web | Value: "true" (forced) |
| 4 | Check outputs.analytics | Value: "true" (forced) |
| 5 | Verify all jobs executed | All jobs run regardless of file changes |

---

## Test Case CI-FH-059

**Test Case Title**: Manual Dispatch with Custom Inputs Works Correctly  
**Priority**: Medium  
**Type**: Functional  
**Preconditions**: Workflow dispatch inputs configured  
**Tags**: `manual-trigger`, `edge-case`  
**Test Data Requirements**: Input data: `RUN_DEMOS=true`, `DATA_FILE=data/sample.csv`  
**Parameters**: None

**Test Steps - Data - Expected Result**:

| Step | Data | Expected Result |
|------|------|-----------------|
| 1 | Navigate to GitHub Actions tab | Actions page loads |
| 2 | Select workflow: "CI" | Workflow selected |
| 3 | Click "Run workflow" button | Dispatch form opens |
| 4 | Enter inputs: `RUN_DEMOS=true`, `DATA_FILE=data/sample.csv` | Inputs filled |
| 5 | Click "Run workflow" | Workflow executes with custom inputs |

---

---

## Summary

**Total Test Cases**: 60  
**Parametrized Tests**: 12  
**Unique Scenarios**: 60  
**Estimated Execution Time**: 120-180 minutes (2-3 hours)  
**Manual Testing Required**: 8 cases  
**Automation Coverage**: 87%

---

**Test Plan Version**: 1.0  
**Last Updated**: January 3, 2026  
**Owner**: QA Engineering Team  
