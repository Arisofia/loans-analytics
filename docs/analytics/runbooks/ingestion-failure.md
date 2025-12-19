# Runbook: Ingestion Failure
Owner: Data Engineering | SLA: acknowledge 15m, resolve 2h | Escalate to: Data Lead, Ops
<<<<<<< HEAD
1) Detect: Alert on failed pipeline step, freshness lag >1h, or 5xx from source.
2) Contain: Pause downstream consumers; mark affected partitions; communicate status.
3) Triage: Check pipeline logs, recent schema changes, source availability, credentials.
4) Fix: Re-run with corrected config; backfill missing partitions; validate row counts and null thresholds.
5) Verify: Data quality checks pass; dashboards show expected freshness; close alert.
6) Learn: File postmortem (cause, fix, tests/alerts added, MTTR/MTTD). Link to ticket.
=======

1. Detect: Alert on failed pipeline step, freshness lag >1h, or 5xx from source.
2. Contain: Pause downstream consumers; mark affected partitions; communicate status.
3. Triage: Check pipeline logs, recent schema changes, source availability, credentials.
4. Fix: Re-run with corrected config; backfill missing partitions; validate row counts and null thresholds.
5. Verify: Data quality checks pass; dashboards show expected freshness; close alert.
6. Learn: File postmortem (cause, fix, tests/alerts added, MTTR/MTTD). Link to ticket.
>>>>>>> main
