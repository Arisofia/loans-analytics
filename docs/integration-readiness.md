# Integration readiness checklist

This repository offers several integrations that require manual configuration before they are operational. Use the checklist below to confirm which services are wired up in your environment and which still need secrets or infrastructure.

## Available integrations

- Azure SQL, Cosmos DB, and Storage for data workloads.
- Supabase for auth and database hosting.
- Vercel for the Next.js dashboard deployment.
- OpenAI, Gemini, and Claude for AI-assisted features.
- SonarCloud for code quality scanning.
- GitHub Actions for CI/CD pipelines.

## How to validate each integration

- **Azure SQL / Cosmos / Storage**: ensure connection strings and access keys are present in your environment or key vaults. Run a smoke test against each service (e.g., simple read/write scripts) before promoting changes.
- **Supabase**: populate the project URL and service role key in your environment variables, then run a basic auth/database query to confirm connectivity. See `docs/supabase-setup.md` for project-specific wiring.
- **Vercel**: verify the project is connected to the correct GitHub repo and that build secrets are defined. Trigger a preview deployment to confirm builds succeed.
- **OpenAI / Gemini / Claude**: load the corresponding API keys and run a short completion or embedding request to ensure rate limits and billing are in place.
- **SonarCloud**: confirm the `sonar-project.properties` matches your organization key and that the token is supplied in CI. Run a local or CI scan to verify analysis completes.
- **GitHub Actions**: review workflow files under `.github/workflows` (if present) and confirm required secrets are set in the repository. Run the workflows (or `act`) to ensure CI passes.

## Quick environment guard

Before running tooling, you can execute the Deno helper to confirm expected directories exist:

```bash
deno run --allow-all main.ts
```

If the script reports missing paths, address them before attempting the integrations above.
