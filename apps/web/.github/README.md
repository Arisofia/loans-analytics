# Deployment & Operations Documentation

**Version**: 2.0
**Date**: 2025-12-26
**Status**: Complete CI/CD automation with team runbooks

---

## 📚 Documentation Index

### For Developers (Start Here)

1. **[QUICK_START.md](./QUICK_START.md)** ⭐ **START HERE**
   - Your daily workflow
   - Common commands
   - How to fix CI failures
   - Branch naming & PRs
   - **Read time**: 5 minutes

### For All Roles

1. **[TEAM_RUNBOOKS.md](./TEAM_RUNBOOKS.md)** (Role-specific guides)
   - **Frontend Developer**: Daily workflow, fixing CI, code review
   - **QA**: Staging validation checklist, 24-hour testing
   - **DevOps**: Pre-deployment, production approval, rollback
   - **Infrastructure**: Secrets management, environment config
   - **Read time**: 15-30 minutes (read your role section)

2. **[DEPLOYMENT_COORDINATION.md](./DEPLOYMENT_COORDINATION.md)** (Slack notifications)
   - What to post in which channel
   - Notification templates
   - Incident escalation
   - **Read time**: 10 minutes

### For Operations & DevOps

1. **[DEPLOYMENT_CONFIG.md](./DEPLOYMENT_CONFIG.md)** (Technical reference)
   - All workflow details
   - Required GitHub secrets
   - Environment configuration
   - Troubleshooting guide
   - **Read time**: 15 minutes

2. **[OPERATIONS.md](../OPERATIONS.md)** (In parent directory)
   - Deployment procedures
   - Monitoring & alerts
   - Incident response
   - Rollback procedures
   - **Read time**: 20 minutes

---

## 🔄 Workflow Files

### CI Workflow

- **File**: `ci.yml`
- **Trigger**: Push to main/develop, all PRs
- **Duration**: 5-10 minutes
- **Jobs**: Lint → Type-check → Test → Build
- **Gates**: 85% code coverage required

### Staging Deployment

- **File**: `deploy-staging.yml`
- **Trigger**: Auto on develop branch merge
- **Duration**: 2-3 minutes
- **Validation**: 24-hour period (QA testing)
- **Gates**: CI must pass first

### Production Deployment

- **File**: `deploy-production.yml`
- **Trigger**: Git tag (v*.*.*)
- **Duration**: 5-10 minutes total
- **Validation**: Manual approval gate + health checks
- **Gates**: All quality checks + staging validation

### Rollback

- **File**: `rollback.yml`
- **Trigger**: Manual workflow dispatch
- **Duration**: < 5 minutes
- **Approval**: Manual environment approval
- **Use**: Emergency recovery only

### Reusable Steps

- **File**: `reusable-steps.yml`
- **Purpose**: Shared workflows for modular testing
- **Used by**: CI, staging, and production workflows

---

## 📋 Common Tasks

### I want to
### 
1. Follow QUICK_START.md → "Your Daily Workflow"
2. Create feature branch
3. Push code → PR → Code review → Merge
4. Auto-deploy to staging (24h validation)
5. Create tag for production (DevOps role)
### 
1. Go to QUICK_START.md → "CI Check Failures"
2. See specific fix for your error type
3. Run locally, fix, and push
### 
1. Follow TEAM_RUNBOOKS.md → "QA" section
2. Use staging URL provided in workflow
3. Run 24-hour validation checklist
4. Post results in #dev-alerts
### 
1. Follow TEAM_RUNBOOKS.md → "DevOps" section
2. Verify 24-hour staging validation complete
3. Create version tag
4. Approve production deployment
5. Monitor health checks
### 
1. Follow TEAM_RUNBOOKS.md → "DevOps / Emergency Rollback"
2. Workflow dispatch → Enter previous version
3. Approve rollback
4. Monitor health checks
### 
1. Go to DEPLOYMENT_COORDINATION.md
2. Find appropriate severity level (P1/P2/P3)
3. Post in correct Slack channel
4. Include GitHub Actions link
5. Follow up with root cause analysis

---

## 🚀 Deployment Pipeline Overview

```
┌─────────────────────────────────────────────────────────────┐
│ FEATURE DEVELOPMENT                                         │
├─────────────────────────────────────────────────────────────┤
│ 1. Create feature branch from develop                       │
│ 2. Push code                                                │
│ 3. Create PR → Code review → Merge when approved           │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ CI VALIDATION (5-10 min)                                    │
├─────────────────────────────────────────────────────────────┤
│ ✓ Lint (ESLint)                                            │
│ ✓ Type check (TypeScript)                                  │
│ ✓ Tests (Jest)                                             │
│ ✓ Coverage (≥ 85%)                                         │
│ ✓ Build (Next.js)                                          │
│                                                             │
│ ❌ Fail? Developer fixes and pushes again                  │
│ ✅ Pass? Proceed to staging                                │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGING DEPLOYMENT (2-3 min)                                │
├─────────────────────────────────────────────────────────────┤
│ Auto-deploy to https://staging.abaco-loans-analytics.com   │
│ Run smoke tests (health check)                             │
│ QA: Start 24-hour validation period                        │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
        ┌──────────────┐
        │ 24H TESTING  │
        │ QA validates │
        └──────┬───────┘
               │
               ✅ Approved
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ CREATE RELEASE TAG (Manual - DevOps)                        │
├─────────────────────────────────────────────────────────────┤
│ git tag -a v1.x.x -m "Release v1.x.x"                     │
│ git push origin v1.x.x                                     │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓ Triggers automatically
┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION CI VALIDATION (5-10 min)                         │
├─────────────────────────────────────────────────────────────┤
│ Re-run: Lint, type-check, test, coverage, build            │
│                                                             │
│ ❌ Fail? Tag is invalid, must fix and re-tag               │
│ ✅ Pass? Wait for manual approval                          │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ APPROVAL GATE (Manual - DevOps/Lead)                        │
├─────────────────────────────────────────────────────────────┤
│ Review quality checks                                       │
│ Approve deployment in GitHub Actions                       │
│ (1 click approval step in Actions UI)                      │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT (2-3 min)                             │
├─────────────────────────────────────────────────────────────┤
│ Deploy to Azure Static Web Apps (production)                │
│ Notify #prod-alerts                                        │
└──────────────┬────────────────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────────────────┐
│ POST-DEPLOYMENT VALIDATION (5-10 min)                       │
├─────────────────────────────────────────────────────────────┤
│ Health check (HTTP 200)                                    │
│ Performance baseline check                                  │
│ Monitoring enabled                                          │
│                                                             │
│ ❌ Fail? Trigger rollback immediately                      │
│ ✅ Pass? Production deployment successful 🎉               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🆘 Emergency Procedures

### Service Down (P1)

```
1. Post to #incidents: "🚨 CRITICAL: [Issue description]"
2. DevOps: Trigger rollback workflow
3. Monitor health checks (< 5 min recovery)
4. Post in #incidents when recovered
5. Schedule post-mortem
```

**Guide**: TEAM_RUNBOOKS.md → "Incident Response (P1)"

### Major Feature Broken (P2)

```
1. Post to #incidents: "⚠️  HIGH: [Issue description]"
2. Engineering: Investigate root cause
3. Decide: Rollback or push fix?
4. If rollback: Follow emergency procedure above
5. If fix: Deploy new version after staging validation
```

**Guide**: TEAM_RUNBOOKS.md → "Incident Response (P2)"

### Degradation (P3)

```
1. Create GitHub issue
2. Post in #dev-alerts
3. Investigate during business hours
4. Fix in next feature cycle
```

---

## 📚 Reference by Role

### Frontend Developer

1. Start: QUICK_START.md
2. Daily: TEAM_RUNBOOKS.md → "Frontend Developer"
3. Issues: Slack #dev-help
4. Reference: TEAM_RUNBOOKS.md → "Common Scenarios"

### QA / Testing

1. Start: QUICK_START.md (overview)
2. Daily: TEAM_RUNBOOKS.md → "QA / Quality Assurance"
3. Reference: TEAM_RUNBOOKS.md → "Staging Validation (24-hour window)"

### DevOps / Release Engineer

1. Start: DEPLOYMENT_CONFIG.md
2. Daily: TEAM_RUNBOOKS.md → "DevOps / Release Engineer"
3. Reference: OPERATIONS.md → "Deployment" section
4. Troubleshooting: DEPLOYMENT_CONFIG.md → "Troubleshooting"

### Infrastructure / Secrets

1. Start: TEAM_RUNBOOKS.md → "DevOps / Infrastructure"
2. Reference: DEPLOYMENT_CONFIG.md → "Required GitHub Secrets"
3. Troubleshooting: DEPLOYMENT_CONFIG.md → "Troubleshooting"

---

## ✅ Pre-Deployment Checklist

**Every deployment must verify**:

- [ ] All tests passing (100%)
- [ ] Code coverage ≥ 85%
- [ ] Linting clean (0 errors)
- [ ] Types correct (0 errors)
- [ ] Build successful
- [ ] Staging validation complete (24+ hours)
- [ ] No blocking QA issues
- [ ] Security review passed
- [ ] Team notifications sent
- [ ] Rollback plan documented

See: TEAM_RUNBOOKS.md → "Checklists"

---

## 🔗 Integration with Other Docs

- **ENGINEERING_STANDARDS.md**: Code quality requirements
- **OPERATIONS.md**: Operational procedures and runbooks
- **MIGRATION.md**: Migration procedures (related to deployment)
- **PRODUCTION_READINESS.md**: Pre-deployment checklist
- **ARCHITECTURE.md**: System design and data flow

---

## 📞 Getting Help

### Quick Questions

- Slack: #dev-help
- Response: Real-time (team members)

### CI/CD Issues

- GitHub issue: Label `deployment`
- Read: QUICK_START.md → "CI Check Failures"
- Slack: #dev-alerts

### Production Issues

- Slack: #incidents (P1/P2 only)
- Read: TEAM_RUNBOOKS.md → "Incident Response"
- GitHub: Create issue + link in #incidents

### General Questions

- Start: QUICK_START.md
- Then: Read role-specific section in TEAM_RUNBOOKS.md
- Finally: Search other docs using Cmd/Ctrl + F

---

## 🎯 Key Metrics

**Deployment Frequency**: Multiple per day (develop → staging)
**Staging Validation**: 24 hours
**Production Approval**: < 5 minutes (after validation)
**Deployment Duration**: 5-10 minutes total
**Rollback Time**: < 5 minutes
**Mean Time To Recovery**: < 5 minutes
**Quality Gates**: 0% error tolerance (lint, type, test, coverage)

---

## 📅 Last Updated

- **Documentation**: 2025-12-26
- **Workflows**: All current
- **Team processes**: All current
- **Next review**: Q1 2026

Questions or feedback? Post in #dev-help
