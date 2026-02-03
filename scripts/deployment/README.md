# Deployment Scripts

Scripts for deploying and managing production environments.

## Scripts

**Deployment:**
- `deploy_to_azure.sh` - Deploy application to Azure
- `deploy_stack.sh` - Deploy complete infrastructure stack
- `rollback_deployment.sh` - Rollback to previous deployment

**Monitoring:**
- `monitor_deployment.sh` - Monitor deployment progress
- `production_health_check.sh` - Check production system health
- `health_check.py` - Comprehensive health check utility

## Usage Examples

```bash
# Deploy to Azure
./scripts/deployment/deploy_to_azure.sh

# Monitor deployment
./scripts/deployment/monitor_deployment.sh

# Health check
python scripts/deployment/health_check.py

# Rollback if needed
./scripts/deployment/rollback_deployment.sh
```

## Prerequisites

- Azure CLI configured
- Required environment variables set (see .env.example)
- Appropriate Azure permissions
