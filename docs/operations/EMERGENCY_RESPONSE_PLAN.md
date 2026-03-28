# 🚨 Emergency Response Plan - Production Outage

**Status**: Active runbook template for P0 production incidents.
**Owner**: DevOps / Data Engineering Lead.

---

## 1) Immediate Incident Classification (First 15 Minutes)

Classify impact using live symptoms:

| Incident ID | Symptom | Severity | Immediate Owner |
| --- | --- | --- | --- |
| PROD-API | API `/health` failing | P0 | DevOps |
| PROD-DASH | Streamlit `/_stcore/health` failing | P0 | DevOps |
| PROD-PIPE | ETL/pipeline runs failing | P0 | Data Engineering |
| PROD-DATA | KPI freshness SLA missed | P1 | Data Engineering |

---

## 2) First Response Actions (First 30 Minutes)

### A. Validate deployment workflow health

1. Open GitHub Actions and inspect latest `deploy-free-tier.yml`, `tests.yml`, and `etl-pipeline.yml` runs.
2. If deploy workflow failed, capture exact failed step and error.
3. If deployment target secrets are missing, fail closed and escalate immediately.

### B. Validate runtime endpoints

- API: `GET /health`
- Dashboard: `GET /_stcore/health`
- Data freshness: latest KPI timestamp in monitoring tables

### C. Validate image integrity

Confirm deployed services use expected GHCR `sha-<commit>` image tag.

---

## 3) Immediate Mitigation Rules

- **Do not** hotfix directly in running containers.
- **Do not** bypass failing checks by forcing traffic to stale instances.
- **Do** rollback only to previous known-good image SHA.
- **Do** keep API and dashboard on the same release SHA.

---

## 4) Rollback Procedure (Fail-Fast)

1. Identify last known-good release SHA from GitHub Actions.
2. Redeploy that exact image tag via deployment target (Render/Railway/Fly).
3. Re-run health checks.
4. Verify KPI freshness resumes.
5. Keep incident open until root cause is documented.

---

## 5) Escalation Matrix

| Scenario | Action | Escalation |
| --- | --- | --- |
| Platform remains unavailable > 30 min | Trigger rollback | Engineering Manager |
| Rollback fails | Declare SEV-1 and freeze releases | CTO |
| Data freshness still stale after recovery | Stop KPI publication | Head of Data |

---

## 6) Recovery Exit Criteria

All must be true before incident closure:

- [ ] API health endpoint returns success
- [ ] Dashboard health endpoint returns success
- [ ] Pipeline run completes without critical error
- [ ] KPI freshness is within SLA
- [ ] Post-incident notes include root cause and prevention actions

---

## 7) Post-Incident Actions (Within 24 Hours)

1. Create incident timeline (detection → mitigation → recovery).
2. Record root cause and guardrail gap.
3. Add tests/alerts preventing recurrence.
4. Link PR and workflow runs used to recover.
