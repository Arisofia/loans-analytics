# Deployment Coordination Guide

**Version**: 2.0
**Date**: 2025-12-26
**Purpose**: Team communication during deployments

---

## Slack Channels

### Primary Channels

**#dev-alerts**: General development notifications

- CI check failures
- Deployment status updates
- Code review requests
- Sprint updates

**#prod-alerts**: Production-specific notifications

- Production deployments started
- Production deployments completed
- Health check results
- Performance alerts
- Incident notifications

**#incidents**: Critical incident management

- P1/P2 incidents only
- Root cause analysis
- Rollback decisions
- Recovery status

**#dev-help**: Questions and troubleshooting

- CI/CD questions
- Deployment help
- Configuration issues
- Best practices

---

## Deployment Notification Protocol

### Feature Development → Staging Deployment

**When**: Developer merges PR to develop
**Channel**: #dev-alerts

```
✅ Feature deployed to staging

Branch: develop
Feature: [Brief description of feature]
Version: auto-deployed to staging
Validator: @qa-team
Duration: 24 hours
Link: https://github.com/[owner]/[repo]/actions/runs/[run-id]

Actions:
- QA: Start 24-hour validation
- Team: Monitor for issues
```

### Staging Validation Period

**Status Update at 12h (mid-way)**
**Channel**: #dev-alerts

```
📋 Staging validation update (12h)

Version: [auto-deployed version]
Status: In progress ✅
Issues found: [0 or N]
Next: Final validation in 12h
```

### Staging Validation Complete

**When**: 24-hour window ends
**Channel**: #dev-alerts

```
✅ Staging validation complete

Version: [commit hash]
Issues: [0 blocking, X non-blocking]
Status: Ready for production
Next: Tag creation for release

QA Sign-off: @qa-lead
DevOps: Proceed with release tag when ready
```

### Production Release Started

**When**: Version tag created
**Channel**: #prod-alerts

```
🚀 Production deployment started

Version: v1.3.0
Changes: [Brief list of major changes]
QA Status: ✅ Approved
Link: https://github.com/[owner]/[repo]/actions/runs/[run-id]

Timeline:
- Quality verification: ~5 min
- Approval required: Manual step
- Deployment: ~2 min
- Health checks: ~5 min

Approver: @devops-lead
ETA completion: [Time estimate]
```

### Production Deployment - Awaiting Approval

**Channel**: #prod-alerts

```
⏳ Awaiting approval for production deployment

Version: v1.3.0
Quality Checks: ✅ All passed
Approver: @devops-lead

Action required:
1. Go to Actions tab
2. Click deploy-production workflow
3. Click "Review deployments"
4. Approve "production" environment

Estimated deploy time: 2 minutes after approval
```

### Production Deployment In Progress

**Channel**: #prod-alerts

```
🔄 Production deployment in progress

Version: v1.3.0
Status: Deploying to Azure Static Web Apps
Progress: [50% or similar]
Duration: ~2 min
Link: [GitHub Actions link]

Do not: Push new code, create tags
```

### Production Deployment Complete - Health Checks Running

**Channel**: #prod-alerts

```
✅ Deployment complete, running health checks

Version: v1.3.0
Deployed at: [Timestamp]
Status: Running automated validation
Expected: ~5 min to complete

Health checks:
- HTTP connectivity
- Page load performance
- Database connectivity
- API responses

Link: [GitHub Actions link]
```

### Production Deployment Successful

**Channel**: #prod-alerts

```
🎉 Production deployment successful

Version: v1.3.0
Deployed at: [Timestamp]
Status: ✅ All health checks passing
Live URL: https://abaco-loans-analytics.com

What's new:
- Feature X
- Bug fix Y
- Performance improvement Z

Monitoring: Active
Dashboard: [Grafana/monitoring link]
Rollback available: Yes (< 5 min if needed)

Team: Please report any issues in #dev-alerts
```

### Production Deployment Failed

**Channel**: #prod-alerts

```
❌ Production deployment failed

Version: v1.3.0
Error: [Brief error description]
Status: Rolled back to previous version
Current version: v1.2.3
Time to recovery: [X minutes]

Action required:
1. DevOps: Assess issue
2. Engineering: Root cause analysis
3. Create issue: Describe failure + fix plan

Link: [GitHub Actions link]
Investigation: #incidents
```

---

## Incident Notification Protocol

### Critical Incident (P1) - Service Down

**Channel**: #incidents (ping @on-call, @devops-lead, @engineering-lead)

```
🚨 CRITICAL INCIDENT - SERVICE DOWN

Issue: [Clear description]
Status: INVESTIGATING
Severity: P1 - Service unavailable

Time discovered: [Timestamp]
Last known good version: v1.2.3
Current version: v1.3.0 (deployed 30 min ago)

Immediate actions:
- [ ] DevOps: Trigger rollback
- [ ] Engineering: Investigate root cause
- [ ] Comms: Notify stakeholders

Link: [GitHub Actions / Error logs]
Slack thread: All updates here

Rollback command: @devops run rollback-workflow
```

### High Incident (P2) - Major Feature Broken

**Channel**: #incidents (ping relevant teams)

```
⚠️  HIGH INCIDENT - MAJOR FEATURE BROKEN

Issue: [Feature description] not working
Status: INVESTIGATING
Severity: P2 - Significant impact
Users affected: ~[estimate]

Reproduction:
1. [Step 1]
2. [Step 2]
Result: [Error or incorrect behavior]

Workaround: [If any]
Timeline: [When issue started]

Investigation lead: @engineer-name
Updates: Will post every 10 min

Link: [Issue / Error logs]
```

### Medium Incident (P3) - Degradation

**Channel**: #dev-alerts

```
⚠️  Medium issue detected

Issue: [Description]
Severity: P3 - Performance degradation
Impact: ~[% of users or features]

Details:
- What: [What's wrong]
- When: [Timeline]
- Who: [Affected users/features]
- Impact: [User-facing consequence]

Status: Monitoring
Action: Investigating root cause

Issue: [GitHub link]
```

---

## Rollback Notification Protocol

### Rollback Started

**Channel**: #prod-alerts (immediate)

```
🔄 EMERGENCY ROLLBACK STARTED

Reason: [Critical issue description]
From: v1.3.0
To: v1.2.3
Status: In progress

Timeline:
- Checkout & build: 2 min
- Deployment: 2 min
- Health checks: 2 min
Total ETA: ~5 min

Approved by: @devops-lead
Link: [GitHub Actions rollback workflow]

Do not: Push code, create tags during rollback
```

### Rollback Successful

**Channel**: #prod-alerts

```
✅ Rollback successful

From: v1.3.0 (broken)
To: v1.2.3 (stable)
Time to recovery: [X minutes]
Status: Service restored ✅

Next steps:
1. Monitor for stability
2. Investigate root cause (issue created)
3. Fix and re-test in staging
4. New release when ready

Investigation: See #incidents thread
```

### Rollback Failed

**Channel**: #incidents (CRITICAL)

```
🚨 ROLLBACK FAILED - CRITICAL

Attempted: Rollback from v1.3.0 to v1.2.3
Status: DEPLOYMENT FAILED
Severity: CRITICAL - Manual intervention required

Last known status: [Details]
Error: [Error message]

Immediate action:
- [ ] DevOps: Check Azure deployment history
- [ ] Try manual rollback (see OPERATIONS.md)
- [ ] Page on-call engineer

Contact: @devops-lead @engineering-lead
Emergency escalation: [Phone number / escalation procedure]

Link: [GitHub Actions error logs]
```

---

## Status Update Timeline

### During Deployment

**Every 2-5 minutes**: Status update with emoji

- 🔄 In progress
- ⏳ Awaiting action
- ✅ Step complete
- ❌ Failed

### During Incident

**Every 5-10 minutes**: Status update

- Investigation progress
- Estimated time to resolution
- Actions being taken
- Next steps

### Resolution

**Immediate**: Post final status

- ✅ Resolved / ❌ Escalated
- Timeline from issue discovery
- What was done
- Post-mortem planned

---

## Message Template Library

### Feature Branch Ready for Merge

```
📋 Ready for review: [Feature name]

Branch: feature/[name]
Author: @author
Changes: [Brief description]
Tests: [N new, M updated]
Coverage: [Percentage]

Please review: @reviewer-1 @reviewer-2
Link: [PR link]
```

### Code Review Approval

```
✅ Approved: [Feature name]

Reviewer: @reviewer
Quality: Excellent
Tests: Comprehensive
Types: Complete

Ready to merge into develop
```

### Code Review Request Changes

```
🔄 Changes requested: [Feature name]

Reviewer: @reviewer
Issue: [Description of concern]
Severity: [Blocking / Nice-to-have]

Please address and push updates
CI will re-run automatically
Link: [PR link with comments]
```

---

## Communication Best Practices

### DO

✅ Post updates in correct channel
✅ Use clear, concise language
✅ Include relevant links
✅ Mention specific people when action needed
✅ Update regularly during deployments/incidents
✅ Tag issues/PRs properly
✅ Use emoji for quick status scanning

### DON'T

❌ Post secrets or API keys
❌ Spam multiple channels with same message
❌ Use all-caps (unless CRITICAL)
❌ Post personal opinions in official channels
❌ Ignore incidents for > 5 minutes
❌ Deploy without notifying team
❌ Mix incident and non-incident discussions

---

## Channel Etiquette

### #prod-alerts

**Purpose**: Production notifications only
**Ping**: Yes (relevant teams)
**Frequency**: As needed (quality > quantity)
**Urgency**: High
**Audience**: DevOps, engineering leads, on-call

### #incidents

**Purpose**: P1/P2 incident coordination
**Ping**: Yes (immediately for P1)
**Frequency**: Only during incidents
**Urgency**: Critical
**Audience**: On-call, engineering, DevOps, leadership

### #dev-alerts

**Purpose**: Development notifications
**Ping**: No (use threads for replies)
**Frequency**: Regular
**Urgency**: Medium
**Audience**: All developers

### #dev-help

**Purpose**: Questions and learning
**Ping**: No
**Frequency**: Ongoing
**Urgency**: Low to medium
**Audience**: All developers

---

## Escalation Matrix

### P1 - Service Down

```
Escalation path:
1. Immediate: @on-call engineer
2. +5 min: @engineering-lead
3. +10 min: @devops-lead
4. +15 min: @cto
```

### P2 - Major Feature Broken

```
Escalation path:
1. Immediate: @feature-owner
2. +15 min: @engineering-lead
3. +30 min: @devops-lead
```

### P3 - Degradation

```
Escalation path:
1. Normal: Issue creation
2. +1 hour: @engineering-lead if still investigating
3. +4 hours: Escalate to backlog
```

---

## Integration with GitHub

**GitHub Actions → Slack**:

- Deployment workflows can post Slack notifications
- Set up in workflow file with Slack webhook

**GitHub Issues → Slack**:

- Use `#` mentions to link issues in Slack
- Example: "See #123 for details"

**Slack → GitHub**:

- Link GitHub Actions runs
- Link PRs with [Title](URL)
- Reference issues with #[number]
