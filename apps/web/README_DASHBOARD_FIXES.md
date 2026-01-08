# Dashboard Binding Fixes & Verification

This document lists steps to identify and fix dashboard binding regressions and to verify them via unit tests and Playwright smoke tests.

## Common binding issues

- KPI field names changed in backend vs. frontend (e.g., `portfolio_yield` vs `portfolio_yield_percent`)
- Missing sanity checks in the UI code that assume data shape

## Fix checklist

1. Verify KPI schemas in `config/kpis/*` and ensure frontend mapping in `apps/web/src/lib/exportHelpers.ts` / components uses the canonical names.
2. Add unit tests for mapping functions in `apps/web/src/lib/` and component snapshot tests.
3. Add Playwright smoke tests for dashboard KPI element presence (already present in `apps/web/e2e/dashboard-executive.spec.ts`).
4. Re-run Playwright locally (npm run test:e2e) and in CI after Playwright workflow fix.

## Verification

- Unit tests pass locally and in CI
- Playwright smoke tests pass (both locally and in CI)
- Visual check: export `figma/exports/dashboard-preview.png` and confirm dashboard preview on PR page

**Owner**: @frontend
