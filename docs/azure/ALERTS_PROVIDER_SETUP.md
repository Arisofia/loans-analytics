# Azure Alerts Management Provider Setup

**Date**: 2026-02-04  
**Purpose**: Enable deployment of Application Insights alert rules  
**Subscription**: `695e4491-d568-4105-a1e1-8f2baf3b54df`

---

## Overview

To enable deployment of Application Insights alert rules, the subscription must be registered for `Microsoft.AlertsManagement`. This is a **one-time setup** per Azure subscription.

## Prerequisites

- Azure CLI installed (`az --version`)
- Contributor or Owner role on subscription `695e4491-d568-4105-a1e1-8f2baf3b54df`
- Authenticated to Azure (`az login`)

## Steps

### 1. Set Active Subscription

```bash
az account set --subscription 695e4491-d568-4105-a1e1-8f2baf3b54df
```

### 2. Register Provider

```bash
az provider register --namespace Microsoft.AlertsManagement
```

### 3. Verify Registration

```bash
# Check registration status (may take 1-2 minutes)
az provider show \
  --namespace Microsoft.AlertsManagement \
  --query "registrationState" \
  -o tsv

# Expected output: "Registered"
```

### 4. Verify Alert Rules Can Deploy

After registration completes, re-run the alert rule deployments that previously failed:

- `Failure-Anomalies-Alert-Rule-Deployment-{guid}`

## Related Deployments

These alert rules depend on the provider being registered:

1. **Failure Anomalies Alert Rule** (3 instances)
   - Resource Group: `abaco-rg`
   - Resource: Application Insights `abaco-loans-app-insights`
   - Purpose: Detect abnormal failure rate increases

## Troubleshooting

### Error: "The subscription is not registered to use namespace 'Microsoft.AlertsManagement'"

**Solution**: Follow steps above to register the provider.

### Registration stuck in "Registering" state

```bash
# Force re-registration
az provider unregister --namespace Microsoft.AlertsManagement
az provider register --namespace Microsoft.AlertsManagement
```

### Verify all required providers

```bash
# List all resource providers and their registration state
az provider list \
  --query "[?namespace=='Microsoft.AlertsManagement' || namespace=='Microsoft.Insights'].{Namespace:namespace, State:registrationState}" \
  -o table
```

## Automation

Add to your IaC/deployment pipeline prerequisites:

```yaml
# .github/workflows/deploy-infra.yml
- name: Register Azure Providers
  run: |
    az provider register --namespace Microsoft.AlertsManagement
    az provider register --namespace Microsoft.Insights
    # Wait for registration
    az provider wait --namespace Microsoft.AlertsManagement --registered
```

## Documentation

- [Azure Resource Providers](https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-providers-and-types)
- [Application Insights Alerts](https://learn.microsoft.com/en-us/azure/azure-monitor/alerts/alerts-overview)

---

**Last Updated**: 2026-02-04  
**Status**: ✅ Required for alert rule deployments
