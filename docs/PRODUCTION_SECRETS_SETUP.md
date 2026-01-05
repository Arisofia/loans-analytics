# Production Secrets Setup - Complete Guide

**Status**: Complete
**Last Updated**: January 1, 2026
**Purpose**: Configure all GitHub Actions secrets for unified output exports and production deployments

---

## Overview

This guide provides step-by-step instructions for setting up all secrets required by the batch export pipelines and output integrations to Figma, Azure, Supabase, Meta, and Notion.

**Note**: Never commit secrets to the repository. All credentials should be stored in GitHub Actions Secrets only.

---

## ✅ Already Configured (From Previous Session)

These secrets are documented as previously set:

```text
SUPABASE_URL: https://zpowfbeftxexzidlxndy.supabase.co
SUPABASE_ANON_KEY: <REDACTED>
FIGMA_TOKEN: <REDACTED>
FIGMA_FILE_KEY: <REDACTED>
```

---

## 🔧 Priority Secrets to Add (Production Readiness)

### 1. Supabase Database URL (Transaction Pooler)

**Environment Variable**: `DATABASE_URL`

**Why**: Required for KPI persistence and analytics data writes via Supabase PostgreSQL.

**How to get**:

1. Go to [Supabase Dashboard](https://app.supabase.com) → Select project `abaco-loans-analytics`
2. Settings → Database → Connection string → Select **Transaction Pooler** tab
3. Copy the connection string
4. Replace `[YOUR-PASSWORD]` with your Supabase database password

**Format**:

```text
postgres://postgres:[PASSWORD]@db.zpowfbeftxexzidlxndy.supabase.co:6543/postgres
```

**Why Port 6543?**: Transaction pooler is ideal for serverless/stateless applications (better than direct connection port 5432).

**To Add to GitHub**:

1. Go to repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `DATABASE_URL`
4. Value: [paste connection string]
5. Click "Add secret"

---

### 2. Azure Service Principal Credentials

**Environment Variable**: `AZURE_CREDENTIALS`

**Why**: Required for:

- App Service deployments
- Azure Blob Storage access (alternative to connection string)
- Azure Dashboard creation
- Azure Monitor operations

**How to create**:

Run this Azure CLI command (requires Azure CLI installed and authenticated):

```bash
az ad sp create-for-rbac \
  --name "abaco-loans-analytics-github" \
  --role contributor \
  --scopes /subscriptions/695e4491-d568-4105-a1e1-8f2baf3b54df/resourceGroups/AI-MultiAgent-Ecosystem-RG \
  --sdk-auth
```

**Output** (copy entire JSON):

```json
{
  "clientId": "00000000-0000-0000-0000-000000000000",
  "clientSecret": "secret-value-here",
  "subscriptionId": "695e4491-d568-4105-a1e1-8f2baf3b54df",
  "tenantId": "00000000-0000-0000-0000-000000000000",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

**To Add to GitHub**:

1. Go to repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `AZURE_CREDENTIALS`
4. Value: [paste entire JSON from above]
5. Click "Add secret"

---

### 3. Azure Storage Connection String

**Environment Variable**: `AZURE_STORAGE_CONNECTION_STRING`

**Why**: Direct access to Azure Blob Storage for exporting files.

**How to get**:

1. Azure Portal → Storage account `abacostgprod` (or your storage account)
2. Settings → Access keys
3. Copy "Connection string" under "key1"

**Format**:

```text
DefaultEndpointsProtocol=https;AccountName=abacostgprod;AccountKey=...;EndpointSuffix=core.windows.net
```

**To Add to GitHub**:

1. Settings → Secrets and variables → Actions
2. Name: `AZURE_STORAGE_CONNECTION_STRING`
3. Value: [paste connection string]

---

### 4. Azure Resource IDs (For Dashboard & Monitoring)

**Environment Variables**:

- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`
- `AZURE_DASHBOARD_NAME`

**To get**:

1. Azure Portal → Your resource group `AI-MultiAgent-Ecosystem-RG`
2. Copy the Resource Group ID
3. Subscription ID: visible in the portal URL or Settings

**Values**:

```text
AZURE_SUBSCRIPTION_ID: 695e4491-d568-4105-a1e1-8f2baf3b54df
AZURE_RESOURCE_GROUP: AI-MultiAgent-Ecosystem-RG
AZURE_DASHBOARD_NAME: abaco-analytics-dashboard
```

**To Add to GitHub**: Add each as a separate secret in Actions Secrets.

---

## 📋 Secondary Secrets (For Full Integrations)

### 5. Supabase Service Role Key

**Environment Variable**: `SUPABASE_SERVICE_ROLE`

**Why**: Required for server-side operations and data writes.

**How to get**:

1. Supabase Dashboard → Settings → API
2. Copy the "service_role secret"

**To Add to GitHub**:

1. Settings → Secrets → New repository secret
2. Name: `SUPABASE_SERVICE_ROLE`
3. Value: [paste key]

---

### 6. Meta (Facebook) Integration

#### 6a. Meta Access Token

**Environment Variable**: `META_ACCESS_TOKEN`

**Why**: Required for Facebook Pixel tracking and Ads Manager API access.

**How to get**:

1. [Meta Business Suite](https://business.facebook.com/) → Settings → Apps and websites
2. Select your app → Settings → Tokens
3. Copy "User access token" (long-lived, 60+ days)

**To Add**:

- Name: `META_ACCESS_TOKEN`

#### 6b. Meta Pixel ID

**Environment Variable**: `META_PIXEL_ID`

**How to get**:

1. Meta Business Suite → Data sources → Pixels
2. Click your pixel → Settings
3. Copy Pixel ID

**To Add**:

- Name: `META_PIXEL_ID`

#### 6c. Meta Ad Account ID

**Environment Variable**: `META_AD_ACCOUNT_ID`

**How to get**:

1. Meta Ads Manager → Settings (gear icon) → Ad account settings
2. Copy "Ad Account ID" (format: `act_1234567890`)

**To Add**:

- Name: `META_AD_ACCOUNT_ID`

---

### 7. Notion Integration

#### 7a. Notion API Key

**Environment Variable**: `NOTION_API_KEY`

**How to get**:

1. [Notion Settings](https://notion.so/profile/settings) → Integrations → Develop your own integrations
2. Click "New integration"
3. Name: `Abaco Analytics Export`
4. Copy the "Internal Integration Token"

**To Add**:

- Name: `NOTION_API_KEY`

#### 7b. Notion Database ID

**Environment Variable**: `NOTION_DATABASE_ID`

**How to get**:

1. Open your Notion database in browser
2. Copy the 32-character ID from the URL: `https://notion.so/{YOUR_WORKSPACE}/{DATABASE_ID}?v=...`

**To Add**:

- Name: `NOTION_DATABASE_ID`

#### 7c. Notion Reports Page ID

**Environment Variable**: `NOTION_REPORTS_PAGE_ID`

**How to get**:

1. Create a page in Notion for analytics reports
2. Copy the page ID from the URL

**To Add**:

- Name: `NOTION_REPORTS_PAGE_ID`

---

### 8. Figma Additional Configuration

#### 8a. Figma Node ID (Optional)

**Environment Variable**: `FIGMA_DASHBOARD_FRAME_ID`

**How to get**:

1. Open your Figma file
2. Right-click on the frame where you want metric updates
3. Copy "Link to frame" and extract the node ID

**To Add** (optional):

- Name: `FIGMA_DASHBOARD_FRAME_ID`

---

### 9. Other Integration Secrets

#### HubSpot

- `HUBSPOT_API_KEY`: [HubSpot Account Settings → Integrations → API key](https://app.hubspot.com/l/integrations)

#### OpenAI

- `OPENAI_API_KEY`: [OpenAI API Keys](https://platform.openai.com/api-keys)

#### Slack Webhooks

- `SLACK_WEBHOOK_URL`: Incoming webhook for notifications
- `SLACK_WEBHOOK_OPS`: Separate webhook for operations notifications

---

## 🛠️ Implementation Checklist

### Before Production Deployment

- [ ] **Supabase Secrets Added**
  - [ ] `DATABASE_URL` - Transaction pooler connection
  - [ ] `SUPABASE_URL` - Already configured
  - [ ] `SUPABASE_ANON_KEY` - Already configured
  - [ ] `SUPABASE_SERVICE_ROLE` - Service role key

- [ ] **Azure Secrets Added**
  - [ ] `AZURE_CREDENTIALS` - Service principal JSON
  - [ ] `AZURE_STORAGE_CONNECTION_STRING` - Blob storage access
  - [ ] `AZURE_SUBSCRIPTION_ID` - Subscription ID
  - [ ] `AZURE_RESOURCE_GROUP` - Resource group name

- [ ] **Meta Secrets Added**
  - [ ] `META_ACCESS_TOKEN` - Long-lived user token
  - [ ] `META_PIXEL_ID` - Facebook Pixel ID
  - [ ] `META_AD_ACCOUNT_ID` - Ad account ID

- [ ] **Notion Secrets Added**
  - [ ] `NOTION_API_KEY` - Internal integration token
  - [ ] `NOTION_DATABASE_ID` - Analytics metrics database
  - [ ] `NOTION_REPORTS_PAGE_ID` - Reports page

- [ ] **Figma Secrets Added**
  - [ ] `FIGMA_TOKEN` - Already configured
  - [ ] `FIGMA_FILE_KEY` - Already configured
  - [ ] `FIGMA_DASHBOARD_FRAME_ID` - (Optional)

---

## 🚀 Quick Setup Commands

### Validate All Secrets Are Set

```bash
# Check which secrets are configured (requires GitHub CLI)
gh secret list
```

### Test Batch Export Locally

Before deploying to production:

```bash
# Set up environment variables locally
export DATABASE_URL="postgres://..."
export SUPABASE_URL="https://..."
export SUPABASE_SERVICE_ROLE="..."
export FIGMA_TOKEN="figd-..."
export FIGMA_FILE_KEY="..."
export META_ACCESS_TOKEN="..."
export NOTION_API_KEY="..."
export AZURE_STORAGE_CONNECTION_STRING="..."

# Run batch export runner
python src/integrations/batch_export_runner.py --type full --verbose
```

Note: The batch export runner reports success as long as all enabled outputs succeed.
Missing integrations (unset tokens or disabled outputs) are treated as skipped rather than failures.

---

## 🔄 Secret Rotation Schedule

All secrets should be rotated on a regular basis:

| Secret | Rotation Frequency | Instructions |
|--------|-------------------|--------------|
| DATABASE_URL | 90 days | Regenerate in Supabase → Settings → Database |
| META_ACCESS_TOKEN | 90 days | Generate new token in Meta Business Suite |
| AZURE_CREDENTIALS | 90 days | Run `az ad sp create-for-rbac` again |
| OPENAI_API_KEY | 90 days | Generate new key in OpenAI → API Keys |
| NOTION_API_KEY | 180 days | Regenerate in Notion → Integrations |
| FIGMA_TOKEN | 180 days | Generate new token in Figma account settings |

---

## ❌ Troubleshooting

### Secret Not Found in Workflow

**Error**: `Error: Secret FIGMA_TOKEN not found`

**Solution**:

1. Verify secret is added: Settings → Secrets → Check the list
2. Check spelling (case-sensitive)
3. If using environment variables, ensure they're properly referenced: `${{ secrets.FIGMA_TOKEN }}`

### Access Denied to Azure

**Error**: `Azure: AuthorizationError: User does not have access`

**Solution**:

1. Regenerate service principal with correct scope:

   ```bash
   az ad sp delete --id [clientId]
   az ad sp create-for-rbac --name "abaco-loans-analytics-github" \
     --role contributor \
     --scopes /subscriptions/695e4491-d568-4105-a1e1-8f2baf3b54df/resourceGroups/AI-MultiAgent-Ecosystem-RG \
     --sdk-auth
   ```

2. Update `AZURE_CREDENTIALS` secret with new JSON

### Supabase Connection Timeout

**Error**: `Connection timeout to database`

**Solution**:

1. Verify using Transaction Pooler (port 6543), not direct connection (port 5432)
2. Check database password is correct (contains special characters?)
3. Verify IP allowlisting in Supabase (if applicable)

---

## 📚 References

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [Supabase Connection Pooling](https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pooler)
- [Azure Service Principals](https://learn.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [Meta Graph API](https://developers.facebook.com/docs/graph-api)
- [Notion API](https://developers.notion.com/)
- [Figma API](https://www.figma.com/developers/api)

---

**For questions or issues, refer to the specific integration client in `src/integrations/` or check the runbooks in `docs/operations/`.**
