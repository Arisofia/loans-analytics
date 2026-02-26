// main.bicep
// Azure Bicep template for fintech analytics platform
// Optimized for FREE TIER deployment using Container Apps + Supabase
// All resources configured for minimum cost (scale-to-zero, minimal retention)

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
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false

  }
}

// Azure Container Registry for application images
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: 'abacoacr${take(uniqueString(resourceGroup().id), 16)}'
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
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
  tags: {
    'azd-service-name': 'abaco-loans-analytics'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    managedEnvironmentId: containerAppEnv.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false  // HTTPS only for security
        transport: 'auto'
        clientCertificateMode: 'accept'
      }
      secrets: [
        {
          name: 'supabase-url'
          keyVaultUrl: '${keyvault.properties.vaultUri}secrets/supabase-url'
          identity: 'system'
        }
        {
          name: 'supabase-anon-key'
          keyVaultUrl: '${keyvault.properties.vaultUri}secrets/supabase-anon-key'
          identity: 'system'
        }
        {
          name: 'storage-connection-string'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'app'
          image: containerImage
          env: [
            {
              name: 'SUPABASE_URL'
              secretRef: 'supabase-url'
            }
            {
              name: 'SUPABASE_ANON_KEY'
              secretRef: 'supabase-anon-key'
            }
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: appinsights.properties.ConnectionString
            }
            {
              name: 'AZURE_STORAGE_CONNECTION_STRING'
              secretRef: 'storage-connection-string'
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              initialDelaySeconds: 30
              periodSeconds: 10
            }
          ]
        }
      ]
      scale: {
        minReplicas: 0  // Scale to zero when idle (free tier)
        maxReplicas: 1
      }
    }
  }
}

// Key Vault for secrets management
resource keyvault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'abacokv${uniqueString(resourceGroup().id)}'
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
    RetentionInDays: 30  // Minimum retention for free tier
  }
}

// Key Vault RBAC - Grant Container App access to secrets
resource kvRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyvault.id, containerApp.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyvault
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
  }
}

// Container App identity can pull images from ACR
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, containerApp.id, '7f951dda-4ed3-4680-a7ca-43fe172d538d')
  scope: containerRegistry
  properties: {
    principalId: containerApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId(
      'Microsoft.Authorization/roleDefinitions',
      '7f951dda-4ed3-4680-a7ca-43fe172d538d'
    )
  }
}

// Storage diagnostic settings for audit logging
resource storageDiagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = {
  name: 'storage-audit-logs'
  scope: storage
  properties: {
    workspaceId: logAnalyticsWorkspace.id
    metrics: [
      {
        category: 'Transaction'
        enabled: true

      }
    ]
  }
}

// Resource lock to prevent accidental deletion
resource storageLock 'Microsoft.Authorization/locks@2020-05-01' = {
  name: 'storage-lock'
  scope: storage
  properties: {
    level: 'CanNotDelete'
    notes: 'Prevent accidental deletion of financial data'
  }
}

output containerAppUrl string = containerApp.properties.configuration.ingress.fqdn
output storageAccount string = storage.name
output keyVaultUrl string = keyvault.properties.vaultUri
output appInsightsKey string = appinsights.properties.InstrumentationKey
output appInsightsConnectionString string = appinsights.properties.ConnectionString
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = containerRegistry.properties.loginServer
