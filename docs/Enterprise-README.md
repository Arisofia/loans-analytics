# Enterprise Delivery Playbook — ContosoTeamStats on GitHub Enterprise

This guide captures the operational steps to onboard the team to GitHub Copilot, enforce SAML SSO and enterprise guardrails, run Advanced Security scans, and accelerate the ContosoTeamStats (.NET 6 API) delivery to Azure with CI/CD, monitoring, and dashboards.

## Roles and ownership

- **Enterprise Owner**: configures SAML/SCIM, audit log streaming, default security policies, billing/seat assignments.
- **Org Admin/Security Admin**: enforces security defaults (branch protections, secret scanning push protection, code scanning policies), manages teams, and approves Copilot seat usage.
- **Platform/DevOps**: maintains CI/CD (GitHub Actions + Azure OIDC), Dependabot, environment protections, and observability exports.
- **Team Leads**: approve pull requests, monitor KPIs, and triage security/code scanning alerts.

## Invite the team to GitHub Copilot

1. In **Enterprise/Org Settings → Copilot → Policies**, enable **Copilot for Enterprise** and set the scope to **Allow for all members** or a pilot team.
2. Assign seats via **Billing → Copilot → Seat management → Add members** (supports CSV upload of GitHub usernames). Keep a shared roster in `docs/access-matrix.md` for audits.
3. Map users to GitHub teams (`api-engineering`, `sre-observability`, `analytics`) and grant repo access through teams only. Verify via `Settings → Collaborators and teams` that there are no direct invites.
4. Post an onboarding checklist in Discussions/Wiki with links to IDE setup (VS/VS Code/JetBrains), security policy, and PR flow. Include a **welcome issue template** that asks new members to confirm SSO + MFA and run `npm test` locally.

## Configure SAML SSO (with SCIM if available)

1. As an Enterprise Owner, open **Enterprise Settings → Authentication security → SAML single sign-on → Configure SAML**.
2. Choose your IdP (e.g., Entra ID/Azure AD) → **Upload XML metadata** or paste the IdP URL. Capture the GitHub **Entity ID** and **ACS URL** to paste back into the IdP.
3. In Entra ID: **Enterprise applications → New application → Create your own → Non-gallery** → add Reply URL = ACS, Identifier = Entity ID. Map claims: `user.mail` → NameID, `user.userprincipalname` → `userName`, `user.displayname` → `displayName`, `user.mail` → `email`, `user.department` → `department`.
4. Enable **Assignment required** and add the ContosoTeamStats groups. Turn on **JIT provisioning**; if SCIM licensed, set **Provisioning → Automatic** with the GitHub SCIM URL + token.
5. Back in GitHub, click **Test SAML configuration**, then **Enforce SAML SSO** and **Require SSO for PATs/SSH**. Validate: `ssh -T git@github.com` should prompt SSO, and `gh auth status` should show the SSO session.

## Enterprise guardrails to enable

- **Identity & access**: enforce SSO; require Passkeys/WebAuthn for MFA; disable outside collaborators; set **default repo visibility = private**.
- **Repo protections**: branch protections with 2 reviewers, required checks (`ci-main`, `codeql`, `sonarcloud`), signed commits, linear history, and **CODEOWNERS** for API/service paths. Mark CodeQL and CI as **required workflows** on `main`.
- **Secrets**: enable **Secret scanning + Push Protection + Token Leakage Prevention**; add custom patterns for internal tokens. Enable `actions: read` default permission and **environment secrets** for deployments.
- **Auditability**: stream **audit logs** to Log Analytics/SIEM, enable **security overview**; ship webhook events for secret scanning to the SIEM to alert.
- **Policy controls**: enable **content attachment restrictions**, restrict GitHub Apps to an allowlist, require **Dependabot auto-triage rules** and auto-merge for patch updates after checks pass.

## Code security scans for this repo

- **CodeQL code scanning**: enable via **Security → Code scanning alerts → Set up → Default** or keep `.github/workflows/codeql.yml`. The workflow scans **JavaScript/TypeScript, Python, and C#** on PRs to `main`, weekly, and via **Run workflow** for ad-hoc reruns. Concurrency is enabled to cancel superseded runs. C# analysis activates only when a `.csproj`/`.sln` exists to avoid spurious failures in non-.NET repos. For local verification: `gh codeql database analyze --language=javascript,python,csharp` (requires GHAS CLI and token).
- **Secret scanning**: confirm org-level Secret scanning + Push Protection. Add custom patterns for internal API keys. Verify with **Security → Secret scanning → Enable for private repos** and test by pushing a fake secret (should be blocked).
- **Dependabot**: `.github/dependabot.yml` now covers **npm, pip, NuGet, and GitHub Actions** weekly. Use branch protections to require reviewers/status checks and enable auto-merge for patch groups.
- **Sonar/SAST**: keep `sonarcloud.yml` active; gate merges on the quality gate; notify `#sre` on failures via webhook.

## CI/CD to Azure (ACR + App Service)

1. **OIDC to Azure**: in Azure, create a Federated Credential on the SP used for deployment (scope: `api://AzureADTokenExchange`, subject: `repo:<org>/<repo>:environment:<env>`). Store `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, and `AZURE_RESOURCE_GROUP` as GitHub Environment secrets.
2. **Build & test**: rely on the all-in-one `ci-main.yml` workflow that runs Java/Gradle, Python analytics, and Next.js lint/build/type-check so every push has cross-cutting verification. Add a .NET job that runs `dotnet restore`/`dotnet test` for ContosoTeamStats when the API project is present.
3. **Containerize**: build/push Docker image to ACR using `docker build` + `az acr login` or `azure/login@v2` + `azure/cli@v2`. Tag as `${{ github.sha }}` and `latest`.
4. **Deploy**: use `azure/webapps-deploy@v3` (App Service) pointing to the ACR image tag; guard with environment protection rules (approvals, secrets, lock deployments) per `dev`/`prod`.
5. **Infra-as-Code**: place ARM/Bicep/Terraform in `infra/azure` with review requirements. Run `terraform plan` in PRs and `terraform apply` on protected branches.

## Observability, KPIs, and alerting (free tier friendly)

- **Delivery KPIs**: lead time for changes (<24h target), deployment frequency (>= 2/day to non-prod), MTTR (<4h), change failure rate (<15%), % PRs passing required checks (>95%), Dependabot PR time-to-merge (<48h for patch).
- **Security KPIs**: open CodeQL/secret alerts trend (no >7d open), mean time to remediate vuln/secret (<72h), Dependabot exposure window (<48h for critical/high), signed-commit coverage (>90%), SSO compliance = 100%.
- **Runtime KPIs**: App Service availability (>99.9%), p95 latency (<300ms for API), error budget burn rate (<1 over 6h), container restart count (0 for last 24h), ACR pull errors (0), build success rate (>95%).
- **Alerts/Dashboards**: GitHub **Security Overview**, GitHub Actions workflow success trend, Azure Monitor dashboards (HTTP 5xx/latency, CPU/memory, ACR pull errors), SIEM alerts for audit log anomalies and secret scanning webhooks, PagerDuty/Teams hooks for CodeQL critical alerts and failed deployments.

## Quick commands and links

- **CodeQL local prep**: `gh codeql database analyze --language=javascript,python,csharp` (requires GHAS CLI and auth).
- **Dependabot status**: `gh api repos/:owner/:repo/dependabot/alerts --paginate | jq length` to count open alerts.
- **Secret scanning test**: commit a fake secret pattern, expect push rejection with push protection enabled.
- **Docs**: GitHub Enterprise Cloud → Security → [Advanced Security](https://docs.github.com/enterprise-cloud@latest/code-security) and [Copilot](https://docs.github.com/enterprise-cloud@latest/copilot/overview-of-github-copilot).
