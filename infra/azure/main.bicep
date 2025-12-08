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
  allowAzureServices ? [
    {
      name: 'AllowAzureServices'
      startIpAddress: '0.0.0.0'
      endIpAddress: '0.0.0.0'
    }
  ] : [],
  sqlFirewallRules
)

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

resource webapp 'Microsoft.Web/sites@2022-09-01' = {
  name: webAppName
  location: location
  kind: 'app'
  properties: {
    serverFarmId: appserviceplan.id
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

resource sqlserver 'Microsoft.Sql/servers@2022-02-01-preview' = {
  name: sqlServerName
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
  }
}

resource sqlFirewall 'Microsoft.Sql/servers/firewallRules@2022-02-01-preview' = [for rule in firewallRules: {
  name: rule.name
  properties: {
    startIpAddress: rule.startIpAddress
    endIpAddress: rule.endIpAddress
  }
}]

resource sqldb 'Microsoft.Sql/servers/databases@2022-02-01-preview' = {
  name: sqlDbName
  location: location
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648
    sampleName: 'AdventureWorksLT'
  }
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

output webAppUrl string = webapp.properties.defaultHostName
output storageAccount string = storage.name
output sqlDb string = sqldb.name
