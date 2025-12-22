# Copilot and Enterprise Trial Workflow
Documenting GitHub Copilot usage under the Enterprise trial keeps the team aligned, the security practices auditable, and the outcomes professional.
## 1. Copilot invitations
- Go to **Enterprise Settings > GitHub Copilot**.
- Under **Copilot for Business**, add the teammates who will contribute to `abaco-loans-analytics` (backend, analytics, docs, security).
- Share the invitation link; once accepted, confirm they can use Copilot suggestions in VS Code or Cursor.
- Track adoption per sprint (mention it in the Copilot section of the README) so you can compare productivity KPIs.
## 2. Copilot + workflow integration
- Onboarding doc `docs/ContosoTeamStats-setup.md` already points to the main validation steps—mention Copilot there so people know to ask it to summarize SQL migrations, Docker builds, and workflow triggers.
- Ask Copilot to inspect files by referencing them (e.g., “Use @docs/ContosoTeamStats-setup.md to explain how we run `dotnet ef database update`).
- Log any Copilot-assisted code/commands in your project board to keep traceability for audits.
## 3. Advance security while Copilot learns
- Enable code scanning + Dependabot under `Security > Code security`.
- When a security issue appears, assign it via the Dependabot alerts page (link). Note the remediation plan in a README or Jira ticket; if Copilot suggests a fix, mention it in the comment for that alert.
- Keep the security score link near the doc (https://github.com/Abaco-Technol/abaco-loans-analytics/security/dependabot) so anyone can see the 2 high/1 low alerts.
## 4. Enterprise README checklist
- Create (or expand) `Enterprise-README.md` to summarize: Copilot access, validation branch workflow, Azure free-tier resources used (App Service F1, ACR Basic, Storage), and the GitHub Actions runs (mention `ci-web.yml` and `ci-analytics.yml`).
- Include tenant/subscription details (`abacocapital.co`, subscription `cb1e8785-2893-47a1-be44-d47e13447054`) and the requirement to keep deployments in that scope.
- Outline how to invite members, run scans, and call Copilot with the sample prompts below.
## 5. Sample Copilot prompt
> “I’m working on `abaco-loans-analytics`. Please review `.github/workflows/ci-web.yml`, ensure the Docker image build/push steps are clearly described, and help me document the deployment workflow (ACR, App Service, SQL migrations, Swagger validation). Keep everything inside the free Azure trial, note the KPIs we monitor, and suggest automation improvements for the next sprint.”

Use this prompt to keep Copilot-guided work structured, traceable, and aligned with your fintech-grade outcomes.
