# Migration Guide

**Version**: 2.0  
**Date**: 2025-12-26  
**Audience**: Technical teams, DevOps, Project Managers

---

## Overview

This document guides migration from the legacy fragmented system to the Abaco Loans Analytics V2 Unified Pipeline. The V2 pipeline consolidates configuration, code, and operational procedures into a single, cohesive system with zero production downtime.

**Key Improvements**:
- ✅ Unified 4-phase pipeline (Ingestion → Transformation → Calculation → Output)
- ✅ 18 fragmented config files → 1 master + 3 environment overrides
- ✅ 4 duplicate modules eliminated
- ✅ Automatic environment resolution (dev/staging/production)
- ✅ 100% backwards compatible
- ✅ Zero production downtime during migration

---

## Migration Timeline

### Phase 1: Preparation (2-3 days)

**Tasks**:
1. Review this migration guide
2. Set up staging environment
3. Backup all production data
4. Notify stakeholders
5. Pre-production validation

**Completion Criteria**:
- [ ] All team members read this guide
- [ ] Staging environment ready
- [ ] Production backup verified
- [ ] Stakeholders notified
- [ ] Rollback plan documented

### Phase 2: Staging Deployment (1-3 days)

**Tasks**:
1. Deploy V2 pipeline to staging
2. Run 24-hour shadow mode validation
3. Compare outputs with production
4. Resolve any discrepancies
5. Stakeholder sign-off

**Completion Criteria**:
- [ ] Staging deployment successful
- [ ] 24-hour validation period complete
- [ ] All outputs match production (within tolerance)
- [ ] All tests passing
- [ ] Stakeholder approval obtained

### Phase 3: Production Cutover (< 5 minutes)

**Tasks**:
1. Execute production cutover script
2. Run initial validation checks
3. Monitor for 24 hours
4. Verify all systems operational
5. Document final status

**Completion Criteria**:
- [ ] Production cutover completed
- [ ] All validation checks passing
- [ ] Hour 1 monitoring complete (no issues)
- [ ] 24-hour monitoring complete
- [ ] Migration successful

### Phase 4: Post-Migration (ongoing)

**Tasks**:
1. Monitor production daily
2. Collect user feedback
3. Document any issues found
4. Plan optimization improvements
5. Delete deprecated code (v2.0 release)

**Completion Criteria**:
- [ ] 7 days post-migration monitoring complete
- [ ] No critical issues identified
- [ ] User feedback incorporated
- [ ] Optimization plan documented
- [ ] Scheduled deprecation cleanup

---

## Pre-Migration: What's Changing

### Configuration System

**BEFORE**: 18 fragmented files
```
config/
├── integrations/ (4 files)
├── agents/specs/ (4 files)
├── kpis/ (3 files)
├── pipelines/ (1 file)
├── data_schemas/ (1 file)
└── [8 other scattered files]
```

**AFTER**: 4 unified files
```
config/
├── pipeline.yml (526 lines - master)
├── environments/
│   ├── development.yml (49 lines)
│   ├── staging.yml (58 lines)
│   └── production.yml (64 lines)
└── LEGACY/ (archived with deprecation guide)
```

**Impact**: Zero code changes, automatic environment detection

### Code Changes

**DELETED**:
- `python/ingestion.py` (replaced by `pipeline/ingestion.py`)
- `python/transformation.py` (replaced by `pipeline/transformation.py`)

**DEPRECATED**:
- `python/kpi_engine.py` → Use `python/kpi_engine_v2.py` instead

**MODIFIED**:
- `python/pipeline/orchestrator.py` - Added environment-aware config loading

**IMPACT**: All imports already correct (consolidation completed in Phase 3A)

### Behavioral Changes

**NONE** - V2 pipeline behaves identically to V1

**What stays the same**:
- ✅ Same 4-phase pipeline structure
- ✅ Same KPI calculations
- ✅ Same output formats (Parquet, CSV, JSON, Supabase)
- ✅ Same monitoring and alerts
- ✅ Same performance characteristics
- ✅ Same data validation rules

**What's new**:
- ✅ Automatic environment resolution (PIPELINE_ENV variable)
- ✅ Cleaner configuration management
- ✅ Better code organization
- ✅ Enhanced engineering standards

---

## Migration: Step-by-Step Instructions

### Step 1: Preparation & Backup (Day 1)

```bash
# 1. Notify team of planned migration
echo "V2 Pipeline migration scheduled for [DATE] [TIME]" | slack

# 2. Create production backup
pg_dump -U admin abaco_analytics > backups/abaco_analytics_$(date +%Y%m%d).sql

# 3. Export current Supabase schema
supabase db dump --format plain > backups/supabase_$(date +%Y%m%d).sql

# 4. Document current system state
git log --oneline -1 > backups/current_commit.txt
env | grep CASCADE > backups/environment_vars.txt

# 5. Verify backup integrity
ls -lah backups/
du -sh backups/
```

### Step 2: Staging Deployment (Day 2)

```bash
# 1. Clone latest V2 code
git clone <repo-url> -b refactor/pipeline-complexity

# 2. Install dependencies
cd abaco-loans-analytics
pip install -r requirements.txt

# 3. Deploy to staging environment
export PIPELINE_ENV=staging
export CASCADE_SESSION_COOKIE="<staging-token>"
export SLACK_WEBHOOK_TOKEN="<staging-webhook>"

# 4. Run initial test pipeline
python scripts/run_data_pipeline.py --input data/raw/test/loan_tape_sample.csv

# 5. Verify outputs
ls -la logs/runs/latest/
cat logs/runs/latest/pipeline_summary.json | jq '.'

# 6. Run 24-hour validation (shadow mode)
# Keep pipeline running for 24 hours and collect outputs

# 7. Compare with production
python scripts/compare_outputs.py \
  --production logs/production/latest/ \
  --staging logs/runs/latest/
```

### Step 3: Verification & Sign-Off (Day 3)

```bash
# 1. Run comprehensive validation
make quality  # format, lint, type-check, test

# 2. Compare KPI outputs
echo "Comparing PAR_90, Collection Rate, Portfolio Health..."
diff <(jq '.metrics | keys' logs/production/latest/metrics.json) \
     <(jq '.metrics | keys' logs/runs/latest/metrics.json)

# 3. Validate data lineage
echo "Checking data consistency..."
python scripts/validate_lineage.py

# 4. Check compliance & audit logs
wc -l logs/runs/latest/*_compliance.json

# 5. Get stakeholder approval
# Email with results: metrics_comparison.txt, validation_report.txt
```

### Step 4: Production Cutover (< 5 minutes)

```bash
# CUTOVER WINDOW: [DATE] [TIME-5 minutes to TIME+1 hour]
# Do not run any other operations during this window

# 1. NOTIFY TEAM
echo "🚀 Starting V2 Pipeline production cutover now" | slack

# 2. UPDATE PRODUCTION ENVIRONMENT
export PIPELINE_ENV=production
export CASCADE_SESSION_COOKIE="<production-token>"
export SLACK_WEBHOOK_TOKEN="<production-webhook>"

# 3. VERIFY CONFIGURATION
python -c "from python.pipeline.orchestrator import PipelineConfig; \
c = PipelineConfig(); \
print(f'Environment: {c.environment}'); \
print(f'Config version: {c.config.get(\"version\")}')"

# 4. DEPLOY & RUN PIPELINE
python scripts/run_data_pipeline.py \
  --input data/raw/cascade/loan_tape.csv \
  --validate

# 5. VERIFY IMMEDIATE RESULTS (next 5 minutes)
echo "Execution time:" $(jq '.completed_at - .started_at' logs/runs/latest/pipeline_summary.json)
echo "KPI Count:" $(jq '.phases.calculation.metrics | length' logs/runs/latest/pipeline_summary.json)

# 6. HOUR 1 VALIDATION (automated)
python scripts/hour1_validation.py

# 7. CONTINUE MONITORING
watch -n 10 'tail -20 logs/runs/latest/pipeline_*.log'
```

### Step 5: Post-Migration Monitoring (24-48 hours)

```bash
# HOUR 1 (Critical)
# Run automated validation checks
make test  # All 29 tests must pass

# HOUR 4
# Check alert channels for any warnings
# #risk-monitoring, #compliance-team, #fintech-reports

# HOUR 24 (Full validation)
# 1. Verify all scheduled tasks ran
# 2. Compare daily metrics with historical average
# 3. Check Supabase data persistence
# 4. Review all logs for errors

# IF ANY ISSUES FOUND
# Follow incident response in OPERATIONS.md
```

---

## Rollback Procedures

### When to Rollback

If during the **first 24 hours** you encounter:
- Pipeline execution failures (> 2 consecutive failures)
- Significant KPI calculation differences (> 5%)
- Data persistence issues (Supabase write failures)
- Performance degradation (> 2x normal latency)
- Security/compliance violations

### How to Rollback (< 5 minutes)

```bash
# 1. STOP production pipeline
killall python  # Stop any running processes

# 2. RESTORE PREVIOUS VERSION
git checkout <previous-stable-commit>
pip install -r requirements.txt

# 3. VERIFY ROLLBACK
python -c "import sys; from python.pipeline.orchestrator import PipelineConfig; \
c = PipelineConfig(); sys.exit(0 if c else 1)"

# 4. RUN WITH PREVIOUS VERSION
export PIPELINE_ENV=production
python scripts/run_data_pipeline.py

# 5. NOTIFY TEAM
echo "⚠️ Rolled back to previous version. Investigating..." | slack

# 6. INVESTIGATE ISSUE
# - Review logs from failed run
# - Check environment variables
# - Verify configuration
# - Contact engineering team
```

**Rollback Recovery Target**: < 5 minutes downtime

---

## Configuration Migration

### BEFORE: Manual Configuration

```bash
# Old way: spread across multiple files
export CASCADE_EXPORT_URL="..."
export SLACK_WEBHOOK_TOKEN="..."
# ... 10+ more environment variables ...

# User had to know which configuration files to update
# Risk of inconsistency across environments
```

### AFTER: Automatic Configuration

```bash
# New way: environment variable control
export PIPELINE_ENV=production

# Automatically loads:
# 1. config/pipeline.yml (master)
# 2. config/environments/production.yml (overrides)
# 3. Merges with placeholders resolved from env vars

# Zero configuration differences between environments
# Single source of truth for each setting
```

### Migration Checklist

- [ ] Update deployment scripts to use PIPELINE_ENV
- [ ] Update documentation with new env var usage
- [ ] Update CI/CD pipelines for new config system
- [ ] Update Terraform/IaC if applicable
- [ ] Update monitoring/alerting for config changes
- [ ] Train ops team on new system

---

## Code Migration Checklist

### For Development Teams

- [ ] Review `ENGINEERING_STANDARDS.md` for best practices
- [ ] Install dev dependencies: `make install-dev`
- [ ] Run full quality check: `make quality`
- [ ] Update any custom code to use `python/kpi_engine_v2`
- [ ] Update imports if using deprecated modules

### For DevOps/SRE

- [ ] Review `OPERATIONS.md` for deployment procedures
- [ ] Update deployment scripts to use `PIPELINE_ENV`
- [ ] Update monitoring dashboards (URLs unchanged)
- [ ] Update alert thresholds if needed
- [ ] Test rollback procedures
- [ ] Update on-call runbook

### For QA/Testing

- [ ] Run all tests: `make test`
- [ ] Verify coverage ≥ 85%: `make test-cov`
- [ ] Run performance tests: `python scripts/performance_stress_test.py`
- [ ] Validate all 5 test data scenarios
- [ ] Test rollback procedures

---

## Validation Checklist

### Pre-Cutover (Staging)

- [ ] All tests passing (29/29)
- [ ] Linting clean (0 errors)
- [ ] Type checking clean (0 errors)
- [ ] Coverage ≥ 85%
- [ ] KPI outputs match within tolerance (< 1%)
- [ ] All alerts routing correctly
- [ ] Compliance reports generated
- [ ] Performance metrics acceptable

### Post-Cutover (Hour 1)

- [ ] Pipeline completed successfully
- [ ] Execution time < 10 minutes
- [ ] All 4 KPI categories calculated
- [ ] Outputs persisted to Supabase
- [ ] No error logs in latest run
- [ ] Slack alerts functional
- [ ] Dashboard updated with new data

### Post-Cutover (Hour 24)

- [ ] 24-hour continuous operation successful
- [ ] Daily alerts sent at scheduled times
- [ ] No data quality issues detected
- [ ] Supabase schema queries working
- [ ] Archive and cleanup completed
- [ ] Compliance reports generated
- [ ] Performance within SLAs

---

## FAQ

**Q: Will this require downtime?**  
A: No, V2 pipeline is 100% backwards compatible. Cutover takes < 5 minutes.

**Q: Will my queries break?**  
A: No, Supabase schema and output formats unchanged.

**Q: What about my custom integrations?**  
A: All integrations (Cascade, Meta, Slack) configured in `config/pipeline.yml`. No code changes needed.

**Q: Can I rollback if something goes wrong?**  
A: Yes, rollback takes < 5 minutes. Simply checkout previous commit.

**Q: Do I need to update my monitoring?**  
A: No, all metrics and alerts continue to work. Only environment detection is automatic now.

**Q: What about the deprecated modules?**  
A: They're marked with clear migration paths. Old code still works. Deletion scheduled for v2.0 (Q1 2026).

**Q: How do I know if the migration succeeded?**  
A: All validation checks must pass (see validation checklist above). Stakeholder sign-off required.

---

## Support & Escalation

### During Migration (24-hour Support)

| Issue | Action | Contact |
|-------|--------|---------|
| Configuration error | Check CLAUDE.md | @eng-lead |
| Pipeline failure | Review logs, check OPERATIONS.md | @sre-oncall |
| Data discrepancy | Compare outputs, contact support | @data-team |
| Urgent/Critical | Execute rollback, investigate | @vp-eng |

### Post-Migration

Standard incident response applies (see OPERATIONS.md incident response section).

---

## Success Criteria

Migration is successful when:

1. ✅ Production cutover completed (< 5 minutes)
2. ✅ All validation checks passing
3. ✅ 24-hour continuous operation without issues
4. ✅ Zero data quality problems detected
5. ✅ All stakeholders confirmed operational
6. ✅ Performance metrics within SLAs
7. ✅ Team trained on new procedures
8. ✅ Documentation updated

---

**Document Status**: ✅ Production Ready  
**Effective Date**: 2025-12-26  
**Last Reviewed**: 2025-12-26  
**Next Review**: Post-Migration (48 hours)
