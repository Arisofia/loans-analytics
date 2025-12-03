# Runbook: Model Rollback
Owner: Risk Modeling | SLA: acknowledge 15m, rollback 1h | Escalate to: Risk Lead, Engineering Lead
1) Trigger: Performance degradation (PD/LGD drift >10%), incidents, or failed validation.
2) Contain: Stop promotions using the bad model; pin to last good version; freeze related experiments.
3) Rollback: Deploy prior model version (MLflow/registry tag), restore feature set, clear caches; coordinate with infra.
4) Validate: Sanity checks on sample decisions; monitor KPIs (approval rate, NPL, auto-decision rate) for 24h.
5) Post-change: Rebuild/retrain with fix; add regression tests and monitoring on drift/calibration.
6) Learn: Postmortem with MTTR/MTTD; update playbooks and thresholds.
