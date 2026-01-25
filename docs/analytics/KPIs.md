# KPI Catalog
Each KPI includes owner, agent, source, thresholds, drill-down, runbook, and alert channel.

| KPI Name            | Definition                                        | Owner            | Agent         | Source                   | Thresholds                          | Drill-down                                    | Runbook                         | Alert channel               |
| ------------------- | ------------------------------------------------- | ---------------- | ------------- | ------------------------ | ----------------------------------- | --------------------------------------------- | ------------------------------- | --------------------------- |

## Actionability rules

- Every chart links to a drill-down table and its runbook. Next-best action is documented per KPI (collections playbook, credit tweak, data fix).
- Owners approve KPI definition changes via PRs; PR template requires “KPI impact” and “data sources touched”.
- Alerts route to the owner’s channel with SLA and runbook link; MTTR/MTTD tracked in postmortems.
## Continuous learning

- For KPI breaches or model drift: open postmortem, capture cause/fix/prevention, add tests/alerts, and record MTTR/MTTD. Link postmortem to relevant runbook.
