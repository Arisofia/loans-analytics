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
