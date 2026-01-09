// main.bicep
// Azure Bicep template for fintech analytics platform

param location string = resourceGroup().location
param webAppName string
param storageAccountName string
param sqlServerName string
param sqlDbName string
param sqlAdminLogin string
@secure()
param sqlAdminPassword string
@description('Optional SQL firewall rules to open access beyond Azure services (objects require name/startIpAddress/endIpAddress).')
param sqlFirewallRules array = []
@description('Allow Azure services (including the App Service) to reach SQL via the 0.0.0.0 rule.')
param allowAzureServices bool = true

var firewallRules = concat(
  allowAzureServices
    ? [
        {
          name: 'AllowAzureServices'
          startIpAddress: '0.0.0.0'
          endIpAddress: '0.0.0.0'
        }
      ]
    : [],
  sqlFirewallRules
)

resource storage 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

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

resource webapp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appserviceplan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}

resource appserviceplan 'Microsoft.Web/serverfarms@2022-09-01' = {
  name: '${webAppName}-plan'
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
}

resource sqlserver 'Microsoft.Sql/servers@2022-05-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlFirewall 'Microsoft.Sql/servers/firewallRules@2022-05-01-preview' = [
  for rule in firewallRules: {
    name: rule.name
    parent: sqlserver
    properties: {
      startIpAddress: rule.startIpAddress
      endIpAddress: rule.endIpAddress
    }
  }
]

resource sqldb 'Microsoft.Sql/servers/databases@2022-05-01-preview' = {
  name: sqlDbName
  parent: sqlserver
  location: location
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

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

resource appinsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${webAppName}-insights'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    RetentionInDays: 90
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource webappconfig 'Microsoft.Web/sites/config@2022-09-01' = {
  parent: webapp
  name: 'appsettings'
  properties: {
    APPLICATIONINSIGHTS_CONNECTION_STRING: appinsights.properties.ConnectionString
    AZURE_STORAGE_CONNECTION_STRING: 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=core.windows.net'
    AZURE_KEY_VAULT_URL: keyvault.properties.vaultUri
  }
}

output webAppUrl string = webapp.properties.defaultHostName
output storageAccount string = storage.name
output sqlDb string = sqldb.name
output keyVaultUrl string = keyvault.properties.vaultUri
output appInsightsConnectionString string = appinsights.properties.ConnectionString
