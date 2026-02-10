// Log Analytics Workspace for abaco-logs
// Configured for FREE TIER: PerGB2018 with daily cap of 0.5 GB
param workspaceName string = 'abaco-logs'
param location string = 'eastus'
param sku string = 'PerGB2018'
param retentionInDays int = 30  // Reduced from 90 to minimize costs
@description('Tags to apply to the workspace')
param tags object = {
  Environment: 'Production'
  Project: 'abaco-loans-analytics'
  ManagedBy: 'Bicep'
}
param retentionInDays int = 7  // Reduced to 7 for free tier
resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: workspaceName
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'Free'
    }
    retentionInDays: retentionInDays
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    workspaceCapping: {
      dailyQuotaGb: json('0.5')  // Free tier: limit to 0.5 GB/day
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}
output workspaceId string = logAnalyticsWorkspace.id
output workspaceName string = logAnalyticsWorkspace.name
output customerId string = logAnalyticsWorkspace.properties.customerId
