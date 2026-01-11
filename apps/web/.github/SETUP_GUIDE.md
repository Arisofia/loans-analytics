# Week 1 Setup Guide

**Version**: 2.0
**Date**: 2025-12-26
**Duration**: 2-4 hours
**Audience**: DevOps, Infrastructure, Team Lead

---

## Overview

This guide walks you through the Week 1 setup process to make the CI/CD pipeline operational. All steps must be completed before Week 2 dry-runs.

---

## Prerequisites

### What You Need

- [ ] GitHub CLI installed (`gh`)
- [ ] GitHub account with admin access to the repository
- [ ] Access to Supabase dashboard (staging & production projects)
- [ ] Access to Azure portal (Static Web Apps)
- [ ] Access to Sentry dashboard (optional, for error tracking)
- [ ] 2-4 hours of uninterrupted time

### Install GitHub CLI

**macOS**:

```bash
brew install gh
```

**Linux**:

```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key C99B11DEB97541F0
sudo apt-add-repository https://cli.github.com/packages
sudo apt update
sudo apt install gh
```

**Windows**:

```bash
choco install gh
```

### Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts to authenticate.

---

## Step 1: Gather Required Information (30 min)

Before running the setup script, gather all required values. This prevents interruptions during setup.

### Staging Secrets

#### 1. STAGING_SUPABASE_URL

**Where to find**:

1. Go to <https://supabase.com/dashboard>
2. Select your **staging** project
3. Click **Settings** → **API**
4. Copy the **Project URL** (example: `https://xxxxxxxxxxxx.supabase.co`)

**Verification**: URL should start with `https://` and end with `.supabase.co`

#### 2. STAGING_SUPABASE_KEY

**Where to find**:

1. Same dashboard: **Settings** → **API**
2. Copy the **anon public** key (NOT the service_role key)
3. Key starts with `eyJ...` (JWT format)

**Verification**: Should be a long alphanumeric string starting with `eyJ`

#### 3. AZURE_STATIC_WEB_APPS_TOKEN_STAGING

**Where to find**:

1. Go to <https://portal.azure.com>
2. Find your **Static Web App** (staging environment)
3. Click **Manage deployment token**
4. Copy the token

**Verification**: Should be a long random token

### Production Secrets

#### 4. PROD_SUPABASE_URL

**Where to find**: Same as staging, but select **production** project

#### 5. PROD_SUPABASE_KEY

**Where to find**: Same as staging, but from **production** project

#### 6. PROD_SENTRY_DSN

**Where to find**:

1. Go to <https://sentry.io>
2. Select your organization
3. Go to **Settings** → **Projects**
4. Select your project
5. Click **Settings** → **Client Keys (DSN)**
6. Copy the DSN (example: `https://xxxx@xxxx.ingest.sentry.io/xxxx`)

**Verification**: Should start with `https://` and contain `.ingest.sentry.io`

**Optional**: If not using Sentry, you can use a placeholder like `https://placeholder@placeholder.ingest.sentry.io/0`

#### 7. AZURE_STATIC_WEB_APPS_TOKEN_PROD

**Where to find**: Same as staging, but for **production** Static Web App

---

## Step 2: Run Setup Script (30 min)

Navigate to the repository and run the setup script:

```bash
cd apps/web
.github/setup-secrets.sh
```

The script will:

1. Verify you're in a git repository
2. Verify GitHub CLI is installed and authenticated
3. Ask for repository owner (if not detected)
4. Collect staging secrets
5. Collect production secrets
6. Create secrets in GitHub
7. Verify all secrets were created
8. Display next steps

### What the Script Does

✅ Creates 7 GitHub repository secrets
✅ Validates each secret before creating
✅ Verifies successful creation
✅ Does NOT modify any code or configuration
✅ Can be run multiple times (will update existing secrets)

### Troubleshooting

**"GitHub CLI not installed"**
→ Install using instructions above

**"Not authenticated"**
→ Run `gh auth login`

**"Secret creation failed"**
→ Check your repository permissions
→ Verify the GitHub CLI is authenticated to correct account

**"Secrets not found after creation"**
→ Wait 30 seconds and run again
→ Check repository Settings → Secrets and variables → Actions

---

## Step 3: Verify Secrets (10 min)

### Method 1: Using GitHub Web UI

1. Go to repository **Settings**
2. Click **Secrets and variables** → **Actions**
3. Verify you see 7 secrets:
   - STAGING_SUPABASE_URL
   - STAGING_SUPABASE_KEY
   - AZURE_STATIC_WEB_APPS_TOKEN_STAGING
   - PROD_SUPABASE_URL
   - PROD_SUPABASE_KEY
   - PROD_SENTRY_DSN
   - AZURE_STATIC_WEB_APPS_TOKEN_PROD

**Note**: You won't see the values (GitHub hides them for security)

### Method 2: Using GitHub CLI

```bash
gh secret list -R owner/repo
```

Should show all 7 secrets.

---

## Step 4: Configure Environments (30 min)

GitHub needs to know what environments exist. Create them in repository settings.

### Using GitHub Web UI

1. Go to repository **Settings**
2. Click **Environments** (left sidebar)
3. Click **New environment**
4. Create **staging**:
   - Name: `staging`
   - Click **Configure environment**
   - No additional settings needed (for now)
   - Click **Save protection rules**

5. Repeat for **production**:
   - Name: `production`
   - Click **Configure environment**
   - Under **Deployment branches and tags**:
     - Select "Protected branches and tags"
     - Click **Add deployment branch or tag rule**
     - Pattern: `v*` (version tags only)
   - Under **Reviewers**:
     - Add required reviewers (team leads) - OPTIONAL
   - Click **Save protection rules**

6. Create **production-rollback**:
   - Name: `production-rollback`
   - Same settings as production (for emergency use)
   - Click **Save protection rules**

### Verification

After creating, you should see 3 environments in Settings → Environments:

- staging
- production (with branch rules)
- production-rollback (with branch rules)

---

## Step 5: Configure Environment Files (30 min)

Create environment-specific configuration files.

### Staging Environment File

Create file: `config/environments/staging.yml`

```yaml
# Staging Environment Configuration
environment: staging

cascade:
  base_url: https://app.cascadedebt.com
  portfolio_id: abaco

supabase:
  url: ${STAGING_SUPABASE_URL}
  anon_key: ${STAGING_SUPABASE_KEY}

sentry:
  enabled: false
  dsn: null

azure:
  enabled: true
  environment: staging

features:
  debug: true
  verbose_logging: true
  validation_strict: true
```

### Production Environment File

Create file: `config/environments/production.yml`

```yaml
# Production Environment Configuration
environment: production

cascade:
  base_url: https://app.cascadedebt.com
  portfolio_id: abaco

supabase:
  url: ${PROD_SUPABASE_URL}
  anon_key: ${PROD_SUPABASE_KEY}

sentry:
  enabled: true
  dsn: ${PROD_SENTRY_DSN}

azure:
  enabled: true
  environment: production

features:
  debug: false
  verbose_logging: false
  validation_strict: true
```

### Verification

```bash
ls -la config/environments/
# Should show:
# staging.yml
# production.yml
```

---

## Step 6: Team Onboarding (30 min)

Ensure all team members understand the new workflow.

### Developers

```bash
# Each developer should read
cat .github/QUICK_START.md
```

Key points:

- Daily workflow: feature branch → PR → CI validates → merge
- Commands: `pnpm check-all`, `npm test`, `pnpm build`
- Fix CI failures: `pnpm lint:fix`, etc.

### QA Team

```bash
# QA should read their section
grep -A 100 "## QA / Quality Assurance" .github/TEAM_RUNBOOKS.md
```

Key points:

- 24-hour validation window after develop merge
- Use validation checklist
- Post results in #dev-alerts

### DevOps

```bash
# DevOps should read deployment guide
cat .github/DEPLOYMENT_CONFIG.md
```

Key points:

- Create version tags for production
- Approve deployments in GitHub Actions
- Monitor health checks
- Execute rollback if needed

### Everyone

```bash
# All team members should read
cat .github/README.md
cat .github/DEPLOYMENT_COORDINATION.md
```

---

## Step 7: Slack Setup (Optional, 15 min)

Configure Slack integration for deployment notifications.

### Create Slack Webhooks

For each channel (#dev-alerts, #prod-alerts, #incidents):

1. Go to Slack workspace settings
2. Create an Incoming Webhook
3. Configure for channel
4. Copy webhook URL

### Add to GitHub Actions (Optional)

If you want Slack notifications from workflows:

1. Go to repository Settings → Secrets
2. Add secrets:
   - `SLACK_WEBHOOK_DEV_ALERTS`: Webhook for #dev-alerts
   - `SLACK_WEBHOOK_PROD_ALERTS`: Webhook for #prod-alerts
   - `SLACK_WEBHOOK_INCIDENTS`: Webhook for #incidents

3. Update workflow YAML to use webhooks (see DEPLOYMENT_COORDINATION.md)

---

## Step 8: Final Verification (15 min)

### Checklist

Run through these to confirm setup is complete:

```bash
# 1. Verify git repo
cd /path/to/repo/apps/web
git rev-parse --git-dir
# Should return: .git

# 2. Verify GitHub CLI authenticated
gh auth status
# Should show your username

# 3. Verify secrets exist
gh secret list -R owner/repo
# Should show 7 secrets

# 4. Verify environment files
ls -la config/environments/staging.yml config/environments/production.yml
# Both should exist

# 5. Verify workflows
ls -la .github/workflows/*.yml
# Should show: ci.yml, deploy-staging.yml, deploy-production.yml, rollback.yml, reusable-steps.yml
```

### Manual Verification in GitHub Web UI

1. Go to repository Settings
2. Verify:
   - [ ] Secrets and variables → Actions (should show 7 secrets)
   - [ ] Environments (should show 3: staging, production, production-rollback)
   - [ ] Actions tab (should show 5 workflows)

---

## Troubleshooting

### Secret Creation Failed

**Problem**: Script says secret creation failed

**Solutions**:

1. Verify you have admin access to repository
2. Check GitHub CLI authentication: `gh auth status`
3. Try creating secret manually: `gh secret set NAME --body "value" -R owner/repo`
4. Check for typos in secret names

### Environment Files Not Found

**Problem**: `config/environments/` directory doesn't exist

**Solution**:

```bash
mkdir -p config/environments
# Then create staging.yml and production.yml as shown above
```

### GitHub Actions Can't Access Secrets

**Problem**: Workflows fail with "secret not found"

**Solutions**:

1. Wait 1-2 minutes after creating secrets (GitHub needs time to sync)
2. Trigger workflow manually to test
3. Check workflow YAML uses correct secret names (case-sensitive)
4. Verify workflow is in main branch

### Deployment Fails to Azure

**Problem**: Azure deployment token invalid

**Solutions**:

1. Verify token is still valid (not expired)
2. Regenerate token from Azure portal
3. Update secret with new token

---

## Success Criteria

Week 1 setup is complete when:

✅ 7 GitHub secrets created and verified
✅ 3 GitHub environments created
✅ Staging environment file created
✅ Production environment file created
✅ All team members read documentation
✅ Slack channels ready (optional)

---

## Next: Week 2 Dry-Runs

Once Week 1 is complete, proceed to Week 2:

📋 **Week 2 Dry-Run Checklist** (See POST_IMPLEMENTATION_CHECKLIST.md)

1. **Developer Dry-Run** (4h)
   - Test local CI checks
   - Create feature branch, make change, push
   - Watch CI run automatically
   - Fix any failures

2. **Staging Dry-Run** (6h)
   - Merge feature to develop
   - Watch auto-deploy to staging
   - Run QA validation checklist
   - Post results in #dev-alerts

3. **Production Dry-Run** (4h)
   - Create test version tag
   - Watch production CI
   - Approve deployment
   - Watch health checks
   - Monitor for 15 minutes

4. **Rollback Dry-Run** (2h)
   - Trigger rollback workflow
   - Select previous version
   - Watch rollback complete
   - Verify health checks pass

---

## Getting Help

### Questions During Setup?

1. Check this guide (Step 1-8)
2. Check `.github/README.md` for more context
3. Ask in Slack #dev-help

### Setup Issues?

1. Check Troubleshooting section above
2. Create GitHub issue with:
   - What step failed
   - Error message
   - What you've tried

### After Setup?

1. Follow POST_IMPLEMENTATION_CHECKLIST.md for Week 2
2. Reach out to DevOps lead if issues arise
3. Schedule team retrospective for Week 4

---

## Timeline

**Expected duration**: 2-4 hours for one person
**Best practice**: Have 2-3 people involved (DevOps + Tech Lead)

**Breakdown**:

- Step 1 (Gather info): 30 min
- Step 2 (Run script): 30 min
- Step 3 (Verify): 10 min
- Step 4 (Environments): 30 min
- Step 5 (Config files): 30 min
- Step 6 (Team onboarding): 30 min
- Step 7 (Slack): 15 min
- Step 8 (Verification): 15 min
- **Total**: ~2.5-3 hours

---

**Setup Owner**: _______________
**Completion Date**: _______________
**Verified By**: _______________

**Next**: Follow Week 2 dry-runs in POST_IMPLEMENTATION_CHECKLIST.md
