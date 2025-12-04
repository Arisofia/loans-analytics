# Tools, Integrations, and Agent Triggers

Use this checklist to connect the project’s external services and to start the automations/agents that keep analytics, CI, and presentations in sync.

## 1. Azure data plane (SQL/Cosmos/Storage)
- Confirm you have an Azure subscription and resource group that matches the values referenced in docs/ContosoTeamStats-setup.md.
- Create or reuse Azure SQL, Cosmos DB, and Storage resources; record the connection strings.
- Export secrets to your shell (or a `.env`) before running any tooling:
  - `AZURE_SQL_CONNECTION_STRING`
  - `AZURE_COSMOS_CONNECTION_STRING`
  - `AZURE_STORAGE_CONNECTION_STRING`
- Run the Deno guard to validate required directories and environment wiring:
  ```bash
  deno run --allow-all main.ts
  ```

## 2. Supabase
- In the Supabase dashboard, create a project and enable Postgres + Storage buckets as needed for analytics exports.
- Add these env vars locally and to CI secrets:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE`
- Verify the connection by hitting the health endpoint or a small `fetch` from `apps/analytics`.

## 3. Vercel
- Create/import the `apps/web` project in Vercel.
- Set the Azure/Supabase/OpenAI keys as Vercel project environment variables.
- Enable the **Preview Deployments** GitHub integration so each PR generates a URL that QA can reference in agent reports.

## 4. OpenAI / Gemini / Claude
- Choose at least one provider; set the API key in your shell and CI (e.g., `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`).
- For local notebooks or pipelines, add a thin wrapper that checks which key exists and falls back gracefully when none are present.
- Run a smoke test from `apps/analytics` or `streamlit_app.py` to confirm completions work.

## 5. SonarCloud
- Create the project in SonarCloud and grab the token.
- Add `SONAR_TOKEN` as a GitHub Actions secret and confirm `sonar-project.properties` matches the organization key.
- Trigger the scan locally for a dry run:
  ```bash
  npm run lint
  # then
  sonar-scanner
  ```

## 6. GitHub Actions
- Ensure the following secrets exist in the repo/org: Azure credentials, database/storage connection strings, Supabase keys, OpenAI/Gemini/Claude tokens, `SONAR_TOKEN`.
- Run the workflows manually once to validate credentials:
  - `ci-web.yml` for Next.js build and lint.
  - `ci-analytics.yml` for Python pipeline checks.
  - Any deployment workflow that pushes the Docker image to ACR.
- Capture the run URLs for audit and agent summaries.

## 7. Fitten Code AI
- Place the model artifacts on a secure path and reference it in `fitten.config.toml`.
- Set `FITTEN_CONFIG` in your shell/CI to point at the config file.
- Add a CI step (or local command) to run a scan:
  ```bash
  fitten sniff apps/web
  ```
- Keep the Fitten output with SonarCloud results in the PR discussion for traceability.

## 8. Copilot and agent triggers
- Invite teammates via GitHub Copilot for Business and confirm acceptance.
- Add the `@copilot` account to the GitHub Enterprise org so enterprise prompts and inline guidance stay enabled for this repo.
- Run `scripts/export_copilot_slide_payload.py` after analytics updates so presentation agents receive refreshed content:
  ```bash
  python scripts/export_copilot_slide_payload.py
  ```
- When opening PRs, ask Copilot (or another agent) to summarize CI results, SonarCloud issues, and Fitten findings using the payload above plus workflow logs.
- Assign `@codex` to the commit/PR so the automation that posts summaries and links has a consistent owner.
- Maintain an `Enterprise-README.md` snippet (or PR description) that links to the latest Copilot prompt, workflow runs, and preview URLs.

## 9. Quick validation loop
- Load env vars, run `deno run --allow-all main.ts`, and execute the lint/test targets from the workflows.
- Trigger a one-off GitHub Actions run to confirm external services respond.
- Share the Copilot/agent summary plus preview deployment link in your ticket or PR to prove end-to-end coverage.
