# Credentials Setup & GitHub Actions Integration

**Status:** ✅ Complete  
**Last Updated:** 2026-02-21  
**Scope:** Supabase, Grafana, GitHub Actions Secrets

---

## Overview

This guide covers:
- ✅ Supabase credential verification
- ✅ Local environment file setup (.env.local, .env.monitoring)
- ✅ GitHub Actions secrets configuration
- ✅ Connection testing

---

## 1. Supabase Credentials

### Current Setup

Your `.env.local` file contains credentials for **two** Supabase projects:

#### Project 1: Development (Current in .env.local)
- **Project ID:** `goxdevkqozomyhsyxhte`
- **URL:** `https://goxdevkqozomyhsyxhte.supabase.co`
- **Status:** ✅ Configured in `.env.local`

#### Project 2: Production (New - goxdevkqozomyhsyxhte)
- **Project ID:** `goxdevkqozomyhsyxhte`
- **URL:** `https://goxdevkqozomyhsyxhte.supabase.co`
- **Status:** ✅ Configured in `.env.monitoring`

### Credentials File: `.env.local`

Your local credentials include:

```bash
# Supabase - Project 1 (goxdevkqozomyhsyxhte)
NEXT_PUBLIC_SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co
SUPABASE_PROJECT_REF=goxdevkqozomyhsyxhte
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...
SUPABASE_DATABASE_URL=postgresql://postgres:AbaC0_PG$2026_Loans!Analytics@Secure@...
POSTGRES_PASSWORD=AbaC0_PG$2026_Loans!Analytics@Secure
```

**Security Status:** ✅ Securely stored locally (gitignored)

---

## 2. Credential Verification

### Run Credential Check

```bash
./scripts/setup/manage-supabase-credentials.sh
```

**Expected Output:**
```
✅ Found SUPABASE_ANON_KEY
✅ Found SUPABASE_SERVICE_ROLE_KEY
✅ Found POSTGRES_PASSWORD
✅ SUPABASE_ANON_KEY is valid JWT token
✅ SUPABASE_SERVICE_ROLE_KEY is valid JWT token
✅ Created .env.monitoring
```

### Manual Verification

```bash
# Check JWT format
grep SUPABASE_ANON_KEY .env.local | cut -d'=' -f2 | cut -c1-20

# Output should start with: eyJhbGc
```

---

## 3. Local Environment Files

### `.env.local` (Your Machine)

Located: `/path/to/abaco-loans-analytics/.env.local`

**Contains:**
- ✅ Supabase credentials (both projects)
- ✅ PostgreSQL password
- ✅ OpenAI API key
- ✅ Sentry credentials
- ✅ n8n auth
- ✅ Grafana password
- ✅ Azure credentials
- ✅ JWT secret

**Security:**
- ✅ Git-ignored (never committed)
- ⚠️ Contains production credentials - keep secure
- 🔐 Store in secure location

### `.env.monitoring` (Grafana Stack)

Location: `/path/to/abaco-loans-analytics/.env.monitoring`

**Contains:**
```env
GRAFANA_ADMIN_PASSWORD=admin123
SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co
SUPABASE_ANON_KEY=<your-key>
SUPABASE_SERVICE_ROLE_KEY=<your-key>
AZURE_SUBSCRIPTION_ID=<optional>
```

**Auto-created by:**
```bash
./scripts/setup/manage-supabase-credentials.sh
# OR
./scripts/monitoring/setup-grafana.sh
```

---

## 4. GitHub Actions Secrets

### Add Secrets Automatically

```bash
./scripts/setup/add-github-secrets.sh
```

**Prerequisites:**
- GitHub CLI installed (`brew install gh`)
- Authenticated: `gh auth login`

### Required Secrets

| Secret Name                    | Value                                  | Purpose              |
|--------------------------------|----------------------------------------|----------------------|
| **SUPABASE_URL**               | `https://goxdevkqozomyhsyxhte.supabase.co` | API endpoint         |
| **SUPABASE_ANON_KEY**          | `eyJ...` (from Supabase)               | Client-side queries  |
| **SUPABASE_SERVICE_ROLE_KEY**  | `eyJ...` (from Supabase)               | Server-side ops      |
| **SUPABASE_DATABASE_URL**      | `postgresql://postgres:...@db...`     | Direct DB connection |

### Add Secrets Manually

Go to: **GitHub → Settings → Secrets and variables → Actions**

Click "New repository secret" and add:

```
Name: SUPABASE_URL
Value: https://goxdevkqozomyhsyxhte.supabase.co
```

Repeat for each secret in the table above.

### Verify Secrets

```bash
gh secret list
```

Expected output:
```
SUPABASE_ANON_KEY             Updated 2026-02-21
SUPABASE_DATABASE_URL        Updated 2026-02-21
SUPABASE_SERVICE_ROLE_KEY   Updated 2026-02-21
SUPABASE_URL                 Updated 2026-02-21
```

---

## 5. Workflow Configuration

### Tests Workflow

File: `.github/workflows/tests.yml`

**Uses secrets for:**
```yaml
integration-tests:
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
```

### Deploy Workflow

File: `.github/workflows/deploy-multicloud.yml`

**Uses secrets for:**
```yaml
- AZURE_CREDENTIALS
- AZURE_RESOURCE_GROUP
- AWS_ROLE_TO_ASSUME
- AWS_REGION
```

---

## 6. Updating Supabase Credentials

### When to Rotate

- Every 90 days (security best practice)
- After security incident
- When team member leaves
- When credentials are exposed

### How to Rotate

**Step 1: Generate new keys in Supabase**
1. Go to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
2. Click "Rotate" next to the key you want to rotate
3. Copy the new key

**Step 2: Update `.env.local`**
```bash
# Edit .env.local with new key
SUPABASE_ANON_KEY=<new-key>
SUPABASE_SERVICE_ROLE_KEY=<new-key>
```

**Step 3: Update GitHub Secrets**
```bash
gh secret set SUPABASE_ANON_KEY --body '<new-key>'
gh secret set SUPABASE_SERVICE_ROLE_KEY --body '<new-key>'
gh secret set SUPABASE_DATABASE_URL --body '<new-connection-string>'
```

**Step 4: Update `.env.monitoring`**
```bash
./scripts/setup/manage-supabase-credentials.sh
```

**Step 5: Restart services**
```bash
docker compose --profile monitoring restart grafana
```

---

## 7. Troubleshooting

### Issue: "401 Unauthorized" in workflows

**Cause:** Incorrect or expired API key

**Solution:**
1. Verify key in `.env.local`: `grep SUPABASE_ANON_KEY .env.local`
2. Regenerate key in Supabase Dashboard
3. Update GitHub secret: `gh secret set SUPABASE_ANON_KEY --body '<key>'`
4. Re-run workflow

### Issue: "pq: SSL required"

**Cause:** PostgreSQL connection string missing SSL

**Solution:**
```bash
# .env.local should have:
SUPABASE_DATABASE_URL=postgresql://postgres:PASSWORD@db.PROJECT.supabase.co:5432/postgres?sslmode=require
```

### Issue: "Secret not found in workflow"

**Cause:** Secret not added to repository or typo in secret name

**Solution:**
```bash
# List all secrets
gh secret list

# Should show: SUPABASE_ANON_KEY, SUPABASE_DATABASE_URL, etc.

# Verify workflow uses correct names:
grep "secrets\." .github/workflows/*.yml
```

### Issue: Grafana can't connect to Supabase

**Cause:** Wrong credentials in `.env.monitoring`

**Solution:**
```bash
# Regenerate monitoring config
./scripts/setup/manage-supabase-credentials.sh

# Restart Grafana
docker compose --profile monitoring restart grafana

# Check logs
docker logs grafana
```

---

## 8. Security Checklist

### ✅ DO

- [ ] Store `.env.local` locally only (never commit)
- [ ] Rotate API keys every 90 days
- [ ] Use service role key only for server-side operations
- [ ] Enable Row Level Security (RLS) in Supabase
- [ ] Use Azure Key Vault for sensitive secrets in production
- [ ] Audit secret access logs in GitHub
- [ ] Review GitHub Actions logs for exposed secrets

### ❌ DON'T

- [ ] Commit `.env.local` to git (check `.gitignore`)
- [ ] Share credentials in chat/email/PR comments
- [ ] Use same password for multiple services
- [ ] Expose service role key in client-side code
- [ ] Leave credentials in GitHub Actions logs
- [ ] Hardcode credentials in scripts

### Verification

```bash
# Ensure .env.local is git-ignored
cat .gitignore | grep "^\.env"

# Expected output:
# .env
# .env.local
# .env.monitoring
```

---

## 9. Connection Testing

### Test Supabase Connection

```bash
# Run credential check
./scripts/setup/manage-supabase-credentials.sh

# Run Supabase tests
pytest tests/ -m "integration" -v

# Run pipeline validation
python scripts/data/run_data_pipeline.py --mode validate
```

### Test Grafana Connection

```bash
# Start monitoring stack
./scripts/monitoring/setup-grafana.sh

# Test in browser: http://localhost:3001
# Username: admin
# Password: admin123

# Test datasource
# Navigate to: Configuration → Data Sources → Supabase PostgreSQL
# Click "Test" button
# Expected: ✅ "Data source is working"
```

### Test GitHub Actions

1. Push a commit to your branch
2. Go to **GitHub → Actions**
3. Select **Tests** workflow
4. Check **integration-tests** job
5. Should see: "SUPABASE_URL", "SUPABASE_ANON_KEY" in environment

---

## 10. Summary

**Credentials Status:**
- ✅ Supabase Project: `goxdevkqozomyhsyxhte`
- ✅ Local config: `.env.local` (gitignored)
- ✅ Monitoring config: `.env.monitoring` (auto-generated)
- ⏳ GitHub secrets: Ready for configuration
- ✅ Authentication: JWT-based
- ✅ Rotation: Can be done anytime

**Files Created:**
- ✅ `scripts/setup/manage-supabase-credentials.sh` - Verify credentials
- ✅ `scripts/setup/add-github-secrets.sh` - Add to GitHub Actions
- ✅ `scripts/monitoring/setup-grafana.sh` - Setup Grafana
- ✅ `docs/GRAFANA_SETUP_GUIDE.md` - Grafana documentation
- ✅ `docs/CREDENTIALS_SETUP.md` - This file

---

## Support

**Questions?**
- Review `.env.local` for local credentials
- Check GitHub secret list: `gh secret list`
- Review workflow logs: GitHub → Actions → Workflow → Job
- Test connection: `./scripts/setup/manage-supabase-credentials.sh`

