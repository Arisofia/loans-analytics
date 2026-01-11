# Team Deployment Runbooks

**Version**: 2.0
**Date**: 2025-12-26
**Audience**: All development, QA, and operations teams

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Role-Based Runbooks](#role-based-runbooks)
3. [Common Scenarios](#common-scenarios)
4. [Incident Response](#incident-response)
5. [Checklists](#checklists)

---

## Quick Reference

### Deployment Flow

```
Feature Development
    ↓
Create PR on develop branch
    ↓ CI validation (auto)
Code review + approval
    ↓
Merge to develop
    ↓ Staging deploy (auto)
24-hour validation period
    ↓
Create version tag (v*.*.*)
    ↓ CI validation (auto)
Approve production deployment
    ↓ Production deploy
Health checks + monitoring
```

### Key Commands

```bash
# Local development
pnpm install           # Install dependencies
pnpm dev               # Start dev server (localhost:3000)
pnpm lint:fix          # Fix linting issues
pnpm type-check        # Check TypeScript types
npm test               # Run tests

# Before push
pnpm check-all         # Lint + type-check + format check

# Tagging for production
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

---

## Role-Based Runbooks

### Frontend Developer

#### Daily Workflow

**1. Start Your Day**

```bash
cd apps/web
git fetch origin
git checkout develop
git pull origin develop
pnpm install
pnpm dev
```

**2. Create Feature Branch**

```bash
git checkout -b feature/feature-name
# Follow: feature/, bugfix/, or chore/ prefixes
```

**3. Before Pushing**

```bash
# Run all checks locally
pnpm check-all
npm test

# Fix any issues
pnpm lint:fix
pnpm format
```

**4. Create Pull Request**

- Push to your feature branch
- Open PR against `develop` branch
- Link any related issues
- Add description of changes
- Request review from team

**5. During Code Review**

- Address review comments
- Push fixes to same branch
- CI runs automatically on each push
- Wait for approval before merge

**6. After Merge**

- Delete feature branch
- Monitor staging deployment (auto)
- Participate in 24-hour validation

#### Fixing Lint/Type Errors

**If CI fails on lint**:

```bash
pnpm lint:fix          # Auto-fix most issues
git add .
git commit -m "fix: resolve linting issues"
git push
```

**If CI fails on types**:

```bash
pnpm type-check        # Show errors
# Edit files to fix TypeScript errors
git add .
git commit -m "fix: resolve type errors"
git push
```

**If tests fail**:

```bash
npm test               # Run tests locally
npm test -- --watch   # Debug specific test
# Fix code to pass tests
git add .
git commit -m "fix: resolve test failures"
git push
```

#### Deploying to Production

You don't deploy directly. Production deployments follow this process:

1. **Wait for staging validation**: 24 hours of testing in staging
2. **QA sign-off**: Quality assurance team approves
3. **Tag creation** (DevOps/Team Lead):

   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   ```

4. **Approve deployment**: GitHub Actions prompts for approval
5. **Monitor**: Watch health checks pass in GitHub Actions

---

### QA / Quality Assurance

#### Staging Validation (24-hour window)

**When**: Immediately after develop branch merge
**Duration**: 24 hours
**Environment**: <https://staging.abaco-loans-analytics.com>

**1. Validation Checklist**

- [ ] Application loads without errors
- [ ] All links and navigation work
- [ ] Data displays correctly
- [ ] Forms submit successfully
- [ ] Error messages appear correctly
- [ ] Performance is acceptable (< 2s page load)
- [ ] Mobile responsiveness works
- [ ] No console errors (F12 → Console tab)
- [ ] No visual regressions vs. previous version

**2. Testing Scenarios**

**User Authentication**

```
1. Navigate to login page
2. Try invalid credentials → Error displays
3. Enter valid credentials → Login succeeds
4. Session persists on page reload
5. Logout works correctly
```

**Data Display**

```
1. View portfolio dashboard
2. Verify all KPI cards display
3. Check data freshness (< 6 hours old)
4. Verify numbers are reasonable
5. Export functionality works
```

**Error Handling**

```
1. Try network disconnect (DevTools → Offline)
2. Verify error message displays
3. Reconnect network
4. Verify recovery works
```

**3. Document Findings**

**If issues found**:

```
Create GitHub issue:
Title: [Staging] Brief description
Body:
- Environment: Staging
- Steps to reproduce:
  1. Step 1
  2. Step 2
- Expected: X
- Actual: Y
- Screenshots if helpful

Label: staging-issue
```

**If no issues**:

```
Post comment on GitHub Actions:
✅ 24-hour staging validation complete
- All tests passed
- No visual regressions
- Performance acceptable
- Ready for production
```

**4. Sign-off Process**

When validation is complete:

1. Post ✅ approval in GitHub Actions
2. Notify #dev-alerts Slack channel
3. Production team proceeds with deployment tag

---

### DevOps / Release Engineer

#### Pre-Production Release

**Timeline**: After 24-hour staging validation
**Responsibility**: Coordinate and execute release

**1. Pre-Release Checklist**

- [ ] 24-hour staging validation complete
- [ ] All QA issues resolved (none blocking)
- [ ] Security scan passed
- [ ] Performance baseline acceptable
- [ ] Team notifications sent
- [ ] Deployment window scheduled
- [ ] Rollback plan documented

**2. Create Release**

```bash
# Ensure local repo is up-to-date
git fetch origin
git checkout main
git pull origin main

# Determine version number
# Current: v1.2.3 (check git tags)
# New feature: v1.3.0 (minor bump)
# Bug fix: v1.2.4 (patch bump)
# Breaking change: v2.0.0 (major bump)

# Create and push tag
git tag -a v1.3.0 -m "Release v1.3.0: Add feature X, fix bug Y"
git push origin v1.3.0
```

**3. Monitor CI/CD Pipeline**

Go to: <https://github.com/[owner]/[repo]/actions>

**When deploy-production workflow starts**:

- ✅ Pre-deployment checks
- ✅ Quality verification
- ⏳ Awaiting approval (manual step)

**4. Approve Production Deployment**

In GitHub Actions:

1. Find `deploy-production` workflow run
2. Click "Review deployments"
3. Select `production` environment
4. Click "Approve and deploy"
5. Monitor deployment progress

**5. Post-Deployment Validation**

Workflow automatically runs health checks. If they pass:

- ✅ Deployment successful
- ✅ Health checks passed
- ✅ GitHub release created

**6. Notify Team**

Post to Slack #prod-alerts:

```
🚀 Production Deployment Complete

Version: v1.3.0
Deployed: [Timestamp]
Status: ✅ Healthy
Health Checks: All passing

Changes:
- Added feature X
- Fixed bug Y
- Improved performance by Z%

Monitoring dashboard: [Link]
Rollback procedure: See OPERATIONS.md
```

#### Emergency Rollback

**When to rollback**:

- Health checks failing after 15 minutes
- Critical functionality broken
- Major performance degradation
- Data integrity issues

**1. Rollback Procedure**

Go to: <https://github.com/[owner]/[repo]/actions>

1. Click "Workflows" → "Rollback - Emergency Recovery"
2. Click "Run workflow"
3. Fill in inputs:
   - Target version: Previous stable version (e.g., `v1.2.3`)
   - Environment: `production`
4. Click "Run workflow"
5. Click "Review deployments" when prompted
6. Select `production-rollback`
7. Click "Approve and deploy"

**2. Monitor Rollback**

Expected timeline:

- 0-2 min: Version checkout and build
- 2-4 min: Deployment to Azure
- 4-5 min: Health checks
- 5+ min: Complete

**3. Post-Rollback**

Post to Slack #incidents:

```
🔄 Emergency Rollback Completed

Version: v1.3.0 → v1.2.3
Reason: [Critical issue description]
Status: ✅ Rollback successful
Time to recovery: [X minutes]

Next steps:
1. Investigate root cause
2. Fix issue in develop branch
3. Re-validate in staging
4. Create new release tag
```

---

### DevOps / Infrastructure

#### GitHub Secrets Management

**Required Secrets** (set in repo Settings → Secrets):

**Staging**:

```
STAGING_SUPABASE_URL              # https://[project].supabase.co
STAGING_SUPABASE_KEY              # anon key from Supabase dashboard
AZURE_STATIC_WEB_APPS_TOKEN_STAGING
```

**Production**:

```
PROD_SUPABASE_URL                 # https://[project].supabase.co
PROD_SUPABASE_KEY                 # anon key from Supabase dashboard
PROD_SENTRY_DSN                   # https://[key]@[domain]/[id]
AZURE_STATIC_WEB_APPS_TOKEN_PROD
```

**To add/update secrets**:

1. Go to repository Settings
2. Click Secrets and variables → Actions
3. Click "New repository secret"
4. Enter name and value
5. Click "Add secret"

⚠️ **Never** share secrets in Slack, email, or commit to repo

#### Environment Configuration

**Staging `.env.staging`**:

```
NEXT_PUBLIC_SUPABASE_URL=https://[staging].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[staging-key]
NEXT_PUBLIC_SITE_URL=https://staging.abaco-loans-analytics.com
NODE_ENV=production
```

**Production `.env.production`**:

```
NEXT_PUBLIC_SUPABASE_URL=https://[prod].supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=[prod-key]
NEXT_PUBLIC_SITE_URL=https://abaco-loans-analytics.com
NEXT_PUBLIC_SENTRY_DSN=[sentry-dsn]
NODE_ENV=production
```

---

## Common Scenarios

### Scenario 1: Push to Develop, Auto-Deploy to Staging

**Trigger**: Merge PR to develop

**What happens automatically**:

1. GitHub Actions runs CI checks
2. If all pass → Deploys to staging
3. Smoke tests run (health check)
4. 24-hour validation window starts

**Your role**:

1. Create PR (feature branch → develop)
2. Request code review
3. Wait for CI ✅
4. Get approval
5. Merge PR
6. Watch staging deployment in Actions
7. Notify QA for 24-hour validation

**Timeline**: 5-10 minutes total

---

### Scenario 2: Fix Failing CI Check

**Problem**: Test failed, blocking merge

**Steps**:

```bash
# 1. Pull latest develop
git fetch origin
git rebase origin/develop

# 2. Run test locally to reproduce
npm test

# 3. Fix the test or code
# Edit failing test or implementation

# 4. Verify fix locally
npm test

# 5. Push fix
git add .
git commit -m "fix: resolve test failure in [component]"
git push

# 6. Monitor CI in GitHub
# Watch Actions tab for green ✅
```

**Don't**:

- Force push over review comments
- Merge with failing CI
- Ignore type errors

---

### Scenario 3: Code Review Comments

**When reviewer requests changes**:

1. Don't merge until approved
2. Address comments:

   ```bash
   git add [modified files]
   git commit -m "refactor: address review feedback"
   git push
   ```

3. CI re-runs automatically
4. Request re-review
5. Wait for approval
6. Merge when ready

**Resolution options**:

- ✅ **Approve**: Merge when ready
- 🔄 **Request changes**: Fix required before merge
- 💬 **Comment**: Question or suggestion (can merge)

---

### Scenario 4: Urgent Hotfix to Production

**When**: Critical bug in production, can't wait for develop cycle

**Process**:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# 2. Fix the bug
# Edit files to resolve issue
pnpm lint:fix
npm test

# 3. Push hotfix branch
git push origin hotfix/critical-bug-fix

# 4. Create PR to main
# Title: [HOTFIX] Brief description
# Mark as URGENT in description

# 5. Fast-track code review (team lead approval)

# 6. After merge to main, create release tag
git checkout main
git pull origin main
git tag -a v1.2.4 -m "[HOTFIX] Critical bug fix"
git push origin v1.2.4

# 7. Also merge back to develop
git checkout develop
git pull origin develop
git merge main
git push origin develop
```

**Don't**: Skip CI validation even for hotfixes

---

### Scenario 5: Production Issue, Need to Rollback

**When**: Critical issue detected after deployment
**Who**: DevOps with approval

**Steps**:

1. Go to GitHub Actions
2. Click "Workflows" → "Rollback - Emergency Recovery"
3. Click "Run workflow"
4. Enter:
   - Target version: Last known good version (e.g., `v1.2.3`)
   - Environment: `production`
5. Click "Run workflow"
6. Approve when prompted
7. Monitor rollback progress
8. Verify health checks pass
9. Notify team in #incidents

**Expected time**: < 5 minutes

---

## Incident Response

### Critical Severity (P1)

**Symptoms**: Service down, data loss, security breach

**Immediate Actions** (< 5 min):

1. Create GitHub issue: [CRITICAL] Issue title
2. Post #incidents Slack: Issue description + link
3. Trigger rollback if needed (see Scenario 5)
4. Page on-call engineer

**Follow-up** (< 30 min):

1. Assess root cause
2. Notify stakeholders
3. Document timeline
4. Plan fix

---

### High Severity (P2)

**Symptoms**: Major feature broken, data incorrect

**Immediate Actions** (< 15 min):

1. Create GitHub issue with reproduction steps
2. Post #dev-alerts Slack
3. Assess if rollback needed
4. Notify team lead

**Follow-up** (< 2 hours):

1. Root cause analysis
2. Fix implementation
3. Testing in staging
4. New release

---

### Medium Severity (P3)

**Symptoms**: Functionality degraded, minor issues

**Actions** (within business day):

1. Create GitHub issue
2. Post in #dev-alerts
3. Add to sprint backlog
4. Plan fix in next release

---

### Low Severity (P4)

**Symptoms**: Cosmetic issues, typos

**Actions** (within week):

1. Create GitHub issue
2. Label: `low-priority`
3. Add to backlog for future sprint

---

## Checklists

### Pre-Merge Checklist

- [ ] Feature branch created from develop
- [ ] Code changes complete
- [ ] `pnpm check-all` passes locally
- [ ] Tests added/updated
- [ ] No console errors/warnings
- [ ] No hardcoded secrets
- [ ] Documentation updated if needed
- [ ] PR description complete
- [ ] Request code review
- [ ] CI workflow passes
- [ ] Code review approved
- [ ] Ready to merge

### Pre-Production Release Checklist

- [ ] Feature/fix tested in staging
- [ ] 24-hour validation window complete
- [ ] QA sign-off obtained
- [ ] Security review passed
- [ ] Performance acceptable
- [ ] Team notifications sent
- [ ] Rollback plan documented
- [ ] Release notes prepared
- [ ] Tag created correctly
- [ ] Deployment approved
- [ ] Health checks passing
- [ ] Production verified
- [ ] Team notified

### Post-Deployment Checklist

- [ ] Application loads (<https://abaco-loans-analytics.com>)
- [ ] Login works
- [ ] Data displays correctly
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Monitoring alerts quiet (no unexpected alerts)
- [ ] Team notified in #prod-alerts
- [ ] Stakeholders notified
- [ ] Time-to-recovery documented

### Rollback Checklist

- [ ] Issue identified and documented
- [ ] Severity assessed
- [ ] Team lead notified
- [ ] Previous version identified
- [ ] Rollback approved
- [ ] Rollback executed
- [ ] Health checks passing
- [ ] Users notified
- [ ] Root cause investigation started
- [ ] Incident issue created

---

## Getting Help

**Questions?**

1. Check this guide and related docs
2. Ask in #dev-help Slack
3. Create GitHub issue with `question` label
4. Contact team lead

**Documentation**

- `.github/DEPLOYMENT_CONFIG.md`: CI/CD configuration
- `OPERATIONS.md`: Operational procedures
- `ENGINEERING_STANDARDS.md`: Code standards
- `MIGRATION.md`: Migration procedures

**On-Call**

- During incidents: Follow incident response procedures
- Escalate P1 issues immediately
- Page on-call engineer if service down
