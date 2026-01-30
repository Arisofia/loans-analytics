# Snyk Token Setup for GitHub Actions

This guide explains how to obtain and configure a Snyk token for use in the automated security scanning workflow.

## Overview

The `auto-security-scan.yml` workflow includes optional Snyk integration for comprehensive dependency vulnerability scanning. Snyk is **optional** - the workflow will run all other security checks (Bandit, Safety, pip-audit) even without a Snyk token.

## Step 1: Get a Snyk Token

### Option A: Sign Up for Free on Snyk (Recommended)

1. **Visit Snyk**: Go to https://snyk.io/
2. **Create Account**: Click "Sign up for free"
3. **Choose Login Method**:
   - GitHub (recommended - easier integration)
   - Google
   - Email
4. **Complete Registration**: Follow the onboarding flow
5. **Get Your Token**:
   - Click on your profile icon (top-right)
   - Select "Account settings"
   - Click "General" or "API token"
   - Click "Show" to reveal your token
   - Copy the token (looks like: `12345678-1234-1234-1234-123456789012`)

### Option B: Existing Snyk Account

If you already have a Snyk account:

1. Log in to https://app.snyk.io/
2. Navigate to Account Settings
3. Find API Token section
4. Copy your token

## Step 2: Add Token to GitHub Secrets

### Method 1: Via GitHub Web UI (Easiest)

1. **Go to Repository Settings**:
   - Navigate to: `https://github.com/Arisofia/abaco-loans-analytics/settings`
   - Or: Click "Settings" tab on your repo

2. **Access Secrets**:
   - In left sidebar, click "Secrets and variables"
   - Click "Actions"

3. **Create New Secret**:
   - Click "New repository secret"
   - **Name**: `SNYK_TOKEN`
   - **Secret**: Paste your Snyk token
   - Click "Add secret"

### Method 2: Via GitHub CLI

```bash
# Install GitHub CLI if not already installed
# macOS: brew install gh
# or visit: https://cli.github.com/

# Set the secret
gh secret set SNYK_TOKEN -b "your-snyk-token-here"

# Verify it was set
gh secret list
```

### Method 3: Via Terminal (macOS/Linux)

```bash
# Navigate to repository
cd /Users/jenineferderas/abaco-loans-analytics

# Set environment variable temporarily
export SNYK_TOKEN="your-snyk-token-here"

# Add to GitHub (requires gh CLI)
gh secret set SNYK_TOKEN
```

## Step 3: Verify Setup

### Check Secret is Configured

1. Go to repository Settings → Secrets and variables → Actions
2. You should see `SNYK_TOKEN` in the list (value is hidden for security)

### Test the Workflow

1. **Trigger the workflow**:
   - Make a small commit or PR
   - Go to "Actions" tab
   - Watch "Auto Security Scan" workflow

2. **Check Snyk step**:
   - Expand "Run Snyk" step
   - Should see:
     ```
     ✅ Authenticated with Snyk
     npm install -g snyk
     snyk test
     ```
   - If secret is missing, step is skipped (this is normal)

## Understanding the Workflow Behavior

### With SNYK_TOKEN Set

The workflow will:

1. Run Bandit, Safety, and pip-audit (always)
2. **Also run Snyk** for comprehensive dependency scanning
3. Upload Snyk report to workflow artifacts

### Without SNYK_TOKEN

The workflow will:

1. Run Bandit, Safety, and pip-audit (always)
2. **Skip Snyk steps** (graceful degradation)
3. Workflow still succeeds - no failures

This means **you don't need Snyk to use the security workflow** - it's optional enhancement.

## Security Best Practices

### Protect Your Token

1. **Never commit the token** to version control
2. **Don't paste in code comments** or documentation
3. **Use GitHub Secrets** to store securely
4. **Token is hidden** in GitHub UI and logs

### Token Rotation (Optional)

For enhanced security, rotate your Snyk token periodically:

1. Log in to Snyk account
2. Generate a new API token
3. Update GitHub secret with new token
4. Delete old token from Snyk account

### Access Control

Set who can use the secret:

1. Go to repository Settings
2. Click "Actions" under Secrets and variables
3. Review which workflows can access the secret
4. (The `auto-security-scan.yml` will automatically use it)

## Troubleshooting

### Secret Not Found in Workflow

**Problem**: "Run Snyk" step is being skipped

**Solution**:

- Verify secret name is exactly: `SNYK_TOKEN` (case-sensitive)
- Check secret appears in Settings → Secrets and variables
- Wait a few minutes after adding secret (GitHub caches)
- Create new commit/PR to trigger workflow again

### Authentication Error

**Problem**: Workflow shows "Authentication failed"

**Solution**:

- Verify token is correct (copy from Snyk account again)
- Check token hasn't expired (usually 1 year)
- Regenerate new token in Snyk if needed
- Update GitHub secret with new token

### Snyk Command Not Found

**Problem**: "npm: command not found" or "snyk: command not found"

**Solution**:

- This is handled in workflow (installs Node.js)
- Shouldn't happen in normal runs
- Check workflow logs for details

## Next Steps

1. ✅ Sign up for Snyk (or use existing account)
2. ✅ Get your API token
3. ✅ Add `SNYK_TOKEN` to GitHub Secrets
4. ✅ Create a test commit/PR to verify

## Additional Resources

- **Snyk Documentation**: https://docs.snyk.io/
- **Snyk API Token**: https://docs.snyk.io/snyk-cli/authenticate-the-cli-with-your-account
- **GitHub Secrets**: https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions
- **Auto Security Scan Workflow**: See `.github/workflows/auto-security-scan.yml`

## FAQ

**Q: Is Snyk required?**
A: No, it's optional. All other security tools run regardless.

**Q: How much does Snyk cost?**
A: Free plan available with limits. Paid plans for teams.

**Q: Can I use a different token?**
A: Token must be from Snyk. Other tools are configured differently.

**Q: How often does Snyk run?**
A: Weekly (Sunday at 0:00 UTC) + on every PR and push to main.

**Q: Where can I see Snyk reports?**
A: In "Actions" workflow artifacts after each run.
