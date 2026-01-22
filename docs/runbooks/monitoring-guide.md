# Runbook: Monitoring & Observability

**Status**: 🟢 ACTIVE
**Last Updated**: 2026-01-05
**Owner**: SRE / DevOps

---

## 1. Monitoring Stack

- **Azure Monitor**: Infrastructure health, App Service metrics (CPU/RAM), and HTTP 5xx errors.
- **GitHub Actions**: Pipeline success/failure trends and execution duration.
- **OpenTelemetry**: Distributed tracing for agents and pipeline runs (exported to Azure Application Insights).
- **Log Analytics**: Centralized logs for cross-service debugging.

## 2. Key Metrics to Watch

- **Pipeline Success Rate**: Target > 95%.
- **Agent Latency**: Target < 2s for ReAct loops.
- **Dashboard Availability**: Target 99.9%.
- **Secret Scanning Alerts**: Target 0 open high/critical.

## 3. Incident Triage

1. **Alert Received**: Check the alert source (Azure Monitor, GitHub Action email).
2. **Dashboard Issue**: Navigate to Azure Portal → App Service → Log Stream.
3. **Pipeline Issue**: Navigate to GitHub Actions → [Workflow Name] → Review failed step logs.
4. **Agent Issue**: Check Opik/OpenTelemetry traces for specific trace IDs.

## 4. Useful Queries (Kusto/Log Analytics)

```kusto
// Find App Service Errors
AppServiceHTTPLogs
| where ScStatus >= 500
| project TimeGenerated, CsUriStem, ScStatus, _ResourceId

// Find Pipeline Failures
GitHubWorkflowRuns
| where Status == "failure"
| summarize count() by WorkflowName, bin(TimeGenerated, 1h)
```

## 5. Contact List

- **Primary SRE**: [Name/Handle]
- **Data Engineering**: [Name/Handle]
- **Security**: [Name/Handle]
