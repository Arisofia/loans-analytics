# Required GitHub Secrets

This document lists all GitHub secrets required for the CI/CD workflows in this repository.

## How to Add Secrets

Navigate to: **Settings → Secrets and variables → Actions**

## Core Secrets (Required)

### SonarCloud Integration
- **`SONAR_TOKEN`** - SonarCloud authentication token for code quality analysis
- **`SONAR_HOST_URL`** - SonarCloud host URL (typically https://sonarcloud.io)
- **`SONAR_TOKEN_GITHUB`** - GitHub token for SonarCloud integration

### Database
- **`DATABASE_URL`** - PostgreSQL connection string for production database
- **`SUPABASE_DB_URI_MONITORING`** - Supabase database URI for monitoring

### Supabase
- **`SUPABASE_URL`** - Supabase project URL
- **`SUPABASE_ANON_KEY`** - Supabase anonymous/public key
- **`SUPABASE_ANON_PUBLIC_KEY`** - Supabase public anonymous key
- **`SUPABASE_SERVICE_ROLE`** - Supabase service role credentials
- **`SUPABASE_SERVICE_ROLE_KEY`** - Supabase service role key
- **`NEXT_PUBLIC_SUPABASE_URL`** - Public Supabase URL for Next.js
- **`NEXT_PUBLIC_SUPABASE_ANON_KEY`** - Public Supabase key for Next.js

## Cloud Infrastructure

### Azure
- **`AZURE_CREDENTIALS`** - Azure service principal credentials (JSON)
- **`AZURE_WEBAPP_PUBLISH_PROFILE`** - Azure Web App publish profile
- **`AZURE_STATIC_WEB_APPS_API_TOKEN_YELLOW_CLIFF_03015B20F`** - Static Web Apps deployment token
- **`AZURE_STORAGE_CONNECTION_STRING`** - Azure Storage connection string
- **`AZUREAPPSERVICE_CLIENTID_F6607BB65D034140A480784B481B338B`** - App Service client ID
- **`AZUREAPPSERVICE_SUBSCRIPTIONID_09482FCEC83B4AD880614EFC42AD11AD`** - Azure subscription ID
- **`AZUREAPPSERVICE_TENANTID_F145EFCA8AD64ED686BE309DA9DFE502`** - Azure tenant ID

### Azure Container Registry
- **`AZURE_ACR_LOGIN_SERVER`** - ACR login server URL
- **`AZURE_ACR_USERNAME`** - ACR username
- **`AZURE_ACR_PASSWORD`** - ACR password

### AWS
- **`AWS_ACCESS_KEY_ID`** - AWS access key ID
- **`AWS_SECRET_ACCESS_KEY`** - AWS secret access key
- **`AWS_S3_BUCKET`** - S3 bucket name for storage

### Vercel
- **`VERCEL_TOKEN`** - Vercel deployment token
- **`VERCEL_ORG_ID`** - Vercel organization ID
- **`VERCEL_PROJECT_ID`** - Vercel project ID

## External Integrations

### Figma (Optional)
- **`FIGMA_PERSONAL_ACCESS_TOKEN`** - Figma API token
- **`FIGMA_FILE_LINK`** - Figma file URL
- **`FIGMA_NODE_ID`** - Figma node ID

### Notion (Optional)
- **`NOTION_INTEGRATION_TOKEN`** - Notion integration token
- **`NOTION_DATABASE`** - Notion database ID
- **`NOTION_REPORTS_PAGE_ID`** - Notion reports page ID

### HubSpot (Optional)
- **`HUBSPOT_API_TOKEN`** - HubSpot API token

### Meta/Facebook (Optional)
- **`FACEBOOK_ACCESS_TOKEN`** - Facebook/Meta API access token
- **`FACEBOOK_AD_ACCOUNT_ID`** - Facebook Ad Account ID
- **`META_PIXEL_ID`** - Meta Pixel ID

### Slack
- **`SLACK_WEBHOOK_URL`** - Primary Slack webhook for notifications
- **`SLACK_WEBHOOK_OPS`** - Slack webhook for operations team
- **`SLACK_WEBHOOK_LEADERSHIP`** - Slack webhook for leadership team
- **`SLACK_BOT_TOKEN`** - Slack bot token

## AI/ML Services

### OpenAI
- **`OPENAI_API_KEY`** - OpenAI API key

### AI Platforms
- **`GEMINI_API_KEY_SIMPLE`** - Google Gemini API key
- **`PERPLEXITY_API_KEY`** - Perplexity AI API key
- **`XAI_TOKEN`** - xAI API token
- **`CLAUDE_ROCKET_TOKEN`** - Claude AI token
- **`TAVILY_KEY`** - Tavily search API key

### ML Observability
- **`OPIK_TOKEN`** - Opik observability token
- **`PHOENIX_TOKEN`** - Phoenix monitoring token

## Analytics & Monitoring

### Amplitude
- **`AMPLITUDE_API_KEY`** - Amplitude analytics API key

### Sentry
- **`NEXT_PUBLIC_SENTRY_DSN`** - Sentry DSN for error tracking

## Docker Registry
- **`DOCKER_USERNAME`** - Docker Hub username
- **`DOCKER_PASSWORD`** - Docker Hub password

## Security & Code Analysis
- **`SNYK_TOKEN`** - Snyk security scanning token
- **`CODERABBIT_TOKEN`** - CodeRabbit code review token

## Testing
- **`E2E_TEST_EMAIL`** - Email for E2E tests
- **`E2E_TEST_PASSWORD`** - Password for E2E tests
- **`E2E_SEED_TABLE`** - Database table for E2E seeding
- **`E2E_SEED_ROWS`** - Number of rows to seed for E2E tests

## Miscellaneous
- **`API_KEY`** - General API key for various services
- **`CASCADE_USERNAME`** - Cascade service username
- **`CASCADE_PASSWORD`** - Cascade service password
- **`MIDDLEWARE_SHARED_SECRET`** - Shared secret for middleware authentication

## Secret Validation

The CI workflows include automatic secret validation. Missing secrets will be detected and reported in workflow runs.

### Optional vs Required

- **Required**: Core functionality will fail without these secrets
- **Optional**: Features degrade gracefully if these secrets are missing (Figma, Notion, Meta integrations)

## Security Best Practices

1. **Never commit secrets** to source code
2. **Rotate secrets regularly** (quarterly recommended)
3. **Use minimum required permissions** for service accounts
4. **Monitor secret usage** in GitHub Actions logs
5. **Document secret purpose** when adding new secrets
6. **Remove unused secrets** to reduce attack surface

## Secret Management Tips

- Use environment-specific secrets (dev, staging, production)
- Prefix secrets by service (e.g., `AZURE_*`, `FIGMA_*`)
- Document expiration dates for time-limited credentials
- Test secret rotation in non-production environments first

---

**Last Updated**: 2026-01-24
**Maintainer**: DevOps Team
