# Critical Secrets Report

The following secrets/variables are referenced in workflow YAML files but may be missing from your GitHub repository secrets or .env files. Please review and add them as needed:

## Commonly Referenced Secrets
- SUPABASE_DB_URI_MONITORING
- SLACK_BOT_TOKEN
- OPIK_TOKEN
- PHOENIX_TOKEN
- NEXT_PUBLIC_SENTRY_DSN
- DOCKER_USERNAME
- DOCKER_PASSWORD
- ACR_LOGIN_SERVER
- ACR_USERNAME
- ACR_PASSWORD
- AZURE_CREDENTIALS
- AZURE_ACR_LOGIN_SERVER
- AZURE_ACR_PASSWORD
- AZURE_WEBAPP_PUBLISH_PROFILE
- FIGMA_TOKEN
- AZURE_STORAGE_ACCOUNT_NAME
- AZURE_STORAGE_CONNECTION_STRING
- AZURE_STATIC_WEB_APPS_API_TOKEN
- MIDDLEWARE_SHARED_SECRET
- SUPABASE_SERVICE_ROLE
- CASCADE_USERNAME
- CASCADE_PASSWORD
- SLACK_WEBHOOK_OPS
- SLACK_WEBHOOK_URL
- HUBSPOT_API_TOKEN
- STAGING_SUPABASE_URL
- STAGING_SUPABASE_KEY
- AZURE_STATIC_WEB_APPS_TOKEN_STAGING
- OPENAI_API_KEY
- NOTION_INTEGRATION_TOKEN
- NOTION_DATABASE_ID
- SUPABASE_SERVICE_ROLE_KEY
- ANALYTICS_URL
- GEMINI_API_KEY
- SONAR_TOKEN_GITHUB
- DATABASE_URL
- AWS_S3_BUCKET
- FIGMA_NODE_ID
- AMPLITUDE_API_KEY
- SUPABASE_ANON_PUBLIC_KEY
- SUPABASE_URL
- SUPABASE_ANON_KEY
- SUPABASE_SERVICE_ROLE_KEY
- NEXT_PUBLIC_SUPABASE_URL
- NEXT_PUBLIC_SUPABASE_ANON_KEY
- XAI_TOKEN
- CLAUDE_ROCKET_TOKEN

## Next Steps
1. Review this list and compare with your GitHub repository secrets and .env/.env.example files.
2. Add any missing secrets to GitHub (Settings → Secrets and variables → Actions → New repository secret).
3. For secrets available in .env, copy their values to GitHub secrets.
4. Re-run workflows to confirm errors are resolved.

If you want an automated script to sync .env values to GitHub secrets, let me know!
