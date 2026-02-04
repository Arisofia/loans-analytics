# Azure Container App Deployment Notes

**Last Updated**: 2026-02-04

---

## abaco-loans-app

**Resource**: Container App `abaco-loans-app`  
**Resource Group**: `AI-MultiAgent-Ecosystem-RG`  
**Status**: ✅ Running

### Historical Deployment Note

- **Observed**: A historical deployment (`ai-multiagent-services.co-1770064500`) shows `BadRequest` status in deployment history
- **Impact**: None - the app is currently **Running** and healthy
- **Root Cause**: Transient deployment issue (resolved by subsequent successful deployment)

### Verification Steps

1. **Check Current Status**:

   ```bash
   az containerapp show \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --query "properties.{Status:runningStatus, Health:latestRevision.healthState}" \
     -o table
   ```

   Expected output:

   ```
   Status    Health
   --------  ------
   Running   Healthy
   ```

2. **Check Latest Revision**:

   ```bash
   az containerapp revision list \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --query "[0].{Name:name, Active:active, CreatedTime:properties.createdTime}" \
     -o table
   ```

3. **View Application Logs**:

   ```bash
   az containerapp logs show \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --tail 50
   ```

### Resolution

- ✅ Verified latest revision is healthy in Azure Portal
- ✅ No corrective action required
- ℹ️ Historical `BadRequest` deployment is **informational only** (superseded by successful deployment)

### If Future Deployments Fail

1. **Check Deployment Logs**:

   ```bash
   az containerapp revision list \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --query "[?properties.provisioningState=='Failed']" \
     -o table
   ```

2. **Common Failure Causes**:
   - Image pull failure (check ACR credentials)
   - Invalid environment variables
   - Resource quota exceeded
   - Network configuration issues

3. **Redeploy Action**:

   ```bash
   # Option 1: Redeploy via Azure Portal
   # Navigate to Container App > Deployments > Select failed deployment > Click "Redeploy"

   # Option 2: Trigger new deployment via CLI
   az containerapp update \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --image <your-image>:<tag>
   ```

4. **Check Container Logs**:

   ```bash
   az containerapp logs show \
     --name abaco-loans-app \
     --resource-group AI-MultiAgent-Ecosystem-RG \
     --follow
   ```

---

## Related Resources

- **Application Insights**: `abaco-loans-app-insights`
- **Log Analytics Workspace**: Linked for centralized logging
- **Container Registry**: Check image availability and credentials

## Monitoring

- **Health Probes**: Configured at `/health` endpoint
- **Metrics**: CPU, Memory, Request count tracked in Application Insights
- **Alerts**: Failure anomaly detection enabled

---

**Next Review**: 2026-03-04
