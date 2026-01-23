# FI-ANALYTICS: Analytics Pipeline Test Cases (Sprint 1)

## Test Case ID: FI-ANALYTICS-C-01
**Test Case Title**: Figma KPI Table Sync - Success Path
**Priority**: Critical
**Type**: Functional
**Preconditions**: Valid `FIGMA_TOKEN` and `FIGMA_FILE_KEY` provided in environment.
**Tags**: #integration #figma
**Test Data Requirements**: `kpi_results.json` from Sprint 0.
**Parameters**: N/A
**Test Steps - Data - Expected Result**
1. Trigger Figma sync script with valid KPI JSON - `kpi_results.json` - Script exits code 0
2. Verify API call to Figma contains correct payload - `{"name": "Total Receivable", "value": "4.16M"}` - POST request matches expected JSON structure
3. Mock 200 OK response from Figma - N/A - Log message: "Figma update successful"

---

## Test Case ID: FI-ANALYTICS-D-01
**Test Case Title**: OTLP Span Generation and Trace Consistency
**Priority**: High
**Type**: Performance
**Preconditions**: `OTEL_EXPORTER_OTLP_ENDPOINT` configured.
**Tags**: #tracing #observability
**Test Data Requirements**: Standard loan dataset.
**Parameters**: `exporter = memory`
**Test Steps - Data - Expected Result**
1. Run pipeline with OpenTelemetry instrumentation enabled - `sample_small.csv` - Pipeline completes normally
2. Inspect In-Memory Span Exporter - N/A - Spans found for `ingestion`, `calculation`, and `export`
3. Verify all spans share the same `trace_id` - N/A - One unique Trace ID per run
4. Confirm `run_id` attribute is attached to all spans - `run_id` - Attribute present and matches JSON artifact

---

## Test Case ID: FI-ANALYTICS-F-01
**Test Case Title**: Security - Secret Masking in Logs
**Priority**: Critical
**Type**: Security
**Preconditions**: Pipeline configured with dummy secrets (e.g., `sk_test_123`).
**Tags**: #security #masking
**Test Data Requirements**: N/A
**Parameters**: `loglevel = INFO`
**Test Steps - Data - Expected Result**
1. Execute pipeline while intentionally failing an integration - `invalid_token` - Error logged in stdout
2. Search log output for the raw secret string - `"sk_test_123"` - String NOT found in logs
3. Verify masked placeholder or generic error message - N/A - Log contains "Authentication failed (token hidden)"

---

## Test Case ID: FI-ANALYTICS-C-04
**Test Case Title**: Integration Resilience - Notion API Timeout
**Priority**: Medium
**Type**: Functional
**Preconditions**: Notion integration enabled.
**Tags**: #robustness #retry
**Test Data Requirements**: N/A
**Parameters**: `timeout = 5s`, `retries = 3`
**Test Steps - Data - Expected Result**
1. Simulate 10s delay on Notion API endpoint - N/A - Pipeline detects timeout
2. Verify retry logic attempt count - N/A - Logs show 3 retry attempts
3. Confirm final "fail-soft" behavior - N/A - Pipeline continues other exports, logs Warning instead of Error

---

## Test Case ID: FI-ANALYTICS-F-02
**Test Case Title**: Unauthorized Access Handling (403 Forbidden)
**Priority**: High
**Type**: Security
**Preconditions**: Integration token with insufficient permissions.
**Tags**: #security #api
**Test Data Requirements**: N/A
**Parameters**: `status_code = 403`
**Test Steps - Data - Expected Result**
1. Attempt Meta API sync with restricted token - `restricted_token` - API returns 403
2. Verify pipeline handles status code - N/A - Pipeline logs "CRITICAL: Insufficient permissions for Meta integration"
3. Confirm exit code is non-zero - N/A - Exit code 1 (Security failure)
