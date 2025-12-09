# Fintech Dashboard Web App Guide

## Purpose
This guide defines the standards, structure, and traceability requirements for all dashboards in the ABACO Lending Analytics platform.

## Dashboard Structure
- **Executive Overview:** Headline KPIs, sparkline trends, target vs. actual, risk heatmap by segment.
- **Portfolio Drilldown:** Segment-level metrics, filters, and historical trends.
- **Alert Center:** Real-time risk, compliance, and operational alerts with drilldown links.
- **Adoption & Experimentation:** User engagement, A/B test results, and feature adoption KPIs.

## Data Sources & Refresh Cadence
- List all data sources for each dashboard (e.g., loan portfolio, risk models, external APIs).
- Define refresh frequency (e.g., hourly, daily, weekly).
- Assign a data owner/contact for each dashboard.

## Visual Standards
- Use consistent color palette, typography, and layout.
- Include metric definitions, source, and last refresh timestamp.
- Provide export and audit log for every dashboard view.

## Traceability & Auditability
- Link dashboard metrics to versioned code and GitHub issues/PRs.
- Emit audit logs for dashboard publishes/exports, including filters and user identity.
- Retain logs per compliance policy.

## Compliance Checklist

- [ ] Data sources documented
- [ ] Refresh cadence defined
- [ ] Contact person assigned
- [ ] Audit logs enabled
- [ ] Metric lineage and code references included

## CI/CD Health & Compliance Automation

All code changes (pushes and pull requests) automatically trigger health and compliance checks via CI:

- **Health Check:** Runs `scripts/repo_health_check.sh` to validate repository structure, documentation, and compliance.
- **Environment Validation:** Runs `scripts/validate_and_fix_env.sh` to ensure environment, permissions, and extensions are correct.
- Results are logged in CI for every build and PR.
- If scripts are missing, CI will log a warning but continue.

This automation ensures traceability, auditability, and continuous compliance for all dashboard and analytics code.

For details, see `.github/workflows/ci.yml` and the scripts in `scripts/`.

## Contact

For dashboard support, contact: [analytics@abaco.loans](mailto:analytics@abaco.loans)
