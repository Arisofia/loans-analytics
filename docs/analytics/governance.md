# Analytics Governance & Traceability
Goal: every KPI, dashboard, and alert is auditable, reproducible, and mapped to accountable owners with clear decision
rights. Each change leaves a clear GitHub trail, and every dashboard element can be tied to a playbook, owner, and
rollback plan.
<<<<<<< HEAD
=======

>>>>>>> main
## Roles and decision rights (RACI-style)

- **Data Engineering (Integrator):** owns data contracts, lineage, SLAs, and PII controls; approves schema changes and incident closures related to data quality; accountable for freshness monitors.
- **Risk & Collections (RiskAnalyst, Sentinel):** own credit/collections KPIs, accept/reject threshold changes, and sign off on playbooks tied to credit policy or outreach cadence; accountable for PAR/NPL and roll-rate accuracy.
- **Growth (GrowthCoach):** owns CAC/LTV economics, channel mix assumptions, and promotion guardrails; approves funnel KPI changes and attribution methods.
- **Platform (PlatformAgent):** owns decisioning uptime, latency, and auto-decision coverage; approves any logic/policy toggle impacting TAT and approval outcomes.
- **Analytics Enablement:** maintains dashboards, alert routing tables, drill-down coverage, and documentation; enforces review checklists and GitHub workflow standards; accountable for dashboard consistency and versioning.
## KPI and dashboard change lifecycle (GitHub-first)

1. **Ticketing:** open an issue labelled `kpi-change` or `dashboard-change` with owner, scope, data sources, expected KPI movement, and guardrails (min/max expected swing).
2. **Branching:** include ticket ID in branch name; enable required checks (tests, Sonar, formatting) and code owners for affected domains. No direct pushes to default branch.
3. **Design note:** attach data lineage diagram, calculation definition, and test plan (freshness, reconciliation, and alert updates) to the ticket before implementation.
4. **PR template:** document KPI impact, data sources touched, alert updates, and rollout/rollback steps. Link to runbooks and dashboards touched; include sample screenshots for UI changes.
5. **Review gates:** at least one domain owner + Analytics Enablement approval. Sonar must show no new smells, duplicated code, or coverage drops. Validate that thresholds are parameterized, not hardcoded.
6. **Audit log:** merge commit references the ticket and includes links to dashboards, drill-down tables, and alert routes. Post-merge runbook updates and data dictionary edits ship in the same PR.
## Measurement standards

- **Lineage:** every KPI card includes source tables/views, freshness timestamp, last transformation commit SHA, and data contract link.
- **Thresholds:** stored in configuration with owner + rationale; changes require PR and alert update. Track MTTR/MTTD per KPI with weekly review of noisy alerts.
- **Drill-down coverage:** each chart has a linked table with segment filters, runbook link, and action buttons (e.g., outreach, rule tweak). No chart ships without an action path.
- **Versioning:** models, features, and KPI calculations are versioned; dashboards surface the active version, last change date, and changelog link.
- **Quality monitors:** freshness, completeness, duplicates, and schema drift checks run on every refresh; blockers create incidents with owners and ETAs.
## Compliance & security

- Enforce PII masking in drill-down tables; only role-based access can view unmasked identifiers with session-level audit logs.
- Retain alert/event logs for audit; ensure alert payloads avoid PII and include runbook URLs and correlation IDs.
- Data export/download follows least-privilege and is logged; default exports are aggregated or tokenized. Sensitive exports require time-bound access tokens.
- Secrets live in vault-backed CI/CD; .env files excluded from commits. Rotate keys after incidents and record rotations in the runbook.
## Continuous learning loop

- After breaches or incidents: publish postmortem, add automated tests/monitors, and document permanent fixes; link follow-up issues with owners and due dates.
- Quarterly: review KPI catalog for relevance, recalibrate thresholds, and archive deprecated metrics with rationale and redirect notes to successor metrics.
- Keep a "known gaps" section in dashboards to transparently show pending data sources or modeling work, with owners and target resolution dates.
## Dashboard & alert playbooks

- Exec dashboard highlights NSM, NPL/PAR trend, book growth vs target, CAC/LTV, approval rate, and ECL vs plan, each with drill-down and owner tags. Alerts route to Exec + Risk on budget variance thresholds.
- Risk Ops dashboard surfaces roll-rate matrix, PD/LGD calibration, exceptions aging, auto-decision rate, and TAT with runbook shortcuts. Red states open tickets automatically with owners pre-assigned.
- Collections dashboard tracks cure rate, promise-to-pay kept, agent productivity, and queue health with reassignment and cadence-change actions; alerts include playbook links for requeue logic.
- Product funnel dashboard monitors ingest/parse success, drop-off by step, and schema drift; alerts route to Data Engineering + Platform with payloads that exclude PII but include correlation IDs.
- Data quality dashboard displays freshness, completeness, duplicates, schema drift, and PII checks; red alerts page Data Engineering. Include drill-down to affected tables and last successful refresh time.
