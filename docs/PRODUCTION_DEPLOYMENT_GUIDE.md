# Production Deployment Guide

**Status**: Production-Ready  
**Last Updated**: February 2, 2026  
**Target Audience**: DevOps Engineers, Platform Engineers, SREs

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Platform-Specific Deployment](#platform-specific-deployment)
4. [Security Configuration](#security-configuration)
5. [Environment Variables](#environment-variables)
6. [Data Seeding](#data-seeding)
7. [Health Checks & Monitoring](#health-checks--monitoring)
8. [Rollback Procedures](#rollback-procedures)
9. [Production Checklist](#production-checklist)

---

## Overview

This guide covers production deployment of the Abaco Loans Analytics platform across multiple cloud providers and deployment platforms. The application consists of:

- **ETL Pipeline**: Python 3.11+ data processing pipeline
- **Multi-Agent AI System**: LLM-powered analytics with 9 specialized agents
- **Dashboard**: Streamlit web application for data visualization
- **Database**: PostgreSQL via Supabase
- **Observability**: Prometheus + Grafana + Azure Application Insights

### Architecture

```
┌─────────────────┐
│   Load Balancer │
└────────┬────────┘
         │
    ┌────┴────┐
    │  App    │ (Streamlit Dashboard)
    │ Service │ Port: 8501
    └────┬────┘
         │
    ┌────┴────────┐
    │  Pipeline   │ (ETL Worker)
    │   Worker    │ Scheduled/On-Demand
    └────┬────────┘
         │
    ┌────┴─────────┐
    │  Supabase    │ (PostgreSQL + Auth)
    │   Database   │
    └──────────────┘
```

---

## Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 10GB minimum for logs and data storage
- **Network**: Outbound HTTPS access for LLM APIs and Supabase

### Required Accounts & Credentials

- [ ] Supabase project with connection credentials
- [ ] LLM API keys (OpenAI, Anthropic, or Gemini)
- [ ] Cloud platform account (Azure/AWS/GCP)
- [ ] GitHub account for CI/CD integration
- [ ] Container registry access (GHCR, Docker Hub, or cloud-specific)

### Pre-Deployment Validation

```bash
# Validate repository structure
python scripts/validate_structure.py

# Run tests locally
pytest tests/ -v -m "not integration"

# Build Docker image
docker build -t abaco-loans-analytics:test .

# Test container locally
docker run -p 8501:8501 --env-file .env.local abaco-loans-analytics:test
```

---

## Platform-Specific Deployment

### Azure App Service (Primary Platform)

**Supported Services:**
- Azure App Service (Linux container)
- Azure SQL Database (PostgreSQL-compatible)
- Azure Blob Storage
- Azure Application Insights

#### Automated Deployment

```bash
# 1. Configure Azure CLI
az login
az account set --subscription "Your Subscription Name"

# 2. Deploy infrastructure via Bicep
cd infra/azure
az deployment group create \
  --resource-group abaco-prod \
  --template-file main.bicep \
  --parameters main.bicepparam

# 3. Deploy application
cd ../..
bash scripts/deploy_to_azure.sh --env production
```

#### Manual Azure Portal Deployment

1. **Create App Service**:
   - Runtime: Docker Container
   - OS: Linux
   - Region: Select closest to users
   - Pricing: P1V2 or higher

2. **Configure Container**:
   - Registry: GitHub Container Registry (ghcr.io)
   - Image: `ghcr.io/arisofia/abaco-loans-analytics:latest`
   - Port: 8501

3. **Set Environment Variables** (see [Environment Variables](#environment-variables))

4. **Enable Application Insights**:
   - Create new AI resource
   - Copy instrumentation key
   - Add to app settings

#### Azure Infrastructure as Code (Bicep)

See `infra/azure/` for complete templates:
- `main.bicep`: Root template with all resources
- `appService.bicep`: Web app configuration
- `database.bicep`: PostgreSQL database
- `monitoring.bicep`: Application Insights + Log Analytics

---

### AWS Deployment

#### Option 1: AWS Elastic Beanstalk

**Dockerfile Deployment**:

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize application
eb init -p docker abaco-loans-analytics --region us-east-1

# 3. Create environment
eb create abaco-prod \
  --instance-type t3.medium \
  --envvars SUPABASE_URL=$SUPABASE_URL,SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY

# 4. Deploy
eb deploy
```

**Configuration File** (`.ebextensions/app.config`):

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    PYTHONUNBUFFERED: "1"
    PIPELINE_ENV: "production"
  aws:elasticbeanstalk:container:python:
    WSGIPath: streamlit_app.py
```

#### Option 2: AWS ECS Fargate

**Task Definition** (`ecs-task-definition.json`):

```json
{
  "family": "abaco-loans-analytics",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "app",
      "image": "ghcr.io/arisofia/abaco-loans-analytics:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PIPELINE_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:supabase-url"
        },
        {
          "name": "SUPABASE_ANON_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:supabase-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/abaco-loans-analytics",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**Deployment Commands**:

```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create service
aws ecs create-service \
  --cluster abaco-cluster \
  --service-name abaco-service \
  --task-definition abaco-loans-analytics \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### Google Cloud Platform (GCP)

#### Cloud Run Deployment

```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/abaco-loans-analytics

# 2. Deploy to Cloud Run
gcloud run deploy abaco-loans-analytics \
  --image gcr.io/PROJECT_ID/abaco-loans-analytics \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --port 8501 \
  --set-env-vars PIPELINE_ENV=production \
  --set-secrets SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-key:latest \
  --allow-unauthenticated

# 3. Verify deployment
gcloud run services describe abaco-loans-analytics --region us-central1
```

**Cloud Run Service YAML** (`cloud-run-service.yaml`):

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: abaco-loans-analytics
spec:
  template:
    spec:
      containers:
        - image: gcr.io/PROJECT_ID/abaco-loans-analytics
          ports:
            - containerPort: 8501
          env:
            - name: PIPELINE_ENV
              value: "production"
          resources:
            limits:
              cpu: "2"
              memory: "2Gi"
```

---

### Vercel (Frontend Alternative)

**Note**: Vercel is best for Next.js frontends. For this Python/Streamlit app, use Cloud Run or Azure.

If you have a Next.js frontend in `apps/web/`:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd apps/web
vercel --prod
```

**Environment Variables** (via Vercel dashboard or CLI):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

### Railway

**One-Click Deployment**:

1. Connect GitHub repository to Railway
2. Configure service:
   - Root Directory: `/`
   - Build Command: (Docker auto-detected)
   - Start Command: (From Dockerfile ENTRYPOINT)
3. Add environment variables
4. Deploy

**Railway CLI**:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and init
railway login
railway init

# Add environment variables
railway variables set SUPABASE_URL=https://...
railway variables set SUPABASE_ANON_KEY=eyJ...

# Deploy
railway up
```

---

## Security Configuration

### Rate Limiting

**Implementation Option 1: Nginx Reverse Proxy** (Recommended)

```nginx
# /etc/nginx/conf.d/abaco.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=dashboard:10m rate=100r/s;

server {
    listen 80;
    server_name your-domain.com;

    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        limit_req zone=dashboard burst=200 nodelay;
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Implementation Option 2: Application-Level (Python)**

Create `python/middleware/rate_limiter.py`:

```python
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Callable
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed under rate limit."""
        now = datetime.now()
        cutoff = now - self.window
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False
        
        # Record request
        self.requests[identifier].append(now)
        return True

# Global rate limiter instances
api_limiter = RateLimiter(max_requests=10, window_seconds=1)  # 10/sec
dashboard_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100/min

def rate_limit(limiter: RateLimiter):
    """Decorator for rate limiting functions."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get identifier (IP or user ID)
            identifier = kwargs.get('user_id') or 'anonymous'
            
            if not limiter.is_allowed(identifier):
                raise Exception("Rate limit exceeded. Please try again later.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example:
# @rate_limit(api_limiter)
# def process_request(user_id: str):
#     pass
```

### Security Headers

**Add to Streamlit config** (`~/.streamlit/config.toml`):

```toml
[server]
enableCORS = false
enableXsrfProtection = true

[browser]
serverAddress = "your-domain.com"
serverPort = 443
```

**Nginx Security Headers**:

```nginx
# Add to server block
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# HTTPS only
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# CSP (adjust for your needs)
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https://*.supabase.co;" always;
```

### CORS Configuration

**Supabase Edge Functions** (`supabase/functions/_shared/cors.ts`):

```typescript
export const corsHeaders = {
  'Access-Control-Allow-Origin': process.env.ALLOWED_ORIGIN || '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  'Access-Control-Max-Age': '86400',
};

export function handleCors(req: Request): Response | null {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: corsHeaders,
    });
  }
  return null;
}
```

**Production Recommendation**: Set `ALLOWED_ORIGIN` to your specific domain, not `*`.

### Input Validation

Already implemented in `python/validation.py` and `python/apps/analytics/api/main.py`.

**Best Practices**:
- ✅ Validate all user inputs (type, range, format)
- ✅ Prevent path traversal attacks
- ✅ Sanitize log outputs (no injection)
- ✅ Use Pydantic models for schema validation
- ⚠️ Never trust client data without validation

### Secrets Management

**Azure Key Vault** (Recommended for Azure):

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
vault_url = "https://your-vault.vault.azure.net"
client = SecretClient(vault_url=vault_url, credential=credential)

# Retrieve secret
supabase_key = client.get_secret("supabase-key").value
```

**AWS Secrets Manager**:

```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
response = client.get_secret_value(SecretId='prod/supabase/key')
supabase_key = response['SecretString']
```

**Environment Variables** (Development):
- Use `.env.local` (gitignored)
- Never commit secrets to repository
- Use GitHub Secrets for CI/CD

---

## Environment Variables

### Required Variables

```bash
# Database (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Application (REQUIRED)
PIPELINE_ENV=production  # or development, staging
NODE_ENV=production

# LLM Providers (At least one REQUIRED for multi-agent system)
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...
# OR
GEMINI_API_KEY=...
```

### Optional Variables

```bash
# Service-specific credentials
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # For admin operations
SUPABASE_JWT_SECRET=...           # For token verification

# Observability
ENABLE_OTEL=true
OTEL_ENDPOINT=http://otel-collector:4318
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
LOG_LEVEL=INFO

# Performance
LLM_TIMEOUT=60
LLM_MAX_RETRIES=3
METRICS_PORT=8000
```

### Platform-Specific Configuration

**Azure App Service**:
```bash
# Set via Azure Portal or CLI
az webapp config appsettings set \
  --resource-group abaco-prod \
  --name abaco-app \
  --settings \
    SUPABASE_URL="$SUPABASE_URL" \
    SUPABASE_ANON_KEY="$SUPABASE_ANON_KEY" \
    PIPELINE_ENV=production
```

**AWS ECS**:
- Use Secrets Manager + Task Definition secrets section

**GCP Cloud Run**:
```bash
gcloud run services update abaco-loans-analytics \
  --set-env-vars PIPELINE_ENV=production \
  --set-secrets SUPABASE_URL=supabase-url:latest
```

**Railway**:
```bash
railway variables set SUPABASE_URL=https://...
railway variables set PIPELINE_ENV=production
```

---

## Data Seeding

### Production Data Setup

**1. Create Database Tables**:

```bash
# Run Supabase migration
python scripts/setup_supabase_tables.py --env production
```

**2. Load Sample KPIs** (for testing):

```bash
python scripts/load_sample_kpis_supabase.py \
  --supabase-url $SUPABASE_URL \
  --supabase-key $SUPABASE_ANON_KEY \
  --start-date 2025-01-01 \
  --end-date 2026-01-31
```

**3. Import Real Loan Data**:

```bash
# Via CSV import
python scripts/run_data_pipeline.py \
  --input /path/to/loans.csv \
  --mode full \
  --env production

# Via Supabase direct insert (for large datasets)
# See python/apps/analytics/api/main.py for API endpoints
```

### Data Seeding Best Practices

**Security**:
- ✅ Use service role key for seeding (not anon key)
- ✅ Mask PII during seeding (automatic via `src/compliance.py`)
- ✅ Validate data before insert (use `python/validation.py`)
- ⚠️ Never seed production with unvalidated external data

**Performance**:
- Use batch inserts (1000 rows at a time)
- Enable connection pooling
- Run during low-traffic hours

**Example Seeding Script**:

```python
from python.supabase_pool import get_supabase_client
import pandas as pd

async def seed_production_data():
    client = get_supabase_client()
    
    # Read data
    df = pd.read_csv('production_loans.csv')
    
    # Validate
    from python.validation import validate_loan_data
    errors = validate_loan_data(df)
    if errors:
        raise ValueError(f"Validation failed: {errors}")
    
    # Batch insert
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].to_dict('records')
        response = client.table('fact_loans').insert(batch).execute()
        print(f"Inserted batch {i//batch_size + 1}")

# Run: python -c "import asyncio; asyncio.run(seed_production_data())"
```

---

## Health Checks & Monitoring

### Application Health Endpoints

**Streamlit Health Check** (built-in):
```
GET http://your-domain:8501/_stcore/health
```

**Custom Health Check Script**:

```bash
# scripts/production_health_check.sh
python scripts/health_check.py --url https://your-domain.com
```

### Monitoring Setup

#### Azure Application Insights

```python
# Already configured in src/pipeline/orchestrator.py
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation as aggregation_module

connection_string = os.getenv('APPLICATIONINSIGHTS_CONNECTION_STRING')
if connection_string:
    exporter = metrics_exporter.new_metrics_exporter(
        connection_string=connection_string
    )
```

#### Prometheus + Grafana

```bash
# Start monitoring stack
make monitoring-start

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3001 (admin/admin)
```

**Custom Metrics** (add to your code):

```python
from prometheus_client import Counter, Histogram
import time

# Define metrics
pipeline_runs = Counter('pipeline_runs_total', 'Total pipeline runs')
pipeline_duration = Histogram('pipeline_duration_seconds', 'Pipeline execution time')

# Record metrics
@pipeline_duration.time()
def run_pipeline():
    pipeline_runs.inc()
    # ... pipeline logic ...
```

### Alerting

**Grafana Alerts** (see `grafana/provisioning/alerting/rules.yml`):
- Pipeline failure rate > 5%
- Response time > 5 seconds
- Error rate > 1%

**Azure Monitor Alerts**:

```bash
az monitor metrics alert create \
  --name "High Error Rate" \
  --resource-group abaco-prod \
  --scopes /subscriptions/.../resourceGroups/abaco-prod/providers/Microsoft.Web/sites/abaco-app \
  --condition "avg requests/failed > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

---

## Rollback Procedures

### Automated Rollback

```bash
# Rollback to previous commit
bash scripts/rollback_deployment.sh --commits 1

# Rollback to specific commit
bash scripts/rollback_deployment.sh --to abc123def
```

### Manual Rollback

#### Azure App Service

```bash
# Via Azure CLI
az webapp deployment slot swap \
  --resource-group abaco-prod \
  --name abaco-app \
  --slot staging \
  --action swap

# Or restore previous deployment
az webapp deployment source show \
  --resource-group abaco-prod \
  --name abaco-app
```

#### Docker/Container Platforms

```bash
# Pull previous image
docker pull ghcr.io/arisofia/abaco-loans-analytics:previous-tag

# Restart with old image
docker service update \
  --image ghcr.io/arisofia/abaco-loans-analytics:previous-tag \
  abaco-service
```

#### Database Rollback

⚠️ **CAUTION**: Database rollbacks can cause data loss.

```bash
# Restore from backup (Supabase)
# Via Supabase dashboard: Settings → Database → Restore from backup

# Or manual restore
psql $DATABASE_URL < backup_$(date -d yesterday +%Y%m%d).sql
```

---

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] Code quality checks passed (`make lint`)
- [ ] Security scan completed (`make security-scan`)
- [ ] Environment variables configured
- [ ] Secrets stored in secure vault (not .env files)
- [ ] Database migrations applied
- [ ] Backup taken
- [ ] Rollback plan documented
- [ ] Monitoring dashboards configured
- [ ] Alert rules enabled
- [ ] Rate limiting configured
- [ ] HTTPS/SSL certificates valid
- [ ] CORS headers restricted to production domain
- [ ] Security headers enabled

### Deployment

- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Verify health endpoints responding
- [ ] Check logs for errors
- [ ] Monitor resource usage (CPU, memory)
- [ ] Test critical user flows
- [ ] Deploy to production
- [ ] Verify production health endpoint
- [ ] Monitor error rates for 1 hour
- [ ] Document deployment timestamp and version

### Post-Deployment

- [ ] Verify all services operational
- [ ] Check database connectivity
- [ ] Test LLM API integrations
- [ ] Validate data pipeline runs
- [ ] Review logs for warnings/errors
- [ ] Monitor performance metrics
- [ ] Update status page (if applicable)
- [ ] Notify stakeholders of completion
- [ ] Schedule post-deployment review

### Monitoring (First 24 Hours)

- [ ] Error rate < 1%
- [ ] Average response time < 2 seconds
- [ ] No database connection errors
- [ ] Pipeline success rate > 95%
- [ ] Memory usage stable
- [ ] CPU usage < 70%
- [ ] No security alerts

---

## Troubleshooting

### Common Issues

**1. Application fails to start**:
```bash
# Check logs
docker logs <container-id>

# Verify environment variables
env | grep SUPABASE

# Test database connection
python scripts/test_supabase_connection.py
```

**2. High memory usage**:
```bash
# Check for memory leaks
python scripts/health_check.py --memory-profile

# Restart service
docker restart <container-id>
```

**3. Pipeline failures**:
```bash
# View pipeline logs
ls -la logs/runs/
cat logs/runs/latest/pipeline_results.json

# Run in dry-run mode
python scripts/run_data_pipeline.py --mode dry-run
```

### Getting Help

- **Documentation**: [docs/README.md](../README.md)
- **Runbooks**: [docs/operations/](../operations/)
- **Support**: File an issue on GitHub

---

## Additional Resources

- [CTO Audit Report](CTO_AUDIT_REPORT.md) - Production readiness assessment
- [Operations Master](REPO_OPERATIONS_MASTER.md) - Complete operations guide
- [Setup Guide](SETUP_GUIDE_CONSOLIDATED.md) - Initial setup instructions
- [Security Guide](SECURITY.md) - Security best practices
- [Monitoring Guide](SUPABASE_METRICS_INTEGRATION.md) - Observability setup

---

**Document Version**: 1.0  
**Maintained By**: Platform Engineering Team  
**Review Cycle**: Quarterly
