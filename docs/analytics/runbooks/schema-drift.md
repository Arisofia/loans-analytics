# Runbook: Schema Drift
Owner: Data Engineering | SLA: acknowledge 15m, resolve 4h | Escalate to: Data Lead, Source Owner
<<<<<<< HEAD
1) Detect: Alert from schema registry/expectations or failing transforms.
2) Contain: Freeze downstream loads for affected tables; communicate impacted KPIs.
3) Triage: Compare contract vs incoming schema; identify new/missing/renamed fields; check source change logs.
4) Fix: Map new fields, update contracts, bump version; add defaults/backfill where safe; coordinate with source owners.
5) Verify: Re-run pipeline; expectations pass; lineage updated; dashboards load without errors.
6) Learn: Postmortem; add regression tests/alerts; ensure PR template includes schema change approval.
=======

1. Detect: Alert from schema registry/expectations or failing transforms.
2. Contain: Freeze downstream loads for affected tables; communicate impacted KPIs.
3. Triage: Compare contract vs incoming schema; identify new/missing/renamed fields; check source change logs.
4. Fix: Map new fields, update contracts, bump version; add defaults/backfill where safe; coordinate with source owners.
5. Verify: Re-run pipeline; expectations pass; lineage updated; dashboards load without errors.
6. Learn: Postmortem; add regression tests/alerts; ensure PR template includes schema change approval.
>>>>>>> main
