# Azure Infrastructure

## Descripción

Este directorio contiene los archivos de infraestructura como código (Bicep) para los recursos de Azure del proyecto abaco-loans-analytics.

## Recursos

### Log Analytics Workspace

- **Archivo**: `loganalytics-workspace.bicep`
- **Nombre**: abaco-logs
- **Ubicación**: East US
- **Grupo de recursos**: AI-MultiAgent-Ecosystem-RG
- **Suscripción**: Azure subscription 1 (695e4491-d568-4105-a1e1-8f2baf3b54df)

### Application Insights

- **Archivo**: `appinsights.bicep`
- **Configuración**: `app-insights-config.json`
- **Nombre**: abaco-analytics-insights

## Despliegue del Log Analytics Workspace

Para desplegar el workspace en Azure, ejecuta los siguientes comandos desde la raíz del proyecto:

```bash
# 1. Iniciar sesión en Azure
az login

# 2. Seleccionar la suscripción correcta
az account set --subscription "695e4491-d568-4105-a1e1-8f2baf3b54df"

# 3. Desplegar el workspace
az deployment group create \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --template-file infra/azure/loganalytics-workspace.bicep
```

## Verificación

Después del despliegue, verifica que el workspace se creó correctamente:

```bash
az monitor log-analytics workspace show \
  --resource-group AI-MultiAgent-Ecosystem-RG \
  --workspace-name abaco-logs
```

## Próximos Pasos

1. El workspace `abaco-logs` ahora puede ser referenciado por Application Insights
2. Actualizar la configuración de Application Insights para usar este workspace
3. Configurar alertas y consultas de logs según sea necesario
