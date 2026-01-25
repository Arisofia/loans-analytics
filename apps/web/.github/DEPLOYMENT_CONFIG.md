# Automated Production Deployment Configuration

**Version**: 2.0
**Date**: 2025-12-26
**Status**: Complete CI/CD Pipeline Implementation

---

## Overview

Comprehensive GitHub Actions CI/CD pipeline enabling:

- Automated code quality validation (lint, type-check, tests)
- Staging deployment with 24-hour validation gate
- Production deployment with manual approval gates
- Emergency rollback capabilities
- Health check validation

---

## Workflows

### 1. CI Workflow (`ci.yml`)

**Trigger**: Push to `main`/`develop`, Pull Requests
**Jobs**: Lint → Type-check → Test → Build → Quality Summary

**Quality Gates**:

- ESLint validation (no errors)
- Prettier formatting check
- TypeScript type checking (no errors)
- Jest test suite (100% pass rate)
- Code coverage ≥ 85% (per ENGINEERING_STANDARDS.md)
- Next.js build success

**Artifacts**: Next.js build output (`.next`)

### 2. Staging Deployment (`deploy-staging.yml`)

**Trigger**: Push to `develop` branch
**Environment**: `https://staging.abaco-loans-analytics.com`

**Stages**:

1. **Quality Gate**: Re-run full CI checks
2. **Deploy**: Azure Static Web Apps deployment
3. **Validation Period**: 24-hour shadow mode (per MIGRATION.md)
4. **Smoke Tests**: HTTP 200 health check

**Configuration**:

- Automatic on develop branch pushes
- Manual trigger via `workflow_dispatch`
- Secrets: `STAGING_SUPABASE_URL`, `STAGING_SUPABASE_KEY`, `AZURE_STATIC_WEB_APPS_TOKEN_STAGING`

### 3. Production Deployment (`deploy-production.yml`)

**Trigger**: Git tags (semantic versioning `v*.*.*`) or manual
**Environment**: `https://abaco-loans-analytics.com`

**Stages**:

1. **Pre-deployment**: Version extraction, staging validation reminder
2. **Approval Gate**: Manual environment approval required
3. **Quality Verification**: Final lint, type-check, test, build
4. **Deploy**: Azure Static Web Apps production deployment
5. **Post-deployment Validation**: Health checks, performance baseline
6. **Rollback on Failure**: Automatic detection, manual intervention required

**Configuration**:

- Requires environment approval (manual step)
- Secrets: `PROD_SUPABASE_URL`, `PROD_SUPABASE_KEY`, `PROD_SENTRY_DSN`, `AZURE_STATIC_WEB_APPS_TOKEN_PROD`
- Creates GitHub release on successful deployment

### 4. Rollback Workflow (`rollback.yml`)

**Trigger**: Manual workflow dispatch
**Parameters**:

- `target_version`: Semantic version to rollback to (e.g., `v1.0.0`)
- `environment`: `staging` or `production`

**Stages**:

1. **Pre-rollback**: Input validation, incident issue creation
2. **Approval Gate**: Manual environment approval
3. **Execute Rollback**: Check out target version and deploy
4. **Post-rollback Validation**: Health checks
5. **Failure Notification**: Critical issue creation if rollback fails

**Recovery Time**: < 5 minutes (per OPERATIONS.md)

---

## Required GitHub Secrets

### Staging Secrets

```
STAGING_SUPABASE_URL              # Staging Supabase project URL
STAGING_SUPABASE_KEY              # Staging anonymous API key
AZURE_STATIC_WEB_APPS_TOKEN_STAGING  # Azure deployment token
```

### Production Secrets

```
PROD_SUPABASE_URL                 # Production Supabase project URL
PROD_SUPABASE_KEY                 # Production anonymous API key
PROD_SENTRY_DSN                   # Sentry error tracking DSN
AZURE_STATIC_WEB_APPS_TOKEN_PROD  # Azure deployment token
```

### Setup Instructions

1. Go to repository Settings → Secrets and variables → Actions
2. Add each secret with the exact names above
3. Values obtained from:
   - **Supabase**: Project Settings → API
   - **Sentry**: Project Settings → Client Keys (DSN)
   - **Azure**: Static Web Apps → Deployment token

---

## Environment Configuration

### Staging (`config/environments/staging.yml`)

- Staging Supabase instance
- Development-like data volume
- 24-hour validation before production

### Production (`config/environments/production.yml`)

- Production Supabase instance
- Sentry error tracking enabled
- Performance monitoring active
- Full audit logging

---

## Deployment Timeline

### Feature Development

```
Push to feature branch → CI checks pass → Create PR
```

### Staging Deployment (Auto)

```
Merge PR to develop → CI validation → Staging deploy → 24h validation
```

### Production Deployment

```
Create tag (v*.*.*)  → CI validation → Manual approval
→ Quality verification → Production deploy → Health checks
→ Create release
```

### Emergency Rollback

```
Manual workflow trigger → Select version & environment
→ Manual approval → Deploy previous version → Health checks
```

---

## Monitoring & Alerts

### Deployment Status

- Track via GitHub Actions: <https://github.com/[owner]/[repo]/actions>
- GitHub deployments tab for environment history

### Health Checks

- Staging: HTTP 200 check (30s post-deploy)
- Production: HTTP 200 check (60s post-deploy, 5 retries)

### Incident Response

- Rollback workflow auto-creates incident issues
- CI failures block deployments automatically
- Failed health checks trigger manual rollback

---

## Quality Metrics

All deployments must meet ENGINEERING_STANDARDS.md requirements:

| Check | Threshold | Enforcement |
|-------|-----------|-------------|
| Lint | 0 errors | Blocks CI |
| Type Check | 0 errors | Blocks CI |
| Test Pass Rate | 100% | Blocks CI |
| Code Coverage | ≥ 85% | Blocks CI |
| Build Success | Yes | Blocks deploy |
| Health Check | HTTP 200 | Blocks deploy |

---

## Rollback Procedures

### Quick Rollback

1. Go to GitHub Actions → Rollback workflow
2. Click "Run workflow"
3. Enter target version (e.g., `v1.2.0`)
4. Select environment (staging/production)
5. Approve deployment when prompted
6. Monitor health checks

**Expected Duration**: < 5 minutes

### Manual Rollback

If automated rollback fails:

1. Refer to OPERATIONS.md Rollback Procedures section
2. Restore from Azure Static Web Apps deployment history
3. Verify health checks pass
4. Create incident issue documenting the incident

---

## CI/CD Best Practices

### Branch Strategy

- **main**: Production-ready code, tagged releases
- **develop**: Staging-ready code, features merged here
- **feature/**: Individual feature development

### Semantic Versioning

- `v1.0.0` (major.minor.patch)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Commit Messages

```
feat: Add user authentication
fix: Resolve login timeout issue
docs: Update API documentation
chore: Update dependencies
```

### Code Review Checklist

- [ ] CI workflow passes
- [ ] Code coverage ≥ 85%
- [ ] Linting clean
- [ ] TypeScript types correct
- [ ] Tests added for new features
- [ ] Documentation updated

---

## Troubleshooting

### CI Checks Failing

1. Review workflow logs: Actions tab → workflow → failed job
2. Common issues:
   - **Lint errors**: Run `pnpm lint:fix`
   - **Type errors**: Run `pnpm type-check`
   - **Test failures**: Run `npm test`
   - **Coverage low**: Add tests for new code

### Deployment Fails

1. Check GitHub deployment status
2. Verify all secrets configured correctly
3. Ensure environment approvals granted
4. Review Azure Static Web Apps logs

### Health Checks Fail After Deploy

1. Verify Azure deployment succeeded
2. Check application logs in Azure portal
3. Trigger rollback if needed
4. Document incident for post-mortem

---

## Related Documentation

- **ENGINEERING_STANDARDS.md**: Code quality requirements
- **OPERATIONS.md**: Operational procedures and troubleshooting
- **MIGRATION.md**: Migration procedures with validation gates
- **PRODUCTION_READINESS.md**: Pre-deployment checklist

---

## Contact & Support

For deployment issues:

1. Check this guide and related docs
2. Review workflow logs for specific errors
3. Create issue with `deployment` label
4. Reference OPERATIONS.md incident response procedures
