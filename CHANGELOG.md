# Changelog

All notable changes to Loans Analytics are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [1.3.0] - 2026-Q1

### Added
- Phase 5 deployment-readiness guardrails (environment startup checks, release gate, migration scaffold)
- Empirical LGD computation path and Phase 3 KPI standardization tests
- Safe formula evaluation policy and security hardening checks

### Fixed
- NPL semantic definition aligned to Basel logic (DPD>=90 OR status=defaulted)
- Dependency compatibility for google-api-core/protobuf in production lock path
- .env.example misconfiguration traps (duplicate keys, unsafe defaults)

### Deprecated
- Legacy references to backend/python in docs/workflows/configuration (migrated to backend/loans_analytics)

### Security
- Hardened startup configuration checks for production mode
- Secret scanning and formula execution hardening policies reinforced

## [1.2.x] - Prior iterations
See closed pull requests on GitHub history.
