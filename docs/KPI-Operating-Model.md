<<<<<<< HEAD
# ContosoTeamStats KPI Operating Model
This playbook keeps the ContosoTeamStats platform, coaching staff, and analytics partners aligned on the KPIs that matter for each release of the .NET 6 Web API.
## Objectives and scope
- **Reliability**: Track API uptime, response latency, and error rates for roster, schedule, and notification endpoints.
- **Engagement**: Monitor daily active staff, roster updates per week, and subscription/alert opt-ins through the SendGrid/Twilio hooks.
- **Performance**: Follow win/loss ratios, points scored/allowed per game, and player availability to ensure the analytics models stay relevant to coaching decisions.
## Operating cadence
- **Weekly**: Publish KPI snapshots in the Streamlit dashboard and validate data freshness against SQL Server backups.
- **Sprint reviews**: Compare KPI movements to feature changes (e.g., messaging workflows, roster management) and capture regression notes in the Azure DevOps board.
- **Monthly**: Revisit alert thresholds and scoring formulas with coaching and data stakeholders to keep analytics and product priorities in sync.
## Roles and responsibilities
- **Engineering (ContosoTeamStats API)**: Ensure instrumentation is consistent across endpoints, keep Swagger docs in sync, and ship container images for staging/production with KPI tagging.
- **Analytics**: Maintain the Python KPI pipelines, verify data quality, and tune feature flags for experiments visible in the dashboards.
- **Coaching/Operations**: Interpret KPI changes, propose roster/strategy adjustments, and confirm alerts are actionable for game-day staff.
## Governance and alignment
- Store KPI definitions, alert thresholds, and data lineage notes alongside the .NET API configuration so contributors can trace changes.
- Pair this document with `docs/Analytics-Vision.md` to keep the KPI implementation details aligned with the broader analytics strategy.
- When AI agents contribute updates, have them reference this operating model to explain how changes affect tracking, alerts, and decision-making.
=======
# KPI Operating Model for ABACO Lending Analytics

This playbook aligns the analytics stack with commercial growth goals, enforcing traceability, compliance, and repeatable delivery across data, code, and decision-making.

## Roles and accountability

- **Data Engineering**: Owns ingestion pipelines, schema enforcement, data quality scoring, and lineage capture. Maintains catalog entries and refresh SLAs.
- **Risk & Finance Analytics**: Defines metric formulas, validates backtests, sets alert thresholds, and curates narratives for executive reporting.
- **Product & Growth**: Supplies targets, segmentation needs, and experiment hypotheses; partners on dashboard requirements and adoption KPIs.
- **Platform Engineering / DevOps**: Enforces GitHub workflows, secrets management, runtime hardening, and audit logging for deployments.
- **Governance & Compliance**: Monitors access controls, retention, PII handling, and ensures evidence exists for every KPI rollup and export.

## KPI catalog and formulas

- **Portfolio quality**: NPL%, PAR30/60/90, roll rates, cure rates, LGD/EAD estimates, expected vs. realized loss. Use consistent denominators (exposure or count) and snapshot date keys.
- **Credit conversion**: Funnel conversion, approval ratio, booked/approved ratio, time-to-yes, abandonment rate; segment by channel and cohort.
- **Unit economics**: Yield/APR (nominal and effective), cost of funds, acquisition cost per booked loan, contribution margin by segment, CLV/CAC.
- **Delinquency operations**: Promise-to-pay kept %, contact rate, right-party connect rate, collections cost per recovered dollar.
- **Growth & marketing**: Monthly/quarterly originations vs. target, campaign ROI, retention/renewal, cross-sell uptake, churn probability bands.
- **Data quality**: Null/invalid rates, freshness lag, schema drift count, ingestion success %, validation warnings per batch.

Each KPI definition includes owner, formula, data sources, refresh cadence, and controls; store these in the analytics catalog and link back to GitHub issues/PRs for traceability.

## Dashboards and visual standards

- **Executive overview**: Headline KPIs with sparkline trends, target vs. actual variances, and a risk heatmap by segment.
- **Operations**: Roll-rate cascade, DPD waterfall, collections queue performance, and exception queues with drill-through to account lists.
- **Growth**: Target gap analysis, projected trajectory (monthly interpolation), campaign-level ROI, and regional/channel treemaps.
- **Data quality**: Ingestion scorecards, schema drift alerts, and freshness timelines with SLA badges.
- **Design**: Apply the shared ABACO theme, ordered typography, and consistent number formatting; every chart lists source tables, refresh time, and owner.

## Traceability, lineage, and auditability

- Capture dataset provenance (source system, load timestamp, checksum) and store lineage metadata alongside each transformation.
- Keep metric calculations in versioned code with unit tests; reference PR numbers in the catalog. Disallow ad-hoc SQL in production dashboards.
- Emit audit logs for dashboard publishes/exports, including filters applied and user identity. Retain logs according to compliance policy.
- Tag sensitive dimensions (PII, PCI, banking secrets) and enforce column-level masking and role-based access in BI tools.

## GitHub and automation guardrails

- Require PR reviews with lint/test gates; SonarQube quality gates must pass before merge. Block commits to main without CI.
- Use conventional commits and update changelogs when KPIs or formulas change. Link issues for every dashboard or metric addition.
- Automate data validations in CI (schema checks, null/duplicate tests) and expose results as PR comments for fast triage.
- Store environment secrets in the GitHub Actions vault or cloud KMS; never commit credentials or sample PII.

## Continuous learning and runbooks

- Maintain a living playbook of incident postmortems, alert thresholds, and mitigation actions; fold learnings into tests and dashboards.
- Add notebook-to-PR pipelines that capture experiment context, datasets used, and results, ensuring reproducibility.
- Schedule quarterly KPI reviews to retire stale metrics, recalibrate thresholds, and align with evolving portfolio strategy.

## Implementation checklist

- [ ] KPI definitions recorded with owner, formula, and lineage links.
- [ ] Dashboards list data sources, refresh time, and contact person.
- [ ] CI enforces tests, lint, and security scans; SonarQube is green.
- [ ] Access controls validated for sensitive fields; audit logs stored.
- [ ] Export templates and monitoring alerts validated in staging before production rollout.
>>>>>>> main
