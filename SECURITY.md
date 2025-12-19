# Security and Audit Log

## Known Vulnerabilities

As of 2025-12-08, the following low-severity vulnerabilities are present in indirect dependencies:

- `cookie <0.7.0` (used by `@azure/static-web-apps-cli`)
- `tmp <=0.2.3` (used by `devcert`)

No fix is currently available. We are monitoring for upstream updates and will patch as soon as possible. These packages are not used in production-critical paths.

## Mitigation Plan

- Monitor for updates and apply patches when available.
- Document and review usage of affected packages.
- Ensure audit logs and traceability for all pipeline steps.
