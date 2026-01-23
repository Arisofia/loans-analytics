# Runbook: App Service Diagnostics (Azure)

**Purpose**

- Safely troubleshoot Azure App Service availability, performance, deployment, configuration, and networking issues.
- Capture actionable evidence without disrupting production.

**When to use**

- HTTP 5xx spikes, app down, or timeouts.
- Slow responses or resource saturation.
- Suspected bad deployment or configuration change.
- Networking or SSL/domain issues.

## Safety and access guardrails

- Start read-only and capture evidence before changing anything.
- Do not paste secrets or PII into tickets or chat. Redact tokens and mask PII in logs before sharing.
- Avoid restarts, scaling, auto-heal rule changes, or app setting edits until you have evidence and approval.
- Use lightweight diagnostics first; only enable profiling or verbose logging when necessary and approved.
- Timebox changes and announce them in the incident channel.

## Prerequisites

- Azure Portal access to the App Service and resource group.
- Read access to Application Insights if app-level exceptions are needed.
- App name, resource group, subscription, and environment (prod/stage).

## Open App Service diagnostics

1. Azure Portal -> App Service (or App Service Environment).
2. Select **Diagnose and solve problems**.
3. Use the search box or select a troubleshooting category.

Notes:

- Guided diagnostics are most helpful for incidents within the last 24 hours.
- Graphs are always available for historical analysis.
- Works for Windows, Linux, custom containers, App Service Environments, and Azure Functions.

## Quick triage (5-10 minutes)

1) **Confirm scope and baseline**

- App name, resource group, region, plan, and default domain.
- Current status (Running/Stopped).
- Last deployment time and commit.

1) **Check Availability and Performance**

- Open **Overview** or **App Down / Web App Down**.
- Review the diagnostic report and top indicators.

1) **Review risk alerts**

- Open **Risk Assessments** and capture any recommendations.

1) **Check logs for first error**

- App Service -> **Log stream**.
- If containerized, verify container logs and startup output.

## Diagnostic interface guide

- **Search box**: fastest way to find a diagnostic (availability, CPU, memory, logs).
- **Risk alerts**: configuration checks with recommendations.
- **Categories**: Availability and Performance, Configuration and Management, SSL and Domains, Risk Assessments, Deployment, Networking, Navigator, Diagnostic Tools, Load Test your App.

## Common scenarios and safe next steps

### App down or 5xx

- **Web App Down** report: identify platform or app failures.
- Verify health endpoint if available (for example, `/?page=health`).
- Check **Application Logs** and **Log stream** for first error.
- For containers:
  - Review **Linux - Number of Running Containers**.
  - Confirm correct port binding (`WEBSITES_PORT` or `PORT`) and startup command.

Safe actions:

- Capture the first error log and deployment time correlation.
- Consider redeploying the last known good build if the issue aligns with a release.

### Slow responses or timeouts

- Check **CPU Usage** and **Memory Usage** graphs for saturation.
- Use **Process List** and **Process Fill List** to spot hot processes.
- Review **SNAT Port Exhaustion** and **TCP Connections** if outbound calls are heavy.
- If Application Insights is enabled, review exceptions and dependency calls.
- Collect a profiling trace only if approved and during a safe window.

Safe actions:

- Capture graphs and timestamps before taking remediation steps.
- Scale or restart only with approval and documented reasoning.

### Deployment issues

- Go to **Deployment** diagnostics or **Deployment Center** logs.
- Check for failed build, missing dependencies, or startup command errors.
- Validate environment variables referenced by startup.

Safe actions:

- Roll back to the last known good deployment if errors align with the latest release.
- Avoid changing runtime or build settings without a rollback plan.

### Configuration and management

- Confirm required app settings and connection strings exist.
- Validate SSL certificates, custom domains, and hostnames.
- Check for recent configuration changes in **Application Changes**.

Safe actions:

- Capture the configuration diff and approval before changing settings.

### Networking

- Inspect **Networking** diagnostics for VNET integration, DNS, or routing issues.
- Check **SNAT Port Exhaustion** for outbound failure symptoms.
- For ASE or private endpoints, verify regional health and routing.

Safe actions:

- Escalate to networking owners if infra changes are required.

## Diagnostic tools (use with care)

- **Auto-healing**: configure temporary mitigation rules only when root cause is unknown and impact is severe.
- **Proactive CPU monitoring** (Windows): set thresholds only with approval.
- **Navigator** (Windows): enable only if needed for dependency mapping.
- **Change analysis**: correlate health changes with deployments and config edits.

## Evidence to capture

- App name, resource group, subscription, region, plan, and default domain.
- Diagnostic report screenshots or key findings (timestamps included).
- First error log line and surrounding context.
- Last deployment time and build artifact reference.
- Any configuration or scaling changes performed.

## Escalation and recovery

- Escalate if:
  - Platform outage is suspected.
  - Repeated crashes after rollback.
  - Network or DNS requires infra-level changes.
- Recovery options (in order of safety):
  1) Redeploy last known good.
  2) Restart app (approved only).
  3) Scale up or out (approved only).

## Post-incident

- Update the incident ticket with evidence, actions, and timeline.
- Capture follow-ups: root cause analysis, runbook updates, test gaps, and alerting improvements.
