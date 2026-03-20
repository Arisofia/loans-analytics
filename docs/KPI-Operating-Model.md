# KPI Operating Model

**Document Status**: P8 Documentation Remediation (2026-03-20)  
**Pillar**: Financial Precision & KPI SSOT (P4/P5)  
**Owner**: Head of Risk (per OWNER_MAP.md)

## Overview

This document defines the operating model for KPI ownership, change control, and governance.

## KPI Ownership & Responsibilities

### Head of Risk (Primary Owner)
**Owns**: PAR30, PAR90, NPL Ratio, NPL-90 Ratio, Default Risk Models  
**Responsibilities**:
- Approve changes to risk metric definitions
- Monitor metric accuracy & reconciliation
- Escalate anomalies to CFO

### CFO (Finance Owner)
**Owns**: Collection Efficiency, DSCR, APR Portfolio, Rotation  
**Responsibilities**:
- Approve changes to financial KPIs
- Own variance analysis vs. targets
- Approve guardrail adjustments

### Head of Pricing
**Owns**: APR Distribution, Portfolio Yield, Rate Spread  
**Responsibilities**:
- Monitor pricing effectiveness
- Flag risk-adjusted yield mismatches

### Data & Analytics Team
**Owns**: Implementation & Calculation  
**Responsibilities**:
- Execute KPI computation changes in code
- Maintain pipeline orchestration
- Validate calculations quarterly

## KPI Definition Version Control

**Authority**: `config/kpis/` directory

Each KPI file follows this naming convention:
```
kpi_<name>_v<version>.yml
```

Example:
- `kpi_par30_v1.yml` — Version 1 (initial)
- `kpi_par30_v2.yml` — Version 2 (updated formula)

**Change Log**:
Each KPI file includes a `changelog` section:
```yaml
kpi_name: "par_30"
version: 2
changelog:
  - date: "2026-01-15"
    author: "Risk Team"
    change: "Added status-based delinquency inclusion"
    formula_from: "SUM(outstanding_balance WHERE dpd >= 30) / ..."
    formula_to: "SUM(outstanding_balance WHERE dpd >= 30 OR status IN ['delinquent', 'defaulted']) / ..."
    impact: "PAR30 increased 0.5pp due to delinquent addition"
```

## Change Approval Workflow

1. **Proposal**: Owner submits KPI change with business justification
2. **Impact Analysis**: Data team models change effect on historical KPIs
3. **Review**: Owner + CFO review impact assessment
4. **Approval**: Authorize code change
5. **Implementation**: Update `backend/python/kpis/ssot_asset_quality.py`
6. **Testing**: Verify calculation matches expected impact
7. **Deployment**: Release to production
8. **Audit**: Monthly reconciliation of changed KPI vs. prior version

## Formula Authority (SSoT)

**Single Source of Truth Location**: `backend/python/kpis/ssot_asset_quality.py`

All KPI calculations must route through the formula engine for these metrics:
- PAR30, PAR60, PAR90
- NPL-90 Proxy, NPL-180 Proxy
- Plus any new asset quality metrics added

**Non-SSoT Metrics** (owner-specific, not centralized):
- Collection Efficiency (Finance)
- DSCR (Finance)
- Concentration metrics (Risk) — *future SSOTization*

## Reconciliation Schedule

### Monthly (Data Team)
- Validate calculated KPIs match expected formulas
- Flag any > 1bps variance

### Quarterly (Owner + CFO)
- Reconcile against external benchmarks
- Review definition accuracy vs. business intent
- Approve any minor adjustments

### Annually (Governance Committee)
- Full audit of all KPI definitions
- Benchmark against regulatory guidance
- Update operating model if needed

## Emergency Change Procedures

**Critical Bug** (e.g., calculation error):
1. Head of Risk + CFO approve emergency fix (same day)
2. Change implemented with full testing
3. Post-implementation audit next business day
4. Document in changelog with "EMERGENCY" tag

**Example Scenario**: PAR30 formula inadvertently excluded "delinquent" status  
→ Approved for immediate fix by Risk & CFO  
→ Deployed same day  
→ Reconciliation report run next day showing impact

## Documentation & Training

- **Quarterly**: Owner presents KPI updates to leadership
- **On-Boarding**: New data team members trained on SSoT location & change process
- **Runbook**: `OPERATIONS.md`, Section "KPI Operational Checks"

---

## Appendix: Current Active KPIs

| KPI | Version | Owner | SSoT Authority |
|-----|---------|-------|-----------------|
| PAR30 | 1.0 | Head of Risk | ssot_asset_quality | 
| PAR90 | 1.1 | Head of Risk | ssot_asset_quality |
| NPL Ratio | 1.0 | Head of Risk | ssot_asset_quality |
| NPL-90 Ratio | 1.0 | Head of Risk | ssot_asset_quality |
| Collection Efficiency | 1.0 | CFO | formula_engine |
| DSCR | 1.0 | CFO | formula_engine |
| APR Portfolio | 1.0 | Head of Pricing | formula_engine |
| Portfolio Concentration | 1.0 | Head of Risk | engine.py (pending SSOTization) |
