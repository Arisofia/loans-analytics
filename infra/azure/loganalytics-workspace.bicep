// Log Analytics Workspace for abaco-logs
// This workspace will be used for Application Insights and logging

param workspaceName string = 'abaco-logs'
param location string = 'eastus'
param sku string = 'PerGB2018'
param retentionInDays int = 90

@description('Tags to apply to the workspace')
param tags object = {
  Environment: 'Production'
  Project: 'abaco-loans-analytics'
  ManagedBy: 'Bicep'
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: sku
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: -1
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output customerId string = logAnalyticsWorkspace.properties.customerId
