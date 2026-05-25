targetScope = 'resourceGroup'

@description('Location for all resources')
param location string = resourceGroup().location

@description('App Service Plan Name')
param appServicePlanName string = 'akshay-plan'

@description('Web App Name - must be globally unique')
param webAppName string

@description('Storage Account Name - lowercase only')
param storageAccountName string

@description('SQL Server Name - globally unique')
param sqlServerName string

@secure()
param sqlAdminPassword string

param sqlAdminUser string = 'sqladmin'
param sqlDatabaseName string = 'akshaydb'

@description('Docker image from Docker Hub')
param dockerImage string = 'akshay34567/flask-todo-app:v3'

@description('Azure Blob Storage connection string')
@secure()
param blobConnectionString string

@description('Database connection string')
@secure()
param dbConnectionString string

resource appPlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: true
  }
}

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: sqlServerName
  location: location

  properties: {
    administratorLogin: sqlAdminUser
    administratorLoginPassword: sqlAdminPassword
    version: '12.0'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: sqlDatabaseName
  location: location

  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux,container'

  properties: {
    serverFarmId: appPlan.id

    siteConfig: {
      linuxFxVersion: 'DOCKER|${dockerImage}'
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '5000'
        }
        {
          name: 'AZURE_STORAGE_CONNECTION_STRING'
          value: blobConnectionString
        }
        {
          name: 'DB_CONNECTION_STRING'
          value: dbConnectionString
        }
        {
          name: 'WEBSITES_ENABLE_APP_SERVICE_STORAGE'
          value: 'false'
        }
      ]
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'todo-images'
}

output websiteUrl string = 'https://${webApp.properties.defaultHostName}'
output sqlServerFQDN string = '${sqlServer.name}.database.windows.net'
