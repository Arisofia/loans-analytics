# Master Pre-Production Delivery Checklist

**Document Status**: P8 Documentation Remediation (2026-03-20)  
**Owner**: Head of Engineering + DevOps  
**Frequency**: Before every production release  
**Last Reviewed**: 2026-03-20

## Overview

This checklist ensures all production deployments are safe, auditable, and compliant.

---

## Phase 1: Release Preparation (1 week before)

- [ ] **Code Freeze**: No new features, only bugfixes & hotfixes (PR approval required)
- [ ] **Branch**: Create release branch `release/v<version>` from `main`
- [ ] **Changelog**: Update `CHANGELOG.md` with all user-facing changes
- [ ] **Version Bump**: Update version in `pyproject.toml`, tags
- [ ] **Dependency Audit**: Run `pip-audit` for security vulnerabilities
- [ ] **License Compliance**: Verify all new dependencies are OSI-approved or licensed

### Security Checks
- [ ] **Secrets Scan**: `git secret scan` or equivalent on all new commits
- [ ] **SAST**: SonarQube analysis must pass (no critical/high issues)
- [ ] **DAST**: API penetration testing (if applicable)
- [ ] **Credentials**: Verify no credentials in logs, .env, or codebase

---

## Phase 2: Testing & Validation (3-5 days before)

### Automated Tests
- [ ] **Unit Tests**: `pytest` — 100% pass (`make test`)
- [ ] **Type Checking**: `mypy --check-untyped-defs backend/src` passes (`make type-check`)
- [ ] **Linting**: `ruff check .` passes (`make lint`)
- [ ] **Formatting**: `black --check .` passes (`make format`)

### Integration Tests
- [ ] **Pipeline End-to-End**: Full pipeline executes on sample data
  ```bash
  python scripts/data/run_data_pipeline.py --input data/samples/loans_sample_data.csv
  ```
- [ ] **All 4 Phases**: Ingestion → Transformation → Calculation → Output complete
- [ ] **Data Integrity**: Output balances to input ± expected rounding
- [ ] **KPI Accuracy**: Spot-check 5 key KPIs against expected values

### Compliance Tests
- [ ] **Supabase Schema**: `python scripts/data/setup_supabase_tables.py --dry-run` succeeds
- [ ] **Data Governance**: All PII redaction paths active (guardrails.py)
- [ ] **Audit Trail**: Calculation run IDs recorded for every computation
- [ ] **Fail-Fast Validation**: Null handling, outlier detection working as expected

### KPI Tests
- [ ] **PAR30/PAR90**: Values within expected range (2-10% typical)
- [ ] **NPL Ratios**: Broad > strict (NPL ≥ NPL-90)
- [ ] **LTV**: Mean > 0, high-risk pct < 80%
- [ ] **Concentration**: Top-1 < 20%, Top-10 < 50%

### Performance Tests
- [ ] **Pipeline Runtime**: < 5 minutes for 10k+ loans
- [ ] **Memory Usage**: < 4GB RAM during calculation
- [ ] **Database Writes**: Supabase ingest latency < 2s per 1k records

---

## Phase 3: Staging Deployment (2-3 days before)

### Environment Setup
- [ ] **Staging Infrastructure**: All resources (DB, API, Dashboard) operational
- [ ] **Data**: Clone of production data (anonymized/masked PII) loaded to staging
- [ ] **Secrets**: All API keys, DB credentials configured (AWS Secrets Manager)
- [ ] **Monitoring**: Prometheus, Grafana dashboards connected

### Smoke Tests (Staging)
- [ ] **API Health**: `curl https://staging-api.loans.local/health` → 200 OK
- [ ] **Dashboard Load**: Streamlit dashboard loads without errors
- [ ] **Pipeline Execution**: Full pipeline runs on staging data
- [ ] **KPI Calculation**: Compare staging KPIs vs. production (variance < 0.1%)
- [ ] **Export Functionality**: CSV/Parquet exports execute successfully
- [ ] **Multi-Agent**: Agent orchestrator functional, can process queries

### Regression Tests (Staging)
- [ ] **Historical KPIs**: Match expected values from prior release
- [ ] **API Endpoints**: All endpoints respond correctly (integration tests)
- [ ] **Security**: OWASP Top 10 checks pass
- [ ] **Backward Compatibility**: Old client versions still compatible

---

## Phase 4: Production Deployment (Day of release)

### Pre-Deployment
- [ ] **Communication**: Notify stakeholders of maintenance window (if required)
- [ ] **Rollback Plan**: Document rollback steps, test them
- [ ] **Backup**: Snapshot production Supabase DB
- [ ] **On-Call**: Assign on-call engineer for 24h post-deployment

### Deployment Execution
- [ ] **Blue-Green Setup**: New (green) environment ready, parallel to prod (blue)
- [ ] **Code Deploy**: Push docker images, update K8s/ECS definitions
- [ ] **Database Migrations**: Run Supabase migrations (if applicable)
  ```bash
  python scripts/data/setup_supabase_tables.py --apply
  ```
- [ ] **Health Checks**: Wait for service readiness probes to pass
- [ ] **Traffic Cutover**: Shift traffic from blue → green (gradual or instant)
- [ ] **Verify**: Same smoke tests as staging (Phase 3)

### Post-Deployment (First 4 hours)
- [ ] **Error Monitoring**: Check logs for errors (CloudWatch, Datadog)
  - Alert thresholds: > 1% error rate
  - Alert thresholds: response time p99 > 5s
- [ ] **Data Integrity**: Run reconciliation checks
  - KPI values match staging ± 0.1%
  - All records processed without loss
  - PII redaction working (spot-check 10 records)
- [ ] **User Reporting**: Monitor support channels for incidents
- [ ] **Performance**: API response times, dashboard load time within SLA

### Incident Response
- [ ] **Critical Issue Detected**: Activate rollback (revert to blue)
  - Execute documented rollback procedure
  - Notify Head of Engineering + product team
  - Post-incident review within 24h
- [ ] **Non-Critical Issue**: Log in Jira, plan fix for next release

---

## Phase 5: Post-Release (Days 1-7)

### Monitoring & Validation
- [ ] **Daily Checks** (Days 1-3):
  - KPI calculations running on schedule
  - No errors in logs (error rate < 0.1%)
  - API response times nominal
  - Dashboard responsiveness acceptable

- [ ] **Weekly Review** (Day 7):
  - Full reconciliation: prod KPIs vs. expected values
  - Performance metrics normalized
  - No escalations from users
  - Staging matches prod (for next release testing)

### Documentation & Closure
- [ ] **Release Notes**: Published to docs/CHANGELOG.md, GitHub releases
- [ ] **Known Issues**: Document any non-critical issues for next sprint
- [ ] **Lessons Learned**: If incidents occurred, update runbooks (docs/runbook.md)
- [ ] **Team Debrief**: 15-min sync with deployment team recording what went well/poorly

### Deprecation Governance (Q2 2026)
- [ ] **P6 Checkpoint (2026-04-15)**: Confirm `backend/src/agents/multi_agent/__init__.py` has no active imports/usages
- [ ] **Removal Deadline (2026-06-30)**: Remove deprecated `backend/src/agents/multi_agent/__init__.py` and update references/docs

---

## Approval Sign-Off

Before proceeding to each phase, the following roles must approve:

| Phase | Approver(s) | Evidence |
|-------|-------------|----------|
| Release Prep | VP Engineering, Product Manager | Approval in Jira/GitHub |
| Testing | QA Lead, Head of Risk (for KPI accuracy) | Test report attached to PR |
| Staging | DevOps Lead, VP Engineering | Smoke test results |
| Production | VP Engineering, CFO (for financial KPIs) | Final approval in change log |
| Post-Release | VP Engineering | 7-day monitoring complete |

---

## Emergency Hotfix Procedure

If a critical production bug is discovered:

1. **Triage** (within 1h): Determine if hotfix required or can wait for next release
2. **Code Fix**: Create hotfix branch `hotfix/v<version>.1` from `main`
3. **Expedited Testing**: Abbreviated testing (critical path only), Head of Risk approval
4. **Staging Validation**: Deploy to staging, verify fix, compare KPIs
5. **Production Deploy**: Blue-green deploy with rollback ready
6. **Monitoring**: Continuous monitoring for 24h post-hotfix
7. **Retroactive Testing**: Full test suite run post-deployment (next business day)

**Hotfix Approval**: VP Engineering + CFO (same-day decision)

---

## Rollback Procedure

If critical issues detected post-deployment:

```bash
# 1. Immediate: Revert traffic to blue (prod-stable)
kubectl set service prod-api --image=prod:latest-stable

# 2. Restore data if necessary
python scripts/restore_supabase_backup.py --from-snapshot prod-before-release

# 3. Verify
curl https://api.loans.local/health
# Should return green

# 4. Notify stakeholders
# Issue via ops channel, public status page update

# 5. Post-mortem (within 24h)
# Review what went wrong, update runbooks
```

**Rollback Approval**: On-call engineer + VP Engineering (no CFO approval needed for rollback)

---

## Appendix: Critical Files to Review

Before each release, review these files for changes:

1. `backend/python/kpis/ssot_asset_quality.py` — Formula changes?
2. `config/kpis/` — KPI definition updates?
3. `db/migrations/` — Schema changes applied correctly?
4. `docs/KPI-Operating-Model.md` — Ownership/approval changes?
5. `CHANGELOG.md` — User-facing summary complete?
6. `.github/workflows/` — Any CI/CD changes?

---

**Last Updated**: 2026-03-20 (P8 Documentation Remediation)
