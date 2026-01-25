# FI-ANALYTICS: Analytics Pipeline Test Plan (Sprint 1)

## Objectives
- Validate reliable integration with external platforms (Figma, Notion, Meta) using robust mocking.
- Ensure end-to-end tracing visibility via OTLP/OpenTelemetry for performance monitoring.
- Verify secure handling of API credentials and sensitive data (no leaks in logs/artifacts).
- Confirm graceful degradation when external services are unavailable.

## Scope
- **External Sync Scripts**: `scripts/sync_kpi_table_to_figma.py`, `scripts/notion-actions.js`, and Meta integration modules.
- **Tracing Infrastructure**: `src/tracing_setup.py` and OTLP span generation in the pipeline.
- **Security**: Secret validation logic and logging filters.
- **Error Recovery**: Retry mechanisms for transient network failures.

## Out of Scope
- Performance testing of the actual Figma/Notion/Meta APIs (rate limits excluded).
- UI testing of the external platforms themselves.
- Production-level secret rotation logic.

## Test Approach
- **Mock-Based Integration Tests**: Use `pytest-mock` or `responses` to simulate API responses and failure modes (401, 403, 429, 500).
- **Observability Validation**: Inspect OTLP spans using an in-memory exporter to verify trace parent/child relationships and attribute accuracy.
- **Secret Leak Scanning**: Automated log inspection to ensure strings matching sensitive patterns (API keys, tokens) are never persisted.
- **Negative Testing**: Force network timeouts and DNS failures to verify "fail-soft" behavior.

## Test Environment Requirements
- **Mock API Servers**: Configured for Figma/Notion/Meta endpoints.
- **OTLP Collector (Optional)**: A local Jaeger/Tempo instance for visual trace verification (for manual exploratory testing).
- **Environment Variables**: Managed via `.env.test` for secret simulation.

## Risk Assessment
- **Brittle Mocks**: Mocks may not reflect breaking changes in external APIs. *Mitigation: Periodic contract tests against live sandboxes.*
- **Tracing Overhead**: High-frequency tracing could impact pipeline performance. *Mitigation: Set sampling rates and monitor execution time.*
- **Secret Exposure**: Test secrets might accidentally leak into CI logs. *Mitigation: Use masking in GitHub Actions and scrub logs post-execution.*

## Key Checklist Items
- [ ] Figma sync handles "Token Expired" (401) with clear error messages.
- [ ] Notion integration correctly maps KPI JSON to table properties.
- [ ] OTLP spans are generated for every major pipeline stage (Ingest, Transform, Export).
- [ ] No API keys are visible in the `--verbose` log output.
- [ ] Pipeline continues (with warnings) if a non-critical integration fails.

## Test Exit Criteria
- 100% of integration mock tests passing.
- Tracing coverage confirmed for all core modules.
- Zero "Secret Leak" findings from automated log scanners.
- Documented recovery procedures for integration failures.
