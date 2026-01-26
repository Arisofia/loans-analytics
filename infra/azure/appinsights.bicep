// appinsights.bicep
// Azure Application Insights resource for monitoring

param location string = resourceGroup().location
param appInsightsName string

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
  }
}

output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
