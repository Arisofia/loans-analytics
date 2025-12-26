# DO NOT USE IN PRODUCTION
# Legacy operations snapshot. Superseded by docs/OPERATIONS.md.

# Abaco Loans Analytics - Operations Runbook

## Table of Contents
1. [Deployment](#deployment)
2. [Monitoring](#monitoring)
3. [Incident Response](#incident-response)
4. [Maintenance](#maintenance)
5. [Troubleshooting](#troubleshooting)

## Deployment

### Prerequisites
- Python 3.10+
- PostgreSQL or Supabase account
- Azure storage account (optional, for cloud uploads)
- Docker (for containerized deployment)

### Local Development Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd abaco-loans-analytics

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env.local
# Edit .env.local with your credentials

# 5. Run tests
pytest tests/ -v --cov=python --cov-report=html

# 6. Run pipeline
python -m python.pipeline.orchestrator --input data/sample.csv
```

### Docker Deployment

```bash
# Build image
docker build -f Dockerfile.pipeline -t abaco-pipeline:latest .

# Run container
docker run \
  -e AZURE_STORAGE_CONNECTION_STRING="..." \
  -e META_SYSTEM_USER_TOKEN="..." \
  -v $(pwd)/data:/app/data \
  abaco-pipeline:latest

# Push to registry
docker tag abaco-pipeline:latest acr.azurecr.io/abaco-pipeline:latest
docker push acr.azurecr.io/abaco-pipeline:latest
```

### Production Deployment (Azure Container Instances)

```bash
# Deploy to ACI
az container create \
  --resource-group abaco-prod \
  --name abaco-pipeline \
  --image acr.azurecr.io/abaco-pipeline:latest \
  --environment-variables \
    AZURE_STORAGE_CONNECTION_STRING="..." \
    META_SYSTEM_USER_TOKEN="..." \
  --cpu 2 \
  --memory 4
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: abaco-pipeline
spec:
  replicas: 1
  selector:
    matchLabels:
      app: abaco-pipeline
  template:
    metadata:
      labels:
        app: abaco-pipeline
    spec:
      containers:
      - name: pipeline
        image: acr.azurecr.io/abaco-pipeline:latest
        env:
        - name: AZURE_STORAGE_CONNECTION_STRING
          valueFrom:
            secretKeyRef:
              name: abaco-secrets
              key: azure-conn-str
        - name: META_SYSTEM_USER_TOKEN
          valueFrom:
            secretKeyRef:
              name: abaco-secrets
              key: cascade-token
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 60
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/pipeline.yml
name: Pipeline
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=python
      - uses: codecov/codecov-action@v3

  pipeline:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: python -m python.pipeline.orchestrator --input data/sample.csv
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: pipeline-results
          path: data/metrics/
```

## Monitoring

### Health Checks

#### Pipeline Health Endpoint
```bash
# Check if pipeline is operational
curl http://localhost:8000/health

# Response
{
  "status": "healthy",
  "last_run": "2025-12-26T00:00:00Z",
  "next_run": "2025-12-26T02:00:00Z",
  "metrics_computed": 4,
  "last_error": null
}
```

#### KPI Validation
```bash
# Validate KPIs are within expected ranges
python -c "
from python.pipeline.orchestrator import UnifiedPipeline
pipeline = UnifiedPipeline()
result = pipeline.execute(Path('data/sample.csv'))
# Verify thresholds
for kpi, data in result['phases']['calculation']['metrics'].items():
    print(f'{kpi}: {data[\"value\"]}')
"
```

### Metrics to Monitor

#### Phase Metrics
- **Ingestion**:
  - Rows loaded
  - Validation errors
  - Processing time
  - File size
  
- **Transformation**:
  - Rows processed
  - Null count
  - PII columns masked
  - Processing time
  
- **Calculation**:
  - KPIs computed
  - Calculation time
  - Audit entries
  - Errors (by metric)
  
- **Output**:
  - Files persisted
  - Azure upload success
  - Database writes
  - Manifest generation time

#### KPI Metrics
- **PAR30**: Warning > 5%, Critical > 8%
- **PAR90**: Warning > 3%, Critical > 5%
- **CollectionRate**: Warning < 1.5%, Critical < 1%
- **PortfolioHealth**: Warning < 5, Critical < 3

### Alerting Rules

```yaml
# prometheus-rules.yml
groups:
  - name: abaco_pipeline
    rules:
      - alert: PipelineFailure
        expr: pipeline_status == "failed"
        for: 5m
        annotations:
          summary: "Pipeline failed: {{ $value }}"
      
      - alert: PAR90Critical
        expr: kpi_par90 > 5.0
        for: 1h
        annotations:
          summary: "PAR90 critical: {{ $value }}%"
      
      - alert: ProcessingDelayed
        expr: (time() - pipeline_last_run) > 3600
        annotations:
          summary: "Pipeline hasn't run in 1+ hours"
```

### Dashboards

#### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Abaco Pipeline",
    "panels": [
      {
        "title": "PAR Metrics",
        "targets": [
          {"expr": "kpi_par30"},
          {"expr": "kpi_par90"}
        ]
      },
      {
        "title": "Pipeline Health",
        "targets": [
          {"expr": "pipeline_execution_time_seconds"},
          {"expr": "pipeline_status"}
        ]
      }
    ]
  }
}
```

## Incident Response

### Incident Severity Levels

| Level | Impact | Response Time | Example |
|-------|--------|----------------|---------|
| P1 | Critical | 15 min | Pipeline down, no metrics |
| P2 | High | 1 hour | KPI calculation failed |
| P3 | Medium | 4 hours | Data quality issue |
| P4 | Low | 24 hours | Documentation updates |

### P1: Pipeline Down

1. **Verify Status** (1 min)
   ```bash
   # Check pipeline health
   curl http://localhost:8000/health
   
   # Check logs
   tail -f logs/pipeline.log
   ```

2. **Identify Root Cause** (5 min)
   - Check Azure credentials
   - Verify Cascade connection
   - Review recent code changes
   - Check disk space

3. **Mitigation** (10 min)
   - Restart service: `systemctl restart abaco-pipeline`
   - Or restart container: `docker restart abaco-pipeline`
   - Check if manual intervention needed

4. **Restore** (15 min)
   - Verify pipeline runs successfully
   - Validate output
   - Notify stakeholders

### P2: KPI Calculation Failed

1. **Investigation**
   ```bash
   # Run pipeline with debug logging
   python -m python.pipeline.orchestrator \
     --log-level DEBUG \
     --input data/latest.csv
   ```

2. **Validation**
   ```bash
   # Check data quality
   python -c "
   import pandas as pd
   df = pd.read_csv('data/latest.csv')
   print(df.info())
   print(df.describe())
   "
   ```

3. **Remediation**
   - Update pipeline config if needed
   - Rollback to previous version if regression
   - Re-run pipeline

### P3: Data Quality Issue

1. **Analysis**
   ```bash
   # Check for anomalies
   python -c "
   from python.kpi_engine_v2 import KPIEngineV2
   import pandas as pd
   
   df = pd.read_csv('data/latest.csv')
   engine = KPIEngineV2(df)
   metrics = engine.calculate_all()
   
   # Review thresholds
   for kpi, data in metrics.items():
       if data['value'] > threshold:
           print(f'Alert: {kpi} = {data[\"value\"]}')
   "
   ```

2. **Notification**
   - Slack message to #analytics-alerts
   - PagerDuty incident (if severe)
   - Email stakeholders

## Maintenance

### Daily Tasks
- [ ] Check pipeline health dashboard
- [ ] Review error logs
- [ ] Verify KPI calculations are within expected ranges
- [ ] Confirm Azure backups completed

### Weekly Tasks
- [ ] Run full test suite
- [ ] Review pipeline performance metrics
- [ ] Update documentation
- [ ] Check for dependency updates

### Monthly Tasks
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Disaster recovery drill
- [ ] Stakeholder reporting

### Quarterly Tasks
- [ ] Full system audit
- [ ] Capacity planning
- [ ] Technology evaluation
- [ ] Architecture review

## Troubleshooting

### Common Issues

#### 1. Ingestion Fails: "File not found"
```
Error: Input file not found: data/sample.csv

Resolution:
- Verify file exists: ls -la data/
- Check file permissions: chmod 644 data/*.csv
- Verify path is correct in config
```

#### 2. Schema Validation Error
```
Error: Schema validation failed for 5 rows

Resolution:
- Check data types: python -c "import pandas as pd; df = pd.read_csv('data/sample.csv'); df.info()"
- Review required columns in config/pipeline.yml
- Validate against schema: python -c "from python.validation import validate_dataframe; validate_dataframe(df)"
```

#### 3. KPI Calculation Returns 0
```
Error: All KPIs returning 0 (possibly due to zero total_receivable)

Resolution:
- Check data: df['total_receivable_usd'].describe()
- Verify column names match config
- Check for data type issues
```

#### 4. Azure Upload Fails
```
Error: Azure upload failed: ConnectionError

Resolution:
- Verify connection string: echo $AZURE_STORAGE_CONNECTION_STRING
- Check container exists: az storage container list --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
- Verify network connectivity
```

#### 5. Memory Issues
```
Error: MemoryError: Unable to allocate 4GB

Resolution:
- Reduce batch size in config/pipeline.yml
- Enable chunking for large files
- Increase available memory: docker run --memory 8gb ...
```

### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python -m python.pipeline.orchestrator \
  --input data/sample.csv \
  --config config/pipeline.yml \
  --output data/debug_output/
```

### Performance Tuning

```bash
# Profile pipeline execution
python -m cProfile -s cumulative -m python.pipeline.orchestrator \
  --input data/sample.csv > profile.txt
cat profile.txt | head -30
```

## Rollback Procedures

### Rollback to Previous Version
```bash
# 1. Stop current pipeline
systemctl stop abaco-pipeline

# 2. Checkout previous version
git checkout <previous-commit>

# 3. Reinstall dependencies
pip install -r requirements.txt

# 4. Restart pipeline
systemctl start abaco-pipeline

# 5. Verify health
curl http://localhost:8000/health
```

### Data Rollback
```bash
# Restore from backup
aws s3 cp s3://abaco-backups/pipeline-results-2025-12-25.tar.gz .
tar -xzf pipeline-results-2025-12-25.tar.gz -C data/
```

## Support

For issues or questions:
- **Slack**: #analytics-support
- **Email**: analytics-team@abaco.io
- **On-Call**: See PagerDuty rotation
- **Documentation**: See ARCHITECTURE_UNIFIED.md
