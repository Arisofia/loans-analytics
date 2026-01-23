# Runbook: Secret Rotation

**Status**: 🟢 ACTIVE
**Last Updated**: 2026-01-05
**Owner**: DevOps / Security

---

## 1. Overview
This runbook describes the process for rotating critical secrets used by the Abaco Analytics platform to mitigate the impact of potential leaks.

## 2. Target Secrets
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `HUBSPOT_API_KEY`
- `SUPABASE_KEY` / `SUPABASE_SERVICE_ROLE_KEY`
- `AZURE_STORAGE_CONNECTION_STRING`

## 3. Rotation Process

### 3.1 GitHub Secrets
1. Navigate to **Settings → Secrets and variables → Actions**.
2. Update the secret value in the repository or environment secrets.
3. Trigger a manual workflow run to verify the new secret (e.g., `.github/workflows/ci.yml`).

### 3.2 Azure App Service
1. Navigate to the **App Service → Configuration → Application settings**.
2. Update the environment variable value.
3. **Save** and restart the App Service.
4. Verify connectivity via `/?page=health`.

### 3.3 Supabase
1. Navigate to **Project Settings → API**.
2. Roll the API keys if necessary.
3. Update `NEXT_PUBLIC_SUPABASE_ANON_KEY` in GitHub Secrets and Vercel/Azure environments.

## 4. Emergency Revocation
If a secret is confirmed to be leaked:
1. Immediately revoke the key at the provider (OpenAI, HubSpot, etc.).
2. Follow the rotation process above to provision a replacement.
3. Audit recent logs for unauthorized access using the leaked key.

## 5. Verification Checklist
- [ ] Pipeline runs pass successfully.
- [ ] Dashboard (Streamlit) loads data without auth errors.
- [ ] Agents can successfully query MockLLM/OpenAI/Anthropic.
