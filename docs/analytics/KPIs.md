# KPI Catalog

Each KPI includes owner, agent, source, thresholds, drill-down, runbook, and alert channel.

| KPI                 | Definition                                        | Owner            | Agent         | Source                   | Thresholds                          | Drill-down                                    | Runbook                         | Alert channel               |
| ------------------- | ------------------------------------------------- | ---------------- | ------------- | ------------------------ | ----------------------------------- | --------------------------------------------- | ------------------------------- | --------------------------- |
| NPL% / PAR30/60/90  | Outstanding balance 30/60/90+ days past due       | Risk Ops         | RiskAnalyst   | Loans fact + aging view  | Amber >3%, Red >5%                  | Delinquent accounts table with cohort filters | `runbooks/kpi-breach.md`        | Slack `#risk-alerts`, email |
| LGD / ECL           | Loss given default and expected credit loss       | Risk Modeling    | RiskAnalyst   | Models + write-off table | Red if variance >10% vs plan        | Model version comparison, segment loss curves | `runbooks/kpi-breach.md`        | Slack `#risk-alerts`, email |
| Approval Rate       | Approved apps / total apps                        | Credit Policy    | PlatformAgent | Applications fact        | Amber <40%, Red <35%                | Funnel by channel/segment                     | `runbooks/ingestion-failure.md` | Slack `#ops-alerts`         |
| Auto-decision Rate  | % auto-approved/-declined                         | Credit Ops       | PlatformAgent | Decision engine logs     | Amber <70%                          | Rule hit table, manual override queue         | `runbooks/kpi-breach.md`        | Slack `#ops-alerts`         |
| TAT (Decision)      | Median time to decision                           | Credit Ops       | PlatformAgent | Decision logs            | Red > 60s                           | Latency by step                               | `runbooks/ingestion-failure.md` | Slack `#ops-alerts`         |
| Roll Rate Matrix    | Transitions between delinquency buckets           | Collections      | Sentinel      | Payments + aging         | Red if roll-forward +5% vs baseline | Heatmap → loan list per cell                  | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| Cure Rate           | % delinquent loans cured per period               | Collections      | Sentinel      | Payments                 | Red < target by 3pp                 | Segment table (agent, bucket, cohort)         | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| Promise-to-Pay Kept | Kept PTPT / total PTPT                            | Collections      | Sentinel      | Promise logs             | Red <80%                            | Agent and borrower drill-down                 | `runbooks/kpi-breach.md`        | Slack `#collections`, email |
| CAC / LTV           | Acquisition cost vs lifetime value                | Growth           | GrowthCoach   | Marketing + repayment    | Red if CAC/LTV >0.3                 | Channel table, cohort profitability           | `runbooks/kpi-breach.md`        | Slack `#growth`             |
| Data Quality        | Freshness, completeness, duplicates, schema drift | Data Engineering | Integrator    | Pipelines + monitors     | Red if freshness >1h or null %>1%   | Failed checks, offending rows                 | `runbooks/schema-drift.md`      | Slack `#data`, email        |

## Actionability rules

- Every chart links to a drill-down table and its runbook. Next-best action is documented per KPI (collections playbook, credit tweak, data fix).
- Owners approve KPI definition changes via PRs; PR template requires “KPI impact” and “data sources touched”.
- Alerts route to the owner’s channel with SLA and runbook link; MTTR/MTTD tracked in postmortems.

## Continuous learning

- For KPI breaches or model drift: open postmortem, capture cause/fix/prevention, add tests/alerts, and record MTTR/MTTD. Link postmortem to relevant runbook.
