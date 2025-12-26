# Week 3 Day 7: Rollback Procedures & Testing
**Date**: December 26, 2025  
**Status**: Documentation & Testing Plan

---

## Executive Summary

This document defines comprehensive rollback procedures for reverting from V2 pipeline back to V1 in case of critical issues. All procedures have been designed for **minimum downtime** (<5 minutes) and **zero data loss**.

---

## Rollback Decision Criteria

### Trigger Rollback If:

**Critical Performance Issues:**
- End-to-end latency > 60 seconds (vs 5ms in tests)
- Memory consumption > 500 MB sustained
- CPU utilization > 90% sustained
- Processing throughput < 50% of baseline

**Data Quality Issues:**
- KPI variance > 5% vs historical baselines
- Data loss detected in output
- Null value handling errors
- Output format incompatibility

**System Stability Issues:**
- Error rate > 5% of transactions
- Database connection failures > 10% of attempts
- Repeated crash/restart cycles
- Unrecoverable deadlocks

**External System Failures:**
- Azure Blob Storage unavailable > 5 minutes
- Supabase database unavailable > 5 minutes
- Data source (Cascade) unavailable > 5 minutes

### NOT Trigger Rollback:
- Single isolated errors (retryable)
- Minor variance (< 1%)
- Performance degradation temporary (<2 minutes)
- Informational warnings

---

## Rollback Decision Process

```
┌─────────────────────────────────────────────────────────┐
│ PRODUCTION ALERT OR ISSUE DETECTED                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────────┐
         │ PAGE ON-CALL ENGINEER           │
         └──────────────┬──────────────────┘
                        │
                        ▼
         ┌─────────────────────────────────┐
         │ ASSESS ISSUE SEVERITY            │
         │ - Performance?                   │
         │ - Data quality?                  │
         │ - System stability?              │
         └──────────────┬──────────────────┘
                        │
                        ▼
            ┌─────────────────────────┐
            │ MEETS ROLLBACK CRITERIA? │
            └──┬─────────────────────┬─┘
               │                     │
          YES  │                     │  NO
               ▼                     ▼
         INITIATE            CONTINUE MONITORING
         ROLLBACK            TROUBLESHOOT
               │
               ▼
        NOTIFY STAKEHOLDERS
               │
               ▼
        EXECUTE ROLLBACK
               │
               ▼
        VERIFY V1 OPERATIONAL
               │
               ▼
        POST-INCIDENT ANALYSIS
```

---

## Rollback Execution Procedure

### Pre-Rollback Checklist (< 2 minutes)

**Phase 1: Verification** (30 seconds)
- [ ] Confirm issue reproducibility
- [ ] Verify rollback criteria met
- [ ] Take production database backup
- [ ] Export last 24 hours V2 metrics (for analysis)
- [ ] Record current system state (logs, metrics)

**Phase 2: Notification** (30 seconds)
- [ ] Notify on-call manager
- [ ] Message #incidents channel
- [ ] Update status page (maintenance mode)
- [ ] Alert customer success team

**Phase 3: Preparation** (1 minute)
- [ ] Stop V2 pipeline scheduler
- [ ] Verify V1 binaries ready
- [ ] Activate standby database connections
- [ ] Pre-stage V1 configuration

### Rollback Execution (< 3 minutes total)

**Step 1: Stop V2 Pipeline** (30 seconds)
```bash
# Stop all V2 pipeline processes
systemctl stop abaco-pipeline-v2 || true

# Verify stopped
pgrep -f "python.*pipeline.*v2" && echo "ERROR: V2 still running" || echo "✓ V2 stopped"

# Capture final V2 status
journalctl -u abaco-pipeline-v2 -n 50 > /tmp/v2_final_state.log
```

**Step 2: Restore V1 Configuration** (30 seconds)
```bash
# Restore V1 environment variables
source /etc/abaco/v1-pipeline.env

# Verify V1 binaries
ls -la /opt/abaco/pipeline-v1/bin/pipeline

# Check V1 database connectivity
python3 -c "import psycopg2; conn = psycopg2.connect(...); print('✓ DB OK')"
```

**Step 3: Start V1 Pipeline** (1 minute)
```bash
# Start V1 service
systemctl start abaco-pipeline-v1

# Wait for startup
sleep 10

# Verify running
systemctl is-active abaco-pipeline-v1 && echo "✓ V1 started" || echo "ERROR: V1 failed"

# Check health endpoint
curl -s http://localhost:8001/health | jq .
```

**Step 4: Validate Rollback** (30 seconds)
```bash
# Test KPI calculation
python3 -c "
from python.kpi_engine import KPIEngine
import pandas as pd
df = pd.read_csv('/tmp/test_data.csv')
engine = KPIEngine(df)
metrics = engine.calculate_metrics()
print('✓ KPI calculations working')
"

# Verify output generation
ls -la /data/metrics/*.parquet | head -5
```

### Post-Rollback Verification (< 30 seconds)

- [ ] All 4 pipeline phases executing
- [ ] KPI calculations producing values
- [ ] Output files being generated
- [ ] No errors in logs
- [ ] Health check passing
- [ ] Database connectivity confirmed

---

## Rollback Testing Procedure (Week 3 Day 7)

### Test 1: Dry-Run Rollback (Staging Environment)

**Objective**: Practice rollback without production impact

**Procedure**:
1. Deploy V2 to staging
2. Run pipeline successfully
3. Simulate failure condition
4. Execute rollback procedures step-by-step
5. Verify V1 operational in staging
6. Document execution time and any issues

**Success Criteria**:
- [ ] Rollback completed in < 5 minutes
- [ ] V1 fully operational after rollback
- [ ] All metrics restored
- [ ] Zero data loss

### Test 2: Rollback with Data Validation

**Objective**: Ensure no data loss or corruption during rollback

**Procedure**:
1. Run V2 pipeline to completion on test data
2. Export final KPI metrics
3. Execute rollback
4. Run V1 pipeline on same test data
5. Compare outputs

**Expected Results**:
- V1 outputs match V2 outputs (< 1% variance)
- No missing data points
- All historical metrics intact

### Test 3: Rollback Time Measurement

**Objective**: Establish baseline for production rollback

**Procedure**:
```bash
#!/bin/bash
START_TIME=$(date +%s)

# Execute rollback procedures
systemctl stop abaco-pipeline-v2
systemctl start abaco-pipeline-v1
sleep 10
curl -s http://localhost:8001/health

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
echo "Rollback completed in ${DURATION} seconds"
```

**Target**: < 300 seconds (5 minutes)

### Test 4: Rollback-Forward Recovery

**Objective**: Test re-deployment of V2 after rollback

**Procedure**:
1. Execute rollback to V1
2. Verify V1 operational
3. Re-deploy V2 to staging
4. Test V2 again
5. Compare with previous V2 run

**Success Criteria**:
- V2 re-deployment successful
- Consistent KPI outputs
- No state corruption

---

## Rollback Rollback (V1 → V2 Recovery)

If rollback itself fails, immediate escalation procedures:

**Emergency Contact Tree**:
1. Primary On-Call Engineer
2. Engineering Manager
3. VP of Engineering
4. CTO

**Emergency Procedures**:
- Halt all pipeline execution
- Switch to read-only mode
- Manual data export
- External database restore from hourly backup
- Incident war room activation

---

## Post-Rollback Analysis

### Immediate Actions (< 2 hours)
- [ ] Root cause analysis initiated
- [ ] Incident timeline documented
- [ ] V2 logs exported for analysis
- [ ] Customer impact assessed

### Short-Term (< 24 hours)
- [ ] Full incident report drafted
- [ ] Corrective actions identified
- [ ] Code review findings documented
- [ ] Updated rollback procedures if needed

### Long-Term (< 1 week)
- [ ] Post-mortem meeting scheduled
- [ ] Lessons learned documented
- [ ] Preventive measures implemented
- [ ] V2 fixes deployed
- [ ] Shadow mode resumed

---

## Rollback Resources

### Pre-Staged Assets

**Location**: `/var/abaco/rollback/`

```
├── v1-pipeline-binaries.tar.gz      (pre-compiled V1)
├── v1-configuration.yml              (V1 config)
├── v1-database-migrations.sql        (schema)
├── rollback-scripts/
│   ├── stop-v2.sh
│   ├── start-v1.sh
│   ├── validate-rollback.sh
│   └── notify-stakeholders.sh
├── documentation/
│   ├── V1-Operations-Manual.md
│   ├── V1-Troubleshooting.md
│   └── Database-Recovery.md
└── contact-tree.txt                  (escalation)
```

### Rollback Contacts

**On-Call Schedule**:
- Primary: [TBD - Operations Team]
- Secondary: [TBD - Engineering]
- Manager: [TBD - Engineering Lead]
- Executive: [TBD - CTO]

**Communication Channels**:
- Slack: #incidents
- PagerDuty: abaco-incidents
- Email: ops-team@abaco.com
- Phone: [TBD]

---

## Testing Checklist (Week 3 Day 7)

- [ ] Dry-run rollback completed in staging
  - [ ] Time: _____ seconds
  - [ ] V1 fully operational: YES / NO
  - [ ] Issues: ______________
  
- [ ] Data validation tests passed
  - [ ] No data loss: YES / NO
  - [ ] Output variance < 1%: YES / NO
  
- [ ] Rollback time measured
  - [ ] Actual time: _____ seconds
  - [ ] Within 5-minute target: YES / NO
  
- [ ] Rollback-forward recovery tested
  - [ ] V2 re-deployment successful: YES / NO
  - [ ] Consistent outputs: YES / NO
  
- [ ] Contact tree verified
  - [ ] All contacts reachable: YES / NO
  - [ ] Contact information current: YES / NO
  
- [ ] Documentation reviewed
  - [ ] All procedures clear: YES / NO
  - [ ] Team trained on procedures: YES / NO
  - [ ] Runbooks updated: YES / NO

---

## Sign-Off

**Engineering**: _________________________ Date: _________

**Operations**: _________________________ Date: _________

**Management**: _________________________ Date: _________

---

## Appendix: Quick Reference

### Emergency Rollback (Production)
```bash
# 1. Stop V2
systemctl stop abaco-pipeline-v2

# 2. Start V1
systemctl start abaco-pipeline-v1

# 3. Verify
curl http://localhost:8001/health

# 4. Alert stakeholders
echo "ROLLBACK COMPLETE" | mail -s "ABACO ROLLBACK" ops-team@abaco.com
```

### Rollback Verification
```bash
# Check V1 service
systemctl status abaco-pipeline-v1

# Monitor logs
tail -f /var/log/abaco/pipeline.log

# Test calculation
python3 /opt/abaco/test-kpi.py
```

### Emergency Contacts
- On-Call: [contact info]
- Manager: [contact info]  
- CTO: [contact info]

---

**Document Version**: 1.0  
**Last Updated**: December 26, 2025  
**Next Review**: Before Week 4 Production Cutover
