# Operations Runbook

**Version**: 2.0  
**Date**: 2025-12-26  
**Audience**: DevOps, SRE, Operations Teams

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Deployment](#deployment)
3. [Monitoring & Alerts](#monitoring--alerts)
4. [Troubleshooting](#troubleshooting)
5. [Incident Response](#incident-response)
6. [Maintenance](#maintenance)
7. [Rollback Procedures](#rollback-procedures)
8. [On-Call Runbook](#on-call-runbook)

---

## Quick Start

### First-Time Setup

```bash
# 1. Clone repository and navigate to project
git clone <repo-url>
cd abaco-loans-analytics

# 2. Install production dependencies
pip install -r requirements.txt

# 3. Set up production environment
export PIPELINE_ENV=production
export CASCADE_SESSION_COOKIE="<your-cascade-token>"
export SLACK_WEBHOOK_TOKEN="<your-slack-webhook>"

# 4. Verify configuration
python -c "from python.pipeline.orchestrator import PipelineConfig; c = PipelineConfig(); print(f'Environment: {c.environment}')"

# 5. Run initial test
python scripts/run_data_pipeline.py --input data/raw/cascade/loan_tape.csv
```

### Daily Operations

```bash
# Set environment (production is default)
export PIPELINE_ENV=production

# Run daily pipeline
python scripts/run_data_pipeline.py

# Check logs
tail -f logs/runs/*/pipeline_*.log

# Monitor Slack for alerts
# Check #risk-monitoring and #fintech-reports channels
```

---

## Deployment

### Pre-Deployment Checklist

- [ ] All tests passing: `make test` (100% pass rate)
- [ ] Code quality clean: `make lint` (0 errors)
- [ ] Type checking clean: `make type-check` (0 errors)
- [ ] Coverage ≥ 85%: `make test-cov`
- [ ] Staging validation complete (24+ hours)
- [ ] Rollback procedure documented and tested
- [ ] Monitoring alerts configured
- [ ] Team notified of deployment window

### Staging Deployment (Pre-Production Testing)

```bash
# 1. Deploy to staging
PIPELINE_ENV=staging python scripts/run_data_pipeline.py --input data/raw/test/loan_tape.csv

# 2. Run shadow mode (alongside production)
# Pipeline runs with PIPELINE_ENV=staging for 24 hours
# Monitor outputs in logs/runs/ directory

# 3. Validate results
# Compare staging outputs with production outputs
# Check for:
#   - Data consistency
#   - Calculation accuracy
#   - No new errors or warnings
#   - Performance metrics unchanged

# 4. Review logs
tail -100 logs/runs/staging_*/pipeline_summary.json
```

### Production Deployment (5-Minute Cutover)

```bash
# 1. Notify team
echo "Starting production deployment" | slack
# Message sent to #executive-briefing

# 2. Switch environment and run ONE pipeline execution
export PIPELINE_ENV=production
python scripts/run_data_pipeline.py --input data/raw/cascade/loan_tape.csv

# 3. Verify immediate results
ls -la logs/runs/latest/
head logs/runs/latest/pipeline_summary.json

# 4. Hour 1 validation
# Check all 5 validation criteria:
# - All 29 tests passing
# - Pipeline latency < 10 minutes
# - All KPIs calculated
# - Outputs persisted to Supabase
# - No error logs in logs/runs/latest/*.log

# 5. Continue monitoring (24 hours)
# Alert thresholds: PAR_90 > 5%, Collection Rate < 1%, etc.
```

### Deployment Rollback (If Needed)

```bash
# Rollback is simple: restore previous version
git checkout <previous-commit>
pip install -r requirements.txt

# Run with previous version
export PIPELINE_ENV=production
python scripts/run_data_pipeline.py

# Estimated recovery time: < 5 minutes
```

---

## Monitoring & Alerts

### Key Metrics to Monitor

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| PAR_90 (%) | < 3.0% | > 3.0% | > 5.0% |
| Collection Rate (%) | > 1.5% | < 1.5% | < 1.0% |
| RDR_90 (%) | > 50% | < 50% | < 25% |
| Portfolio Health (0-10) | > 5.0 | < 5.0 | < 3.0 |
| Pipeline latency | < 10min | > 12min | > 15min |
| Data freshness | < 6hrs | > 8hrs | > 12hrs |
| Error count | 0 | > 5 | > 10 |

### Slack Alerting

**Channels**:
- `#risk-monitoring` - Risk alerts (PAR_90, RDR_90, Collection Rate)
- `#compliance-team` - Compliance alerts (audit flags, data quality)
- `#fintech-reports` - Daily summary report
- `#executive-briefing` - C-level alerts (critical issues only)

**Alert Rules**:
```
PAR_90 > 5.0%         → Critical alert to #executive-briefing + @cfo
Collection Rate < 1%  → Warning to #risk-monitoring
Compliance violation  → Critical alert to #compliance-team + @general-counsel
Pipeline failure      → Critical alert to #devops-alerts + @sre-oncall
```

### Alert Configuration

Configured in `config/pipeline.yml:integrations.slack.alert_channels`

```yaml
integrations:
  slack:
    alert_channels:
      risk_alerts: '#risk-monitoring'
      compliance_updates: '#compliance-team'
      executive_briefing: '#executive-briefing'
      daily_summary: '#fintech-reports'
```

### Dashboard Monitoring

Dashboard refresh schedules:
- **KPI Dashboard**: Updated every 30 minutes
- **Risk Dashboard**: Updated every 15 minutes
- **Executive Dashboard**: Updated hourly (Mondays at 8 AM)

---

## Troubleshooting

### Common Issues & Solutions

#### Pipeline Timeout (Execution > 15 minutes)

**Symptoms**: Pipeline runs longer than 15 minutes

**Investigation**:
```bash
# 1. Check latest run logs
tail -200 logs/runs/latest/pipeline_*.log | grep -i "phase\|error"

# 2. Check which phase is slow
grep "completed at" logs/runs/latest/pipeline_summary.json | jq '.phases'

# 3. Profile the bottleneck phase
python scripts/performance_stress_test.py --phase <phase-name>
```

**Solutions**:
- **Ingestion slow?** Check Cascade API response times and rate limits
- **Transformation slow?** Check for memory issues on large datasets
- **Calculation slow?** Profile KPI computation with `--profile` flag
- **Output slow?** Check Supabase connection and I/O bandwidth

#### High Memory Usage

**Symptoms**: Pipeline crashes or runs slowly after startup

**Investigation**:
```bash
# Monitor process memory
watch -n 1 'ps aux | grep run_data_pipeline | grep -v grep'

# Check dataset size
du -sh data/raw/cascade/loan_tape.csv
```

**Solutions**:
- Increase system RAM if dataset > 10GB
- Implement chunked processing for large files
- Archive old raw data to reduce disk I/O

#### Data Validation Failures

**Symptoms**: Validation errors in transformation phase

**Investigation**:
```bash
# Check validation logs
grep -i "validation\|error" logs/runs/latest/pipeline_*.log

# Review specific failures
python -c "import json; print(json.load(open('logs/runs/latest/validation_report.json')))"
```

**Solutions**:
- Check source data quality from Cascade
- Verify schema hasn't changed: `config/data_schemas/loan_tape.json`
- Review and update validation rules if needed

#### Supabase Connection Issues

**Symptoms**: Outputs not persisted, connection timeouts

**Investigation**:
```bash
# Test Supabase connection
python -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connection OK' if client else 'Connection failed')
"

# Check network connectivity
ping api.supabase.com
```

**Solutions**:
- Verify Supabase credentials in environment variables
- Check VPN/network connection
- Increase connection timeout in config
- Check Supabase status page for incidents

---

## Incident Response

### Severity Levels

| Level | Impact | Response Time | Escalation |
|-------|--------|----------------|------------|
| P1 (Critical) | Complete outage, revenue impact | 15 min | VP Eng + CEO |
| P2 (High) | Partial functionality, data delayed | 1 hour | Eng Lead + CFO |
| P3 (Medium) | Degraded performance | 4 hours | Eng Lead |
| P4 (Low) | Minor issue, no impact | Next business day | Engineer |

### Incident Response Process

```
1. DETECT (automated via alerts)
   └─ Slack alert in #devops-alerts
   └─ PagerDuty notification to on-call

2. ASSESS (5 minutes)
   └─ Determine severity level
   └─ Assess impact (data affected, business impact)
   └─ Notify stakeholders based on severity

3. MITIGATE (varies by severity)
   P1: Execute rollback immediately
   P2: Investigate & attempt fix (30 min), rollback if needed
   P3: Investigate and plan fix
   P4: Add to backlog

4. RESOLVE
   └─ Apply fix or rollback
   └─ Verify resolution
   └─ Document incident

5. POST-MORTEM (within 24 hours)
   └─ Root cause analysis
   └─ Action items to prevent recurrence
   └─ Update runbook if needed
```

### Critical Incident Contact List

| Role | Name | Phone | Slack |
|------|------|-------|-------|
| On-Call Engineer | TBD | TBD | @sre-oncall |
| Engineering Lead | TBD | TBD | @eng-lead |
| VP Engineering | TBD | TBD | @vp-eng |
| CFO | TBD | TBD | @cfo |
| CEO | TBD | TBD | @ceo |

---

## Maintenance

### Weekly Maintenance Tasks

**Monday 2 AM UTC** (off-peak):
```bash
# Clean up old logs (older than 30 days)
find logs/runs -type d -mtime +30 -exec rm -rf {} \;

# Archive raw data (older than 90 days)
find data/raw/cascade -name "*.csv" -mtime +90 -exec mv {} data/archive/ \;

# Run full diagnostics
make audit-code
```

### Monthly Maintenance Tasks

**First Monday of month, 2 AM UTC**:
```bash
# Generate compliance report
python scripts/generate_compliance_report.py

# Review and rotate credentials
# - Update CASCADE_SESSION_COOKIE if needed
# - Rotate SLACK_WEBHOOK_TOKEN
# - Audit access logs

# Backup production database
# - Export Supabase analytics schema to cold storage
# - Verify backup integrity

# Update dependencies (security patches)
pip install --upgrade -r requirements.txt
make quality  # Ensure no breaking changes
```

### Quarterly Maintenance Tasks

**First day of quarter, 2 AM UTC**:
```bash
# Full system audit (ENGINEERING_STANDARDS.md quarterly checklist)
make install-dev
make quality

# Performance benchmarking
python scripts/performance_stress_test.py

# Security audit
# - Scan for hardcoded secrets
# - Review IAM permissions
# - Update security documentation

# Deprecation review
# - Check for deprecated modules marked for deletion
# - Verify migration paths are documented
```

### Annual Tasks

**Every January 1st**:
```bash
# Delete deprecated code from v1.x
# - Remove config/LEGACY/ directory
# - Remove python/kpi_engine.py (use kpi_engine_v2)
# - Update all documentation

# Major version release (v2.0)
# - Consolidated configuration system
# - Unified pipeline architecture
# - Enhanced engineering standards

# Review SLAs and update targets if needed
```

---

## Rollback Procedures

### Why Rollback?

- Critical bugs preventing pipeline execution
- Data quality issues (incorrect KPI calculations)
- Performance degradation (> 2x normal latency)
- Security vulnerability discovered

### Rollback Steps (< 5 minutes)

```bash
# 1. IDENTIFY the failing commit
git log --oneline | head -10

# 2. CHECKOUT the previous working version
git checkout <stable-commit-hash>

# 3. VERIFY the rollback
git log --oneline -1  # Should show stable version

# 4. REINSTALL dependencies (if changed)
pip install -r requirements.txt

# 5. RUN pipeline with previous version
export PIPELINE_ENV=production
python scripts/run_data_pipeline.py

# 6. VERIFY results
# Check that:
#   - Pipeline completes in < 10 min
#   - KPIs calculated correctly
#   - No errors in logs

# 7. NOTIFY team
echo "Rollback complete to $(git rev-parse --short HEAD)" | slack
```

### Preventing Need for Rollback

- Always run `make quality` before committing
- Deploy to staging first (24-hour validation)
- Monitor first 1 hour post-deployment closely
- Have rollback plan documented before deployment

---

## On-Call Runbook

### On-Call Rotation

- **Duration**: 1 week
- **Primary**: Monday - Friday
- **Secondary**: Weekends + holidays
- **Handoff**: Every Monday 9 AM UTC

### First Response (0-15 minutes)

```
1. Check Slack (#devops-alerts, #risk-monitoring)
2. Review PagerDuty alert details
3. Open logs: tail -200 logs/runs/latest/pipeline_*.log
4. Assess severity: P1 = immediate action, P2+ = investigate first
5. If P1: Execute rollback. If P2+: Investigate root cause.
```

### Investigation Steps

```bash
# 1. Get full context
LATEST_RUN=$(ls -t logs/runs | head -1)
cd logs/runs/$LATEST_RUN

# 2. Review summary
cat pipeline_summary.json | jq '.'

# 3. Check which phase failed
grep -i "error\|failed" *_*.log

# 4. Get error details
tail -100 [phase]_error.log

# 5. Correlate with configuration
echo $PIPELINE_ENV  # Should be 'production'
grep -A5 "error" config/pipeline.yml
```

### Escalation Matrix

| Symptom | P-Level | 15-min action | 1-hour action |
|---------|---------|--------------|---------------|
| Pipeline won't run | P1 | Rollback | Root cause analysis |
| PAR_90 > 10% | P2 | Investigate | Alert CFO |
| Data > 12hrs old | P2 | Investigate | Check Cascade API |
| Connection timeout | P3 | Check network | Escalate to SRE |
| Slow performance | P3 | Profile | Optimize or rollback |

---

## Key Files Reference

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `config/pipeline.yml` | Master configuration | As needed |
| `config/environments/production.yml` | Prod overrides | Quarterly |
| `PROGRESS_REPORT.md` | Project status | Monthly |
| `logs/runs/latest/` | Latest run outputs | Every pipeline execution |
| `.rollback/` | Rollback snapshots | On each deployment |

---

**Document Status**: ✅ Production Ready  
**Effective Date**: 2025-12-26  
**Last Reviewed**: 2025-12-26  
**Next Review**: Q1 2026
