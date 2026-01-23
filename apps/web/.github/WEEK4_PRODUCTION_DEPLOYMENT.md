# Week 4: First Production Deployment & Operations

**Version**: 2.0
**Date**: 2025-12-26
**Status**: Ready to execute
**Duration**: 4-8 hours (deployment) + ongoing operations

---

## Overview

Week 4 marks the transition from preparation to production. This guide covers:

1. **First Real Production Deployment** - Create v1.0.0 tag and deploy
2. **Monitoring & Health Checks** - Verify system health post-deployment
3. **Team Communication** - Keep stakeholders informed
4. **Metrics Tracking** - Establish baseline metrics
5. **Incident Response** - Be ready for any issues
6. **Feedback Collection** - Gather team input on process

---

## Pre-Deployment Checklist (30 min)

Before starting Week 4 deployment, verify:

### Code Quality

- [ ] Run `pnpm check-all` locally → All pass
- [ ] Run `npm test` locally → All pass
- [ ] Code coverage ≥ 85%
- [ ] No console warnings in production build
- [ ] No TODOs or FIXMEs in critical paths

### System Status

- [ ] All workflows visible in GitHub Actions
- [ ] All 7 GitHub secrets configured
- [ ] All 3 GitHub environments exist
- [ ] Staging deployment working (from Week 2 or 3)
- [ ] QA has validated staging version

### Team Readiness

- [ ] All team members read documentation
- [ ] DevOps lead is present and ready
- [ ] Team lead/manager standing by
- [ ] QA ready to monitor post-deployment
- [ ] Slack channels ready (#prod-alerts, #incidents)

### External Systems

- [ ] Supabase production database accessible
- [ ] Sentry error tracking configured
- [ ] Azure Static Web Apps health check working
- [ ] Monitoring dashboards accessible
- [ ] On-call rotation established (if applicable)

**If any item is unchecked**, do not proceed. Complete Week 3 verification first.

---

## Phase 1: Pre-Deployment (1 hour)

### 1.1 Final Code Review

Before creating the version tag:

```bash
# Ensure you're on main branch
cd /Users/jenineferderas/Documents/abaco-loans-analytics/apps/web
git checkout main
git pull origin main

# Verify last commit looks good
git log --oneline -5

# Check what's different from staging
git diff develop..main

# Verify no uncommitted changes
git status
# Should show: "On branch main" with no changes
```

**Expected**: main branch is clean and ready to tag

### 1.2 Document Release Notes

Create a release notes file for reference:

```bash
# Create release notes (optional but recommended)
cat > RELEASE_NOTES_v1.0.0.md << 'EOF'
# Release v1.0.0 - First Production Deployment

**Date**: 2025-12-26
**Deployed By**: [Your Name]
**Approval**: [Approver Name]

## What's Included
- Complete CI/CD pipeline automation
- Automated staging deployments
- Production deployment with approval gates
- Emergency rollback capability
- Team coordination procedures
- Health monitoring and checks

## Testing Status
- [ ] All CI checks passed
- [ ] All tests passed (100%)
- [ ] Code coverage ≥ 85%
- [ ] Staging validation completed
- [ ] QA sign-off obtained

## Deployment Checklist
- [ ] Pre-deployment health checks pass
- [ ] Production approval obtained
- [ ] Post-deployment health checks pass
- [ ] No errors in monitoring
- [ ] Slack notifications working

## Rollback Plan
If critical issues found:
1. Execute rollback workflow
2. Select v0.9.0 (or previous stable version)
3. Approval required
4. Verify health checks
5. Post incident report

## Success Metrics (First Hour)
- [ ] No critical errors in logs
- [ ] Health check HTTP 200
- [ ] < 3 second page load
- [ ] No Sentry errors
- [ ] Team confirms working

## Contact
- **On-Call**: [Name/Number]
- **Escalation**: [Name/Number]
- **Emergency**: #incidents Slack channel
EOF
cat RELEASE_NOTES_v1.0.0.md
```

### 1.3 Notify Team

Post in Slack channels:

**#prod-alerts**

```
🚀 PRODUCTION DEPLOYMENT STARTING

Version: v1.0.0 (First Production Deployment)
Deployed By: [Your Name]
Approval Required: Yes
Expected Duration: 10-15 minutes

Timeline:
- 15:00 UTC: Tag creation & CI runs
- 15:05 UTC: Approval gate (waiting for click)
- 15:10 UTC: Deployment starts
- 15:15 UTC: Health checks
- 15:20 UTC: Go/No-Go decision

All team members on standby.
Watch #prod-alerts for updates.
```

**#incidents** (optional, just for visibility)

```
📡 First production deployment starting

v1.0.0 - First Production Deployment

Status: PLANNED
Team: Standing by
```

---

## Phase 2: Create Version Tag (15 min)

### 2.1 Create Git Tag

```bash
# Verify main branch
git branch
# Should show: * main

# Create annotated tag (required for releases)
git tag -a v1.0.0 -m "Release v1.0.0 - First production deployment

- Complete CI/CD automation
- Staging validation complete
- Production approved for deployment
- All team onboarding complete"

# Verify tag was created
git tag -l v1.0.0

# Push tag to GitHub (this triggers deploy-production.yml workflow)
git push origin v1.0.0
```

**Expected Output**:

```
Total 0 (delta 0), reused 0 (delta 0)
To github.com:owner/repo.git
 * [new tag]         v1.0.0 -> v1.0.0
```

### 2.2 Watch Workflow Trigger

Immediately go to GitHub Actions:

1. Open: <https://github.com/owner/repo/actions>
2. You should see a new workflow run for "deploy-production.yml"
3. Watch it progress through stages:
   - ✅ pre-deployment (extract version)
   - ✅ quality-verification (re-run CI)
   - ⏳ approval-gate (WAITING FOR YOU)
   - ⏳ deploy-production (pending approval)

**Expected**: Workflow appears within 30 seconds

---

## Phase 3: Production Approval (5 min)

### 3.1 Review Approval Gate

When workflow reaches "approval-gate":

1. Click the workflow run name
2. Scroll down to "Review deployments" section
3. You should see a yellow banner: "Review pending"

### 3.2 Final Pre-Approval Check

Before clicking approval, verify:

```bash
# Double-check we tagged the right commit
git show v1.0.0
# Should show your release notes message and correct commit

# Check staging is stable (optional)
curl -s https://staging.abaco-loans-analytics.com | head -20
# Should return HTML (no 404/500)
```

### 3.3 Grant Approval

1. In the "Review pending" banner, click **Review deployments**
2. Select **production** environment
3. Check the checkbox (optional: add comment "Approved for v1.0.0")
4. Click **Approve and deploy**

**Expected**: Workflow continues to deploy-production job

### 3.4 Watch Deployment Progress

The workflow will now:

1. Build application for production
2. Deploy to Azure Static Web Apps
3. Create GitHub release
4. Run health checks
5. Notify completion

This takes 5-10 minutes.

**In the workflow logs, you should see**:

```
✅ Production health check passed
✅ Performance baseline acceptable
✅ Automatic GitHub release created
✅ Deployment successful
```

---

## Phase 4: Post-Deployment Validation (15 min)

### 4.1 Manual Health Check

```bash
# Wait 2 minutes for deployment to propagate
sleep 120

# Test production URL
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" https://abaco-loans-analytics.com
# Expected: HTTP Status: 200

# Check page loads
curl -s https://abaco-loans-analytics.com | head -30
# Should see HTML content (not error page)

# Test with browser (recommended)
# Open: https://abaco-loans-analytics.com
# Check:
# - Page loads without errors
# - No red error messages
# - Can navigate (if applicable)
# - Check browser console (F12) for errors
```

### 4.2 Check Monitoring Systems

**Sentry (Error Tracking)**

1. Go to: <https://sentry.io>
2. Navigate to your organization/project
3. Verify no new errors appeared
4. Check "Last 30 minutes" filter

**Azure Portal (Deployment Status)**

1. Go to: <https://portal.azure.com>
2. Find Static Web App
3. Check deployment status shows latest
4. Verify HTTP 200 responses in logs

**GitHub Releases**

1. Go to: <https://github.com/owner/repo/releases>
2. You should see: "Release v1.0.0"
3. Verify timestamp is recent
4. Release notes should be auto-populated

### 4.3 Team Verification

Ask team to verify in each role:

**DevOps**:

```
✓ Workflow completed successfully
✓ Health checks passed
✓ GitHub release created
✓ No errors in logs
```

**QA**:

```
✓ Application loads
✓ No JavaScript errors
✓ Core functionality works
✓ Performance acceptable
```

**Developers**:

```
✓ Your code deployed
✓ Features visible in production
✓ No console errors
```

---

## Phase 5: Monitoring (1 hour)

### 5.1 Active Monitoring (First 30 min)

Keep monitoring dashboard open and watch:

**Sentry** - Check every 5 minutes

- [ ] No new errors
- [ ] Error rate normal (or zero)
- [ ] All monitors green

**Azure** - Check every 10 minutes

- [ ] Health checks green
- [ ] HTTP response times < 1 second
- [ ] No deployment errors
- [ ] Request rate normal

**Browser** - Test every 15 minutes

- [ ] Page loads
- [ ] No console errors (F12)
- [ ] Interactive features work
- [ ] No layout shifts

### 5.2 Post-Deployment Checklist (30-60 min)

```
PRODUCTION DEPLOYMENT VERIFICATION CHECKLIST

Health Checks
[ ] HTTP 200 response
[ ] Page loads without errors
[ ] No Sentry errors
[ ] No Azure warnings
[ ] Response time < 3 seconds

Functionality Tests
[ ] Core features work
[ ] Database queries respond
[ ] Third-party integrations active (Supabase, etc.)
[ ] Navigation/routing functional
[ ] Forms submit successfully

Monitoring
[ ] Sentry showing clean logs
[ ] Azure showing healthy status
[ ] GitHub Actions workflow completed
[ ] Release page updated

Team Status
[ ] Developers confirm code deployed
[ ] QA approves functionality
[ ] DevOps confirms no issues
[ ] Tech lead gives go/no-go

Slack Notifications
[ ] #prod-alerts shows success
[ ] Team acknowledged deployment
[ ] No critical issues reported
```

**If all items checked**: ✅ Deployment Successful!

**If any item failed**: → See "Rollback Procedures" below

---

## Phase 6: Slack Notifications (Ongoing)

### 6.1 Deployment Success Notification

Post in **#prod-alerts**:

```
✅ PRODUCTION DEPLOYMENT SUCCESSFUL

Version: v1.0.0 (First Production Deployment)
Deployed By: [Your Name]
Deployment Time: 10 minutes
Status: ✅ HEALTHY

Verification Results:
✓ Health checks passed
✓ All systems green
✓ Team verified functionality
✓ Monitoring active

What's New in v1.0.0:
- Complete CI/CD automation
- Automated staging deployments
- Production deployment gates
- Emergency rollback capability
- Team coordination procedures

Rollback Available:
If critical issues found, execute rollback via:
GitHub Actions → rollback workflow → v0.9.0 → Approve

Next Steps:
- Monitor over next hour
- Watch #prod-alerts for updates
- Report any issues in #incidents

Thank you for the smooth deployment! 🎉
```

### 6.2 Ongoing Monitoring Notification

Every 30 minutes for first 2 hours, post updates:

```
📊 Production Monitoring Update (30 min post-deployment)

Status: ✅ HEALTHY
Errors: 0
Response Time: 245ms average
Health Check: ✅ Passing

All systems nominal. Deployment successful.

Next check: 30 minutes
```

### 6.3 24-Hour Stability Report

After 24 hours, post in **#prod-alerts**:

```
📈 24-Hour Stability Report - v1.0.0

Deployment Date: 2025-12-26
Version: v1.0.0
Uptime: 99.9%
Error Rate: 0%

Key Metrics:
✓ Total Requests: [XX,XXX]
✓ Average Response Time: [XXX]ms
✓ Error Count: 0
✓ Health Check Uptime: 100%

Issues Found: None
Rollback Status: Ready (not needed)

Conclusion:
v1.0.0 is stable and ready for standard operations.
First production deployment: SUCCESS ✅

Next Steps:
- Continue monitoring
- Plan next deployment
- Gather team feedback (optional retrospective)
```

---

## Rollback Procedures (If Needed)

**Use only if critical issues found immediately after deployment**

### Automatic Triggers for Rollback

Rollback should be considered if:

- [ ] HTTP errors > 10% of requests
- [ ] Response time > 10 seconds
- [ ] Critical feature completely broken
- [ ] Database connection failures
- [ ] Security incident detected

**Do NOT rollback for**:

- Minor UI issues
- Non-critical feature bugs
- Expected behavior issues
- Sentry alerts without impact

### Execute Rollback

```bash
# Open GitHub Actions
# Go to: https://github.com/owner/repo/actions
# Click: Workflows → rollback
# Click: Run workflow
# Fill in:
#   - target_version: v0.9.0 (or previous stable)
#   - environment: production
# Click: Run workflow
```

**Workflow will**:

1. Validate inputs
2. Create incident issue
3. Wait for approval
4. Check out old version
5. Deploy old version
6. Run health checks
7. Verify rollback complete

**Expected time**: < 5 minutes

### Post-Rollback

After successful rollback:

1. **Post in #incidents**:

```
🔄 ROLLBACK EXECUTED

Version Rolled Back: v1.0.0 → v0.9.0
Reason: [Brief description]
Duration: [Time to rollback]
Status: ✅ HEALTHY

Next Steps:
1. Investigate root cause
2. Fix in develop branch
3. Test in staging
4. Plan new production deployment
```

1. **Create GitHub Issue**:
   - Title: `[INCIDENT] v1.0.0 rollback - [brief description]`
   - Labels: incident, production, rollback
   - Assign to relevant team

2. **Schedule Post-Mortem**:
   - Time: Within 24 hours
   - Attendees: All team leads
   - Duration: 30 minutes
   - Focus: What happened, why, and prevention

---

## Ongoing Operations (Week 4+)

### Daily Checklist

**Every morning**:

```bash
# Check production is healthy
curl -s https://abaco-loans-analytics.com | head -10

# Check Sentry for errors (last 24h)
# Go to: https://sentry.io/projects/[your-project]
# Filter: "last 24 hours"
# Expected: No critical errors

# Check deployment history
# Go to: https://github.com/owner/repo/releases
# Verify latest version is v1.0.0

# Check workflow status
# Go to: https://github.com/owner/repo/actions
# Expected: All recent runs green
```

### Weekly Review

Every Friday:

```
[ ] Check uptime metrics
[ ] Review error logs (weekly)
[ ] Check response time trends
[ ] Review deployment frequency
[ ] Gather team feedback
[ ] Update documentation if needed
```

### Metrics Dashboard

Create a simple tracking sheet:

```
WEEK 4 OPERATIONS METRICS

Date: 2025-12-26 to 2026-01-02

Deployments:
- Production v1.0.0 created: Dec 26
- Rollbacks triggered: 0
- Deployment success rate: 100%

Performance:
- Average response time: XXXms
- 99th percentile: XXXms
- Error rate: 0%
- Uptime: 99.9%

Team Activity:
- Feature branches created: X
- PRs merged: X
- Staging deployments: X
- Production approvals: 1

Issues:
- Critical: 0
- High: 0
- Medium: X
- Low: X

Feedback:
- Team satisfaction: [1-10]
- Process improvements needed: [list]
```

---

## Team Feedback Collection (End of Week 4)

### Slack Survey (Friday)

Post in **#dev-help**:

```
📋 WEEK 4 FEEDBACK - CI/CD Pipeline

We just completed our first production deployment!
Help us improve by answering these quick questions:

1. How clear were the deployment procedures?
   [Very clear] [Clear] [Somewhat clear] [Unclear] [Very unclear]

2. What worked well?
   [Open feedback]

3. What could be improved?
   [Open feedback]

4. Any blockers or confusing parts?
   [Open feedback]

5. On a scale of 1-10, how confident do you feel about deployments?
   [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]

Please reply in thread 👇
```

### Retrospective Meeting (Optional)

Schedule 30-minute meeting:

**Agenda**:

1. (5 min) Celebrate successful first deployment
2. (10 min) What went well?
3. (10 min) What could be better?
4. (5 min) Action items for next deployment

**Discussion Points**:

- Was the documentation clear?
- Any unexpected issues?
- Time estimates accurate?
- Team confidence level?
- Process improvements?

### Document Improvements

Based on feedback:

1. Update guides if procedures unclear
2. Add FAQ section if common questions
3. Improve troubleshooting section
4. Update timelines if inaccurate
5. Add new runbooks for discovered scenarios

---

## Next Steps - Planning Week 5+

### Short-term (Next 2 weeks)

- [ ] Monitor v1.0.0 continuously (24/7)
- [ ] Gather deployment feedback
- [ ] Fix any reported issues in develop
- [ ] Plan next production release
- [ ] Team retrospective (if desired)

### Medium-term (Next month)

- [ ] Release v1.1.0 (with improvements)
- [ ] Establish monitoring alerts
- [ ] Create runbooks for common issues
- [ ] On-call rotation if not already done
- [ ] Performance optimization planning

### Long-term (Q1 2026)

- [ ] Release v2.0 (major features)
- [ ] Delete deprecated code
- [ ] Team retrospective and celebration
- [ ] Document lessons learned
- [ ] Plan Q2 roadmap

---

## Success Criteria

### Immediate (First Hour)

- [x] v1.0.0 tag created and pushed
- [x] CI pipeline passed
- [x] Manual approval granted
- [x] Deployment completed < 15 min
- [x] Health checks passed
- [x] No critical errors

### Short-term (First 24 Hours)

- [x] Uptime 99%+
- [x] Error rate < 1%
- [x] Response time < 3 seconds
- [x] No rollbacks needed
- [x] Team reports working as expected
- [x] Monitoring active

### Medium-term (First Week)

- [x] Zero critical issues
- [x] Stable 99%+ uptime
- [x] Team confident in process
- [x] Documentation proving accurate
- [x] Team feedback positive
- [x] Metrics baseline established

### Long-term (First Month)

- [x] Multiple successful deployments
- [x] Process optimized based on feedback
- [x] Team skilled in procedures
- [x] Monitoring and alerts working
- [x] Incident response practiced
- [x] Ready for v1.1.0 planning

---

## Emergency Contacts

**During Deployment**:

- DevOps Lead: [Name/Number]
- Tech Lead: [Name/Number]
- On-Call: [Name/Number]

**Escalation**:

- Critical Issues: [Name/Number]
- Rollback Approval: Tech Lead or Manager

**Communication**:

- #prod-alerts - Deployment notifications
- #incidents - Critical issues
- #dev-help - Questions and discussion

---

## Troubleshooting

### Health Check Fails (HTTP not 200)

**Symptoms**: Workflow shows red X on health check

**Steps**:

1. Wait 2 minutes (deployment might still be propagating)
2. Manually test: `curl https://abaco-loans-analytics.com`
3. Check Azure portal for deployment status
4. Check application logs for errors
5. If persists > 5 minutes, execute rollback

### Workflow Hangs on Approval

**Symptoms**: Approval gate stuck after 10+ minutes

**Steps**:

1. Refresh GitHub Actions page
2. Click workflow run → Review deployments
3. If button appears, click it
4. If button doesn't appear, check environment settings
5. Contact GitHub support if still stuck

### High Error Rate After Deploy

**Symptoms**: Sentry shows 10%+ errors, but page loads

**Steps**:

1. Check Sentry for error pattern
2. If all from same endpoint, might be expected
3. If widespread, monitor for 5 minutes
4. If persists, execute rollback
5. Investigate root cause

### Slack Notifications Not Working

**Symptoms**: No messages in #prod-alerts

**Steps**:

1. Manually post update in #prod-alerts
2. Check webhook URLs in GitHub secrets
3. Verify Slack channel exists and bot has access
4. Test webhook manually
5. Fix secrets and redeploy

---

## Checklist Summary

**Pre-Deployment**:

- [ ] Code quality verified
- [ ] System status verified
- [ ] Team readiness confirmed
- [ ] External systems accessible
- [ ] Release notes prepared
- [ ] Slack notification ready

**Deployment**:

- [ ] Git tag created
- [ ] Workflow triggered
- [ ] CI checks passed
- [ ] Approval granted
- [ ] Deployment started
- [ ] Deployment completed

**Post-Deployment**:

- [ ] Health checks passed
- [ ] Manual verification done
- [ ] Monitoring systems active
- [ ] Team verified functionality
- [ ] Slack notifications posted
- [ ] 24-hour monitoring ongoing

**Follow-up**:

- [ ] Stability report posted
- [ ] Feedback collected
- [ ] Issues documented
- [ ] Retrospective held (optional)
- [ ] Improvements planned

---

## Files for Week 4

**In `.github/` directory**:

- WEEK4_PRODUCTION_DEPLOYMENT.md (this file)
- TEAM_RUNBOOKS.md (reference for procedures)
- DEPLOYMENT_COORDINATION.md (Slack templates)
- DEPLOYMENT_CONFIG.md (technical reference)

**External**:

- GitHub Actions dashboard (workflow monitoring)
- Sentry dashboard (error tracking)
- Azure portal (deployment status)
- Slack channels (#prod-alerts, #incidents)

---

## Success! 🎉

If you've completed Week 4 following this guide, you've successfully:

✅ Created your first v1.0.0 production release
✅ Deployed to production with approval gates
✅ Verified health and functionality
✅ Established monitoring
✅ Communicated status to team
✅ Prepared rollback procedures

**You now have a production-grade CI/CD pipeline!**

Next: Plan Week 5 and future releases following established procedures.

---

**Status**: 🟢 Week 4 Ready for Execution
**Created**: 2025-12-26
**Duration**: 4-8 hours deployment + ongoing monitoring
