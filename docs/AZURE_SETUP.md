# Azure Connection Setup Guide

## Overview

This guide helps you configure complete Azure integration for abaco-loans-analytics.

## Prerequisites

- Azure subscription
- Azure CLI installed ([Install Guide](https://learn.microsoft.com/cli/azure/install-azure-cli))
- Python 3.11+
- Repository cloned locally

## Quick Setup

### 1. Automated Setup (Recommended)

```bash
# Run the automated setup script
bash scripts/setup_azure.sh
```

This script will:

- Authenticate with Azure
- Create/verify resource group
- Create storage account and container
- Create Key Vault (optional)
- Generate `.env` file with credentials

### 2. Manual Setup

#### Step 1: Login to Azure

```bash
az login
az account set --subscription <your-subscription-id>
```

#### Step 2: Create Resource Group

```bash
az group create \
  --name AI-MultiAgent-Ecosystem-RG \
  --location eastus
```

#### Step 3: Create Storage Account

```bash
# Choose a unique storage account name (lowercase, no special chars)
STORAGE_NAME="abacoanalytics$(date +%s)"

az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --location eastus \
  --sku Standard_LRS \
  --min-tls-version TLS1_2
```

#### Step 4: Create Storage Container

```bash
az storage container create \
  --name kpi-exports \
  --account-name "$STORAGE_NAME"
```

#### Step 5: Get Connection String

```bash
az storage account show-connection-string \
  --name "$STORAGE_NAME" \
  --resource-group AI-MultiAgent-Ecosystem-RG
```

#### Step 6: Create Key Vault

```bash
KV_NAME="abaco-kv-$(date +%s)"

az keyvault create \
  --name "$KV_NAME" \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --location eastus \
  --enable-rbac-authorization
```

#### Step 7: Deploy Infrastructure

```bash
# Deploy using Bicep template
az deployment group create \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --template-file infra/azure/main.bicep \
  --parameters \
    webAppName=abaco-analytics-dashboard \
    storageAccountName="$STORAGE_NAME" \
    sqlServerName=abaco-sql-server \
    sqlDbName=abaco-analytics-db \
    sqlAdminLogin=sqladmin \
    sqlAdminPassword="<strong-password>"
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Update the following in `.env`:

```env
# From Azure CLI commands above
AZURE_SUBSCRIPTION_ID=<your-subscription-id>
AZURE_TENANT_ID=<your-tenant-id>
AZURE_STORAGE_ACCOUNT_NAME=<storage-account-name>
AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_KEY_VAULT_URL=https://<keyvault-name>.vault.azure.net/

# From deployment output
AZURE_WEBAPP_NAME=abaco-analytics-dashboard
AZURE_RESOURCE_GROUP=AI-MultiAgent-Ecosystem-RG
```

### 4. Validate Connection

```bash
# Install required packages
pip install azure-identity azure-storage-blob azure-keyvault-secrets azure-mgmt-resource

# Run validation script
python scripts/validate_azure_connection.py
```

## App Service Startup (Required for Python)

Azure App Service expects `requirements.txt` at the repository root. This repo uses a root `requirements.txt` that delegates to `dashboard/requirements.txt`.

If you deploy the dashboard, set the App Service startup command to:

```bash
bash startup.sh
```

This script launches Streamlit with the port provided by App Service.

## Managed Identity Setup (Recommended for Production)

### Enable System-Assigned Managed Identity on App Service

```bash
az webapp identity assign \
  --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG
```

### Grant Storage Access

```bash
# Get the principal ID
PRINCIPAL_ID=$(az webapp identity show \
  --name abaco-analytics-dashboard \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --query principalId -o tsv)

# Assign Storage Blob Data Contributor role
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/AI-MultiAgent-Ecosystem-RG/providers/Microsoft.Storage/storageAccounts/$STORAGE_NAME"
```

### Grant Key Vault Access

```bash
# Assign Key Vault Secrets User role
az role assignment create \
  --assignee "$PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/AI-MultiAgent-Ecosystem-RG/providers/Microsoft.KeyVault/vaults/$KV_NAME"
```

## GitHub Actions Integration

### Add Secrets to GitHub

```bash
# Get service principal (for GitHub Actions)
az ad sp create-for-rbac \
  --name "abaco-analytics-github" \
  --role Contributor \
  --scopes /subscriptions/<subscription-id>/resourceGroups/AI-MultiAgent-Ecosystem-RG \
  --sdk-auth
```

Add these secrets to your GitHub repository:

- `AZURE_CREDENTIALS` - Output from the above command
- `AZURE_STORAGE_CONNECTION_STRING` - From Step 5
- `AZURE_SUBSCRIPTION_ID`
- `AZURE_RESOURCE_GROUP`

## Testing the Connection

### Test Storage Upload

```python
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

# Using connection string
client = BlobServiceClient.from_connection_string(
    os.getenv("AZURE_STORAGE_CONNECTION_STRING")
)

# Or using managed identity
account_url = f"https://{os.getenv('AZURE_STORAGE_ACCOUNT_NAME')}.blob.core.windows.net"
client = BlobServiceClient(account_url=account_url, credential=DefaultAzureCredential())

# Test upload
container_client = client.get_container_client("kpi-exports")
blob_client = container_client.get_blob_client("test.json")
blob_client.upload_blob(b'{"test": "data"}', overwrite=True)
print("✓ Successfully uploaded test file")
```

### Test Key Vault Access

```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

client = SecretClient(
    vault_url=os.getenv("AZURE_KEY_VAULT_URL"),
    credential=DefaultAzureCredential()
)

# Test access
try:
    list(client.list_properties_of_secrets())
    print("✓ Successfully connected to Key Vault")
except Exception as e:
    print(f"✗ Key Vault connection failed: {e}")
```

## Troubleshooting

### Common Issues

1. **"Storage account name is not available"**
   - Choose a different, unique storage account name
   - Must be 3-24 characters, lowercase letters and numbers only

2. **"Insufficient permissions"**
   - Ensure you have Owner or Contributor role on the subscription
   - Check RBAC assignments: `az role assignment list --assignee <your-email>`

3. **"Key Vault access denied"**
   - Verify managed identity is enabled
   - Check role assignments for Key Vault
   - Ensure Key Vault is using RBAC authorization

4. **"DefaultAzureCredential failed"**
   - Run `az login` to authenticate
   - Set environment variables for service principal if in CI/CD
   - Check firewall rules if running from restricted network

### Validation Script Output

Expected output when everything is configured correctly:

```text
Azure Connection Validator
==================================================
✓ Loaded 15 variables from .env

1. Checking required packages...
✓ All required Azure packages installed

2. Validating Azure credentials...
✓ Azure credentials validated successfully

3. Validating Azure Storage connection...
✓ Azure Storage connection (connection string) validated

4. Validating Azure Key Vault connection...
✓ Azure Key Vault connection validated

==================================================
✓ All Azure connections validated successfully!
```

## Next Steps

1. Configure Supabase connection (see main README)
2. Set up API keys for LLM providers
3. Run the batch analytics pipeline
4. Deploy to Azure App Service

## Support

For issues:

1. Check validation script output: `python scripts/validate_azure_connection.py`
2. Review Azure Portal logs
3. Check GitHub workflow runs for deployment errors
