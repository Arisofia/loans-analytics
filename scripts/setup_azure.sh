#!/bin/bash
# Azure Setup Script
# This script helps configure Azure resources for abaco-loans-analytics

set -e

echo "Azure Setup for abaco-loans-analytics"
echo "======================================"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Azure CLI not found. Please install: https://learn.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure
echo "Logging in to Azure..."
az login

# Set subscription
echo ""
echo "Select your subscription:"
az account list --output table
read -p "Enter subscription ID: " SUBSCRIPTION_ID
az account set --subscription "$SUBSCRIPTION_ID"

# Get tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

echo ""
echo "Resource Group: AI-MultiAgent-Ecosystem-RG"
read -p "Press Enter to continue or Ctrl+C to abort..."

# Create or verify resource group
az group create --name AI-MultiAgent-Ecosystem-RG --location eastus

# Create storage account
read -p "Enter storage account name (lowercase, no special chars): " STORAGE_NAME
az storage account create \
    --name "$STORAGE_NAME" \
    --resource-group AI-MultiAgent-Ecosystem-RG \
    --location eastus \
    --sku Standard_LRS

# Get connection string
CONNECTION_STRING=$(az storage account show-connection-string \
    --name "$STORAGE_NAME" \
    --resource-group AI-MultiAgent-Ecosystem-RG \
    --query connectionString -o tsv)

# Create container
az storage container create \
    --name kpi-exports \
    --account-name "$STORAGE_NAME"

# Create Key Vault (optional)
read -p "Create Azure Key Vault? (y/n): " CREATE_KV
if [ "$CREATE_KV" = "y" ]; then
    read -p "Enter Key Vault name: " KV_NAME
    az keyvault create \
        --name "$KV_NAME" \
        --resource-group AI-MultiAgent-Ecosystem-RG \
        --location eastus
    
    KV_URL="https://$KV_NAME.vault.azure.net/"
else
    KV_URL=""
fi

# Generate .env file
echo ""
echo "Generating .env file..."
cat > .env << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Azure Storage
AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME
AZURE_STORAGE_CONNECTION_STRING=$CONNECTION_STRING
AZURE_STORAGE_CONTAINER_NAME=kpi-exports

# Azure Key Vault
AZURE_KEY_VAULT_URL=$KV_URL

# Azure App Service
AZURE_WEBAPP_NAME=abaco-analytics-dashboard
AZURE_RESOURCE_GROUP=AI-MultiAgent-Ecosystem-RG
EOF

echo ""
echo "✓ Setup complete!"
echo "✓ .env file created with Azure configuration"
echo ""
echo "Next steps:"
echo "1. Review and update .env with additional credentials"
echo "2. Run: python scripts/validate_azure_connection.py"
echo "3. Configure service principal if needed for CI/CD"
