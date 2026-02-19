# Production Deployment Guide

## Overview

This guide covers production deployment of the Abaco Loans Analytics platform across multiple cloud providers and configurations.

**Target Environments**: Azure Functions, AWS Lambda, GCP Cloud Run, Railway, Docker-based hosting

## Prerequisites

- Python 3.9+ runtime
- Docker 20.10+ (for containerized deployments)
- PostgreSQL 13+ (Supabase recommended)
- Redis 6+ (optional, for rate limiting distributed mode)
- 2GB RAM minimum, 4GB recommended

## Environment Configuration

### Required Environment Variables

```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key  # Admin operations only

# LLM Providers (choose one or multiple)
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# Observability
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=...
OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector:4318

# Security
JWT_SECRET_KEY=your-256-bit-secret  # Generate with: openssl rand -hex 32
API_RATE_LIMIT_ENABLED=true
AUTH_RATE_LIMIT_PER_MINUTE=5
```

### Optional Configuration

```bash
# Feature Flags
ENABLE_MULTI_AGENT=true
ENABLE_REAL_TIME_KPIS=false  # Future feature

# Performance
MAX_WORKERS=4
BATCH_SIZE=1000
CACHE_TTL_SECONDS=300

# Compliance
PII_MASKING_ENABLED=true
AUDIT_LOG_RETENTION_DAYS=365
```

## Deployment Options

### Option 1: Azure Functions (Recommended for Azure customers)

**Setup**:

```bash
# Install Azure Functions Core Tools
brew install azure-functions-core-tools@4  # macOS
# OR: npm install -g azure-functions-core-tools@4

# Deploy
cd /path/to/abaco-loans-analytics
func azure functionapp publish your-function-app-name --python

# Configure app settings
az functionapp config appsettings set \
  --name your-function-app-name \
  --resource-group your-rg \
  --settings \
    SUPABASE_URL=$SUPABASE_URL \
    SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
    OPENAI_API_KEY=$OPENAI_API_KEY \
    JWT_SECRET_KEY=$JWT_SECRET_KEY
```

**host.json Configuration** (already in repo):

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensions": {
    "http": {
      "routePrefix": "api"
    }
  }
}
```

### Option 2: Docker Deployment

**Production Dockerfile** (already in repo as `Dockerfile.pipeline`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "scripts/data/run_data_pipeline.py", "--mode", "production"]
```

**Docker Compose Production** (create as `docker-compose.prod.yml`):

```yaml
version: "3.8"

services:
  pipeline:
    build:
      context: .
      dockerfile: Dockerfile.pipeline
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  redis-data:
  grafana-data:
```

**Deploy**:

```bash
# Build
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check health
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f pipeline
```

### Option 3: Railway (Fastest for small teams)

**Setup**:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Create new project
railway init

# Add environment variables
railway variables set SUPABASE_URL=$SUPABASE_URL
railway variables set SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
railway variables set OPENAI_API_KEY=$OPENAI_API_KEY
railway variables set JWT_SECRET_KEY=$JWT_SECRET_KEY

# Deploy
railway up
```

**railway.json** (create in repo root):

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "numReplicas": 1,
    "sleepApplication": false,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 4: AWS Lambda (via Serverless Framework)

**serverless.yml** (create in repo root):

```yaml
service: abaco-loans-analytics

provider:
  name: aws
  runtime: python3.11
  region: us-east-1
  environment:
    SUPABASE_URL: ${env:SUPABASE_URL}
    SUPABASE_ANON_KEY: ${env:SUPABASE_ANON_KEY}
    OPENAI_API_KEY: ${env:OPENAI_API_KEY}
    JWT_SECRET_KEY: ${env:JWT_SECRET_KEY}

functions:
  runPipeline:
    handler: src.pipeline.orchestrator.lambda_handler
    timeout: 300
    memorySize: 2048
    events:
      - schedule: cron(0 2 * * ? *) # Daily at 2am UTC

plugins:
  - serverless-python-requirements

custom:
  pythonRequirements:
    dockerizePip: true
```

**Deploy**:

```bash
npm install -g serverless
serverless deploy --stage production
```

### Option 5: GCP Cloud Run

**Setup**:

```bash
# Build container
gcloud builds submit --tag gcr.io/your-project/abaco-loans-analytics

# Deploy
gcloud run deploy abaco-loans-analytics \
  --image gcr.io/your-project/abaco-loans-analytics \
  --platform managed \
  --region us-central1 \
  --set-env-vars SUPABASE_URL=$SUPABASE_URL,SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY \
  --set-secrets OPENAI_API_KEY=openai-api-key:latest,JWT_SECRET_KEY=jwt-secret:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10
```

## Production Checklist

### Pre-Deployment

- [ ] **Environment variables**: All required vars set (see above)
- [ ] **Secrets management**: Use cloud provider's secret store (Azure Key Vault, AWS Secrets Manager, GCP Secret Manager)
- [ ] **Database migrations**: Run `python scripts/setup_supabase_tables.py` (if schema changes)
- [ ] **PII compliance**: Verify `PII_MASKING_ENABLED=true` in production
- [ ] **Rate limiting**: Configure `python/middleware/rate_limiter.py` thresholds based on expected load
- [ ] **Monitoring**: Application Insights / Prometheus configured
- [ ] **Backups**: Supabase daily backups enabled (automatic on Pro plan)

### Security Hardening

- [ ] **TLS/SSL**: HTTPS enforced (handled by cloud provider)
- [ ] **API authentication**: JWT validation in place (see [API_SECURITY_GUIDE.md](./API_SECURITY_GUIDE.md))
- [ ] **Network policies**: Firewall rules limiting ingress to HTTPS (443)
- [ ] **Secret rotation**: 90-day rotation policy for `JWT_SECRET_KEY`, API keys
- [ ] **Dependency scanning**: Run `make security-check` before deploy
- [ ] **RBAC**: Role-based access for Supabase tables (see `supabase/migrations/`)

### Post-Deployment

- [ ] **Health check**: `curl https://your-app.com/health` returns 200
- [ ] **Smoke test**: Run `python scripts/test_supabase_connection.py`
- [ ] **Log aggregation**: Verify logs appear in Application Insights / CloudWatch / Stackdriver
- [ ] **Alert rules**: Prometheus alerts firing on test violations
- [ ] **Dashboard**: Grafana dashboards loading data
- [ ] **Performance baseline**: Capture initial metrics (P50, P95, P99 latency)

## Monitoring & Observability

### Key Metrics to Track

**Pipeline Performance**:

- Execution time per phase (target: <60s total)
- Rows processed per second (target: >500 rows/s)
- Error rate (target: <0.1%)

**Multi-Agent System**:

- LLM API latency (P95 target: <5s)
- Cost per query (baseline: $0.02-0.05)
- Cache hit rate (target: >70%)

**Infrastructure**:

- CPU utilization (target: <70%)
- Memory usage (target: <1.5GB)
- Database connection pool saturation (target: <80%)

### Grafana Dashboard Setup

Import the pre-built dashboard:

```bash
# From repo root
cp grafana/dashboards/abaco-loans-analytics.json /path/to/grafana/provisioning/dashboards/
```

**Manual Import**:

1. Navigate to Grafana → Dashboards → Import
2. Upload `grafana/dashboards/abaco-loans-analytics.json`
3. Select Prometheus data source
4. Verify panels load data

### Alert Configuration

**Critical Alerts** (PagerDuty integration recommended):

- Pipeline execution failure
- Database connection loss
- PAR-30 > 15% (portfolio at risk threshold breach)
- Default rate > 4% (financial guardrail violation)

**Warning Alerts** (Slack/email):

- Pipeline duration > 90s
- LLM API errors > 5% over 5min
- Disk usage > 80%

See `config/alertmanager.yml.template` for full alert rules (copy or rename to `config/alertmanager.yml` for your environment).

## Disaster Recovery

### Backup Strategy

**Database** (Supabase):

- Automated daily backups (retention: 30 days on Pro plan)
- Point-in-time recovery (PITR) enabled
- Manual backup before major migrations: `pg_dump -h db.your-project.supabase.co -U postgres > backup.sql`

**Data Pipeline Outputs**:

- Versioned storage in `data/processed/<run_id>/`
- Parquet files retained for 90 days (configurable in `config/pipeline.yml`)
- Archive to S3/Azure Blob for long-term retention

**Configuration**:

- Git repository is source of truth
- Tag releases: `git tag -a v1.2.3 -m "Production release"`
- Immutable infrastructure: redeploy from tag, don't patch

### Rollback Procedure

**Azure Functions**:

```bash
# List deployments
az functionapp deployment list --name your-function-app-name --resource-group your-rg

# Rollback to specific deployment
az functionapp deployment source config-zip \
  --name your-function-app-name \
  --resource-group your-rg \
  --src previous-deployment.zip
```

**Docker**:

```bash
# Revert to previous image
docker-compose -f docker-compose.prod.yml down
docker pull your-registry/abaco-loans-analytics:v1.2.2  # Previous version
docker-compose -f docker-compose.prod.yml up -d
```

**Database Schema**:

```sql
-- Rollback last migration (example)
-- See supabase/migrations/ for actual migration files
ALTER TABLE fact_loans DROP COLUMN new_column;
```

## Performance Tuning

### Database Optimization

**Supabase Connection Pooling** (already implemented in `python/supabase_pool.py`):

- Min connections: 5
- Max connections: 20
- Connection timeout: 30s
- Health check interval: 60s

**Index Recommendations**:

```sql
-- Ensure these indexes exist (check supabase/migrations/)
CREATE INDEX idx_loans_status ON fact_loans(status);
CREATE INDEX idx_loans_disbursement_date ON fact_loans(disbursement_date);
CREATE INDEX idx_kpis_date ON kpi_timeseries_daily(date DESC);
```

### Pipeline Optimization

**Batch Processing** (see `src/pipeline/calculation.py`):

- Default batch size: 1000 rows
- Increase for larger datasets: `BATCH_SIZE=5000` env var
- Memory vs. speed tradeoff: Monitor with `docker stats`

**Parallel Processing**:

```python
# config/pipeline.yml
calculation:
  parallel: true
  max_workers: 4  # Adjust based on CPU cores
```

### Multi-Agent Optimization

**LLM Caching** (already implemented in `python/multi_agent/orchestrator.py`):

- Cache TTL: 300s (5 minutes)
- Cache hit rate: Monitor in Application Insights

**Prompt Engineering**:

- Shorter prompts = lower latency + cost
- Pre-compute KPI context where possible
- Use Claude 3.5 Haiku for simple queries (10× cheaper than GPT-4)

## Cost Optimization

### Infrastructure Costs (Estimated Monthly)

**Small Deployment** (100K loans, daily pipeline):

- Supabase Pro: $25/month (includes 8GB DB, 50GB bandwidth)
- Azure Functions: ~$10/month (Consumption plan, 100K executions)
- Application Insights: Free tier (5GB ingestion)
- **Total: ~$35/month**

**Medium Deployment** (1M loans, daily pipeline, 1K agent queries):

- Supabase Pro: $25/month
- Azure Functions: ~$50/month
- OpenAI API (GPT-4): ~$100/month (1K queries × $0.10 avg)
- Application Insights: ~$20/month (data overage)
- **Total: ~$195/month**

### Cost Reduction Tips

1. **LLM Usage**:
   - Use cheaper models for simple queries (GPT-3.5, Claude Haiku)
   - Implement aggressive caching (already done)
   - Batch multi-agent scenarios where possible

2. **Database**:
   - Archive old data to cold storage (S3 Glacier)
   - Optimize queries (use `EXPLAIN ANALYZE` in Supabase SQL Editor)
   - Consider read replicas for analytics (Supabase Enterprise)

3. **Compute**:
   - Use spot instances (AWS Lambda reserved capacity)
   - Scale to zero when idle (Cloud Run default behavior)
   - Right-size memory allocation (start with 1GB, monitor)

## Troubleshooting

### Common Issues

**Issue**: Pipeline execution timeout

- **Solution**: Increase timeout in cloud provider settings (Azure Functions: 300s max in Consumption plan, unlimited in Premium)
- **Verification**: Check `FUNCTIONS_WORKER_PROCESS_COUNT` env var (default: 1, increase for parallelism)

**Issue**: "Invalid URL" database error

- **Solution**: Verify `SUPABASE_URL` format: `https://abc123.supabase.co` (no trailing slash)
- **Verification**: `curl $SUPABASE_URL/rest/v1/` should return 200

**Issue**: High LLM API costs

- **Solution**: Review `python/multi_agent/tracing.py` cost metrics in Application Insights
- **Action**: Switch expensive agents to cheaper models in `python/multi_agent/orchestrator.py`

**Issue**: Rate limit 429 errors

- **Solution**: Adjust rate limiter thresholds in `python/middleware/rate_limiter.py`
- **Defaults**: API: 100 req/10s, Auth: 5 req/60s, Dashboard: 1000 tokens

### Debug Mode

Enable verbose logging:

```bash
# Local testing
python scripts/data/run_data_pipeline.py --input data/raw/sample_loans_800.csv --verbose

# Production (environment variable)
export LOG_LEVEL=DEBUG
```

View structured logs:

```bash
# Azure Functions
func azure functionapp logstream your-function-app-name

# Docker
docker-compose -f docker-compose.prod.yml logs -f --tail=100 pipeline

# Railway
railway logs
```

## Support & Escalation

**Internal Resources**:

- Development guide: [DEVELOPMENT.md](./DEVELOPMENT.md)
- API security: [API_SECURITY_GUIDE.md](./API_SECURITY_GUIDE.md)
- Data seeding: [DATA_SEEDING_GUIDE.md](./DATA_SEEDING_GUIDE.md)
- Runbooks: `runbooks/` directory

**External Support**:

- Supabase: support@supabase.com (Pro plan includes email support)
- Azure: Azure Portal → Help + Support → New support request
- OpenAI: help.openai.com (API issues)

**On-Call Escalation** (define your process):

1. Check Grafana dashboards for anomalies
2. Review recent deployments (Git commits, Azure deployment history)
3. Query Application Insights for error patterns
4. Escalate to CTO if financial guardrail violated (default rate >4%, PAR-30 >15%)

---

**Last Updated**: 2026-02-02  
**Maintained By**: Platform Engineering Team  
**Review Frequency**: Quarterly or after major version releases
