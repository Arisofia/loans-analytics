# Data Pipeline Validation Report

**Status**: ⚠️ **PRODUCTION-READY WITH RECOMMENDATIONS**  
**Last Updated**: 2025-12-14

## Executive Summary

The data pipelines are functional but require hardening for production robustness. Key areas for improvement include validation, error handling, and edge case coverage.

---

## Pipeline Architecture Overview

### 1. **Data Ingestion** → `analyticsProcessor.ts:parseLoanCsv()`

**Purpose**: Parse CSV loan data into structured `LoanRow[]`

**Current Implementation**:

```typescript
- Splits by newlines (/\r?\n/)
- Splits by commas
- Requires minimum 7 columns
- Maps to normalized keys
- Converts string values to numbers using regex cleanup
```

**Issues Found** ⚠️:

| Issue                           | Severity | Details                                                         |
| ------------------------------- | -------- | --------------------------------------------------------------- |
| **No CSV dialect validation**   | High     | Doesn't handle quoted fields with embedded commas/newlines      |
| **No header validation**        | High     | Assumes header row; fails silently if missing                   |
| **Regex-based number parsing**  | Medium   | Uses `/[^\d.-]/g` which may mangle negative numbers incorrectly |
| **No type coercion**            | Medium   | Returns `0` for invalid numbers; no error tracking              |
| **No duplicate/null detection** | Medium   | Silent skipping of incomplete rows                              |
| **No size limits**              | High     | Can process unlimited CSV files (DoS risk)                      |

**Recommendation**:

```typescript
// Add validation:
- Require header row with expected columns
- Validate row count before processing
- Use proper CSV parsing library (papaparse or csv-parse)
- Track parsing errors per row with line numbers
- Set max file size (e.g., 50MB)
- Validate data types strictly with Zod
```

---

### 2. **Data Transformation** → `analyticsProcessor.ts:processLoanRows()`

**Purpose**: Transform raw loan data into analytics (KPIs, visualizations)

**Current Implementation**:

```typescript
- Compute KPIs (delinquency, yield, LTV, DTI)
- Build treemap by loan_status
- Build roll-rate matrix by dpd_status
- Generate growth projections
```

**Issues Found** ⚠️:

| Issue                            | Severity | Details                                                             |
| -------------------------------- | -------- | ------------------------------------------------------------------- |
| **No null/undefined checks**     | High     | Divides by zero with `Math.max(..., 1)` fallback only               |
| **Silent data loss**             | Medium   | Filters missing dpd_status without logging                          |
| **Hardcoded thresholds**         | Medium   | Delinquency statuses hardcoded; not configurable                    |
| **Date generation logic flawed** | Medium   | Uses `Date.now() + index * 30 days` which isn't accurate for months |
| **No rounding consistency**      | Low      | Mixed precision (toFixed with different digits)                     |

**Recommendation**:

```typescript
// Add validation:
- Add explicit null/NaN checks with error tracking
- Log filtered-out rows with reasons
- Extract hardcoded thresholds to constants
- Use proper date math (date-fns/dayjs)
- Consistent decimal precision (2 digits for currency, 1 for %)
- Return validation result with warnings
```

---

### 3. **Export Functions** → `exportHelpers.ts`

**Purpose**: Convert processed analytics to CSV/JSON/Markdown

#### CSV Export (`processedAnalyticsToCSV`)

**Issues Found** ⚠️:

| Issue                             | Severity | Details                                                                    |
| --------------------------------- | -------- | -------------------------------------------------------------------------- |
| **CSV escaping incomplete**       | High     | Escapes `"`,`,`,`\r\n` but doesn't validate result                         |
| **LTV calculation unvalidated**   | Medium   | Divides by `Math.max(appraised_value, 1)` without checking loan_amount > 0 |
| **No header-body mismatch check** | Medium   | Assumes all rows have all keys                                             |
| **Silent failures**               | Medium   | Missing values become empty strings without tracking                       |

**Recommendation**:

```typescript
// Add validation:
- Use Papa Parse's CSV writer for robust escaping
- Validate LTV range (0-100%)
- Verify header count matches body columns
- Return export result with error details
- Add option to include validation warnings in output
```

#### JSON Export (`processedAnalyticsToJSON`)

**Status**: ✅ **Low Risk** - Uses `JSON.stringify()` safely

**Recommendation**:

```typescript
// Already safe, but could add:
- Strict type validation via Zod before export
- Compression option for large datasets
```

#### Markdown Export (`processedAnalyticsToMarkdown`)

**Issues Found** ⚠️:

| Issue                              | Severity | Details                                                                         |
| ---------------------------------- | -------- | ------------------------------------------------------------------------------- |
| **Markdown escaping inconsistent** | Medium   | `sanitizeMarkdownCell` escapes `\|` and backticks but not other markdown syntax |
| **Silent empty data handling**     | Low      | Returns placeholder text without structure                                      |
| **Table format assumed**           | Low      | Doesn't validate number of columns in rows                                      |

**Recommendation**:

```typescript
// Add validation:
- Use proper markdown library for escaping
- Add markdown syntax validation
- Include data completeness warnings
```

---

### 4. **Loan Data Operations** → `loanData.ts`

**Purpose**: Manage loan IDs and updates

#### ID Generation (`ensureLoanIds`)

**Issues Found** ⚠️:

| Issue                         | Severity | Details                                                                           |
| ----------------------------- | -------- | --------------------------------------------------------------------------------- |
| **Unstable ID generation**    | High     | Falls back to `Math.random()` if crypto unavailable; not cryptographically secure |
| **UUID not imported**         | Medium   | Assumes `crypto.randomUUID()` exists; no polyfill                                 |
| **Date-based collision risk** | Medium   | Fallback uses `Date.now()` which can have same value for multiple rows            |
| **No deduplication**          | High     | Doesn't check for existing IDs in array                                           |

**Recommendation**:

```typescript
// Use stable IDs:
- Use UUID v5 (deterministic) if data is stable
- Use database sequence if possible
- Add deduplication check: Set(ids) === rows.length
- Polyfill crypto.randomUUID for older browsers
- Cache generated IDs for consistency
```

#### Update Operation (`updateLoanById`)

**Issues Found** ⚠️:

| Issue                               | Severity | Details                                          |
| ----------------------------------- | -------- | ------------------------------------------------ |
| **Silent no-op on not found**       | High     | Returns original array if ID not found; no error |
| **ID reassignment possible**        | Medium   | Line 36 can reassign ID on fallback update       |
| **No validation of updated fields** | Medium   | No schema validation of partial update           |

**Recommendation**:

```typescript
// Improve reliability:
- Return Result type: { success: true; data } | { success: false; error }
- Throw error if update not found (unless flagged as optional)
- Validate updated fields against LoanRow schema
- Add dry-run mode for testing
```

---

## Data Quality Issues

### Missing Type Safety

**Status**: ⚠️ **CRITICAL**

The codebase has extensive TypeScript types (analytics.ts) but **zero runtime validation**. This creates:

1. **Silent type coercion**: CSV parser returns `LoanRow` but doesn't validate structure
2. **Missing field handling**: No check if required fields are present
3. **Invalid data acceptance**: Negative loan amounts, NaN values, etc. are silently accepted

**Recommendation**:

```typescript
// Add Zod schema validation:
import { z } from 'zod'

const LoanRowSchema = z.object({
  loan_amount: z.number().positive('Must be > 0'),
  appraised_value: z.number().positive(),
  borrower_income: z.number().nonnegative(),
  monthly_debt: z.number().nonnegative(),
  loan_status: z.string().min(1),
  interest_rate: z.number().min(0).max(100),
  principal_balance: z.number().nonnegative(),
  dpd_status: z.string().optional(),
})

// Validate all inputs:
const validated = LoanRowSchema.parse(row) // or safeParse()
```

---

### Error Handling

**Status**: 🔴 **MISSING**

No error handling in any pipeline stage:

- CSV parsing errors → silent failures
- Calculation failures (division by zero) → returns 0 or NaN
- Export failures → no error tracking
- Network errors (Supabase) → not handled

**Recommendation**:

```typescript
// Create error context:
type PipelineResult<T> =
  | { success: true; data: T; warnings: string[] }
  | { success: false; error: string; details: any }

// Track errors per stage
const result = {
  parsedRows: 1000,
  invalidRows: 15,  // with line numbers
  errors: [
    { line: 5, field: 'loan_amount', reason: 'NaN' },
    ...
  ],
  kpis: { ... }
}
```

---

## Production Checklist

### ✅ Implemented

- [x] Type definitions (TypeScript)
- [x] CSV parsing
- [x] KPI calculations
- [x] Export to JSON/CSV/Markdown
- [x] Loan ID management

### ❌ Missing (Critical)

- [ ] **Input validation** (Zod schemas)
- [ ] **Error handling** (try-catch, error context)
- [ ] **Logging** (structured logs for debugging)
- [ ] **Unit tests** (0% coverage currently)
- [ ] **Integration tests** (end-to-end pipeline)
- [ ] **Performance tests** (large dataset handling)
- [ ] **Security validation** (SQL injection in Supabase RLS, CSV injection)

### ⚠️ Medium Priority

- [ ] Rate limiting on CSV uploads
- [ ] File size limits
- [ ] Timeout handling for slow operations
- [ ] Caching of expensive calculations
- [ ] Audit logging for data changes

---

## Recommended Implementation Order

### Phase 1: Critical (Deploy ASAP)

```
1. Add Zod validation to parseLoanCsv()
2. Add error handling to processLoanRows()
3. Add input size limits
4. Add error logging to exports
5. Test with malformed CSV
```

### Phase 2: Important (Before Heavy Load)

```
6. Add unit tests for each transformation
7. Add integration test for full pipeline
8. Add performance benchmarks
9. Document error codes
10. Add monitoring/alerts
```

### Phase 3: Nice-to-Have (Future)

```
11. Add caching layer
12. Add streaming CSV parser for huge files
13. Add data lineage tracking
14. Add audit log table
15. Add data quality dashboard
```

---

## Test Data

Create test cases covering:

### Valid Data

```
✓ Minimal valid loan
✓ Maximum valid loan
✓ Zero values (allowed)
✓ Negative interest (shouldn't happen but handle gracefully)
```

### Invalid Data

```
✗ Missing columns
✗ Non-numeric loan_amount
✗ Negative loan_amount
✗ NaN/Infinity values
✗ Empty CSV
✗ Very large CSV (>100MB)
✗ Malformed quotes in CSV
✗ Unicode/special characters
```

### Edge Cases

```
⚠ All loans have same status (empty treemap)
⚠ No dpd_status provided (empty roll-rate)
⚠ Single loan (division edge cases)
⚠ Missing optional fields (dpd_status)
```

---

## Security Considerations

### CSV Injection Risk ⚠️

**Issue**: Malicious CSV could execute formulas in Excel:

```
=1+9*3       → Executes as formula
```

**Mitigation**:

```typescript
// Prefix numeric strings with single quote in CSV export
"=1+9*3" → "'=1+9*3"
```

### XSS in Markdown Export ⚠️

**Issue**: Unsanitized content in markdown could be rendered as HTML

**Mitigation**:

```typescript
// Already escaping pipes, but verify backticks don't enable code injection
// Use markdown sanitizer library (remarkable, marked with sanitize option)
```

### SQL Injection via Supabase RLS ⚠️

**Issue**: If user-provided data is used in RLS policies

**Mitigation**:

```typescript
// Verify RLS policies don't interpolate user input
// Use parameterized queries (Supabase client already does this)
```

---

## Monitoring Recommendations

### Metrics to Track

```typescript
- parseLoanCsv: input_rows, valid_rows, error_rows, parse_time_ms
- processLoanRows: input_rows, processing_time_ms, calculation_errors
- exports: format, size_bytes, generation_time_ms
```

### Alerts to Configure

```
- Parse error rate > 5%
- Processing time > 5 seconds (for <10k rows)
- Export file size > 100MB
- NaN in KPI results
```

### Sample Structured Log

```json
{
  "timestamp": "2025-12-14T12:00:00Z",
  "event": "loan_csv_parsed",
  "input_rows": 10000,
  "valid_rows": 9985,
  "invalid_rows": 15,
  "errors": [{ "row": 5, "field": "loan_amount", "value": "abc", "reason": "not_numeric" }],
  "duration_ms": 250,
  "kpis": { "delinquencyRate": 3.2, "portfolioYield": 5.8 }
}
```

---

## Conclusion

**Overall Assessment**: ✅ **Ready for MVP, needs hardening for production**

### To Ship Safely:

1. Add Zod validation to all inputs
2. Wrap pipelines in try-catch with error logging
3. Add size limits to CSV uploads
4. Deploy with Sentry error tracking
5. Monitor first week for issues

### Timeline:

- **Week 1**: Deploy with basic error handling + monitoring
- **Week 2**: Add unit tests and fix bugs found in production
- **Week 3**: Add integration tests and performance optimization
