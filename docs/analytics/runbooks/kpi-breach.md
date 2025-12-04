# Runbook: KPI Breach

Owner: KPI Owner (per catalog) | SLA: acknowledge 15m, action plan 2h | Escalate to: Product/Risk Lead

1) Detect: Alert with KPI, threshold, current value, segment, owner, next-best action link.
2) Contain: If breach is collections/risk, tighten credit or pause risky segments; notify stakeholders.
3) Triage: Check recent releases, data quality, model version, mix/seasonality changes; pull drill-down table.
4) Fix: Execute playbook (collections outreach, credit policy tweak, data fix, retrain model). Log actions.
5) Verify: KPI back in green/amber; dashboards and drill-down align; stakeholders updated.
6) Learn: Postmortem; add guardrails (alerts, tests); record MTTR/MTTD and update thresholds if needed.
