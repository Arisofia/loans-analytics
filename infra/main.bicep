// main.bicep
// Azure Bicep template for fintech analytics platform
// Optimized for VM-quota-free deployment using Container Apps + Supabase

param location string = resourceGroup().location
param webAppName string
param storageAccountName string
param containerImage string = 'python:3.11-slim'

resource storage 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
  }
}

// Log Analytics Workspace
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${webAppName}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

// Container Apps Environment (serverless, no VM quota required)
resource containerAppEnv 'Microsoft.App/managedEnvironments@2023-04-01-preview' = {
  name: '${webAppName}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalyticsWorkspace.properties.customerId
        sharedKey: logAnalyticsWorkspace.listKeys().primarySharedKey
      }
    }
  }
}

// Container App for the analytics application
resource containerApp 'Microsoft.App/containerApps@2023-04-01-preview' = {
  name: webAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: true
      }
    }
    template: {
      containers: [
        {
          name: 'app'
          image: containerImage
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 2
      }
    }
  }
}

// Key Vault for secrets management
resource keyvault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: '${webAppName}-kv'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enabledForDeployment: true
    enabledForTemplateDeployment: true
  }
}

// Application Insights
resource appinsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${webAppName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 90
  }
}

output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output storageAccount string = storage.name
output keyVaultUrl string = keyvault.properties.vaultUri
output appInsightsKey string = appinsights.properties.InstrumentationKey
output appInsightsConnectionString string = appinsights.properties.ConnectionString
