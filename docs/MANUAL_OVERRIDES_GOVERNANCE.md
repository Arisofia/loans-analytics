# Manual Overrides Governance Framework

**Status**: Production Ready  
**Effective Date**: 2026-03-19  
**Owner**: Data Governance (Risk & Compliance)  
**Last Updated**: 2026-03-19 (R-17 Remediation)  

---

## Executive Summary

Manual overrides are exception-handling mechanisms that allow authorized personnel to adjust automated systems when standard rules don't apply. This document establishes governance, approval processes, and audit requirements for all manual overrides in the Abaco Loans Analytics platform.

**Key Principles**:
- Overrides are exceptions, not standard operations
- All overrides require documented justification and approval
- Overrides are subject to audit, monitoring, and periodic review
- Override systems must maintain immutable audit logs
- No backdoor overrides (all changes tracked in version control)

---

## 1. Manual Override Categories

### 1.1 Customer/Client Overrides

**System**: `data/raw/client_manual_overrides.csv`  
**Scope**: Customer attributes that deviate from automated mappings

| Attribute | Purpose | Example | Approval Level |
|-----------|---------|---------|-----------------|
| **KAM (Key Account Manager)** | Sales relationship owner | Hunter vs. Farmer assignment | Sales Manager |
| **Industry Segment** | Portfolio segmentation | Override auto-detected industry | Risk Manager |
| **LendingTree Customer ID** | Third-party API mapping | Correct mismatched ID | Credit Engineering |
| **Client Name** | Customer reference | Normalize misspelled names | Compliance Officer |

**Associated Script**: `scripts/data/fill_kam_from_desembolsos.py`  
**Data Source**: Google Sheets (INTERMEDIA + DESEMBOLSOS)  
**Update Frequency**: Monthly (reconciliation) + Ad-hoc (exceptions)

**Risk**: 
- If KAM is wrong, sales incentives misallocated
- If industry is wrong, risk analytics distorted
- If customer ID wrong, API integration fails

### 1.2 Business Rule Overrides

**System**: `config/business_rules.yaml`  
**Scope**: Loan status mappings, classification rules, risk thresholds

**Examples**:
- Status mapping: "Morato" → "delinquent" (requires custom mapping)
- Grace period exceptions: Allow payment beyond N days
- Default classification: Move loan to default despite recent payment

**Approval Level**: Credit Committee / CRO  
**Change Control**: CHANGELOG entry + git commit + Slack notification

### 1.3 Financial Guardrail Adjustments

**System**: `config/business_parameters.yml`  
**Scope**: KPI thresholds, concentration limits, SLA targets

**Examples**:
- Default rate threshold: 4% → 5% (temporary market adjustment)
- Rotation target: 4.5x → 4.0x (portfolio adjustment)
- Concentration limit: 30% → 35% (single large customer)

**Approval Level**: CFO / CRO / Board Risk Committee  
**Change Control**: GOVERNANCE.md section "Financial Guardrail Changes"

### 1.4 KPI Calculation Overrides

**System**: `backend/python/kpis/` modules  
**Scope**: Temporary calculation adjustments (e.g., exclude outlier periods)

**Examples**:
- Exclude Q4 2025 from rotation calculation (data quality issue)
- Use alternative formula for PAR (grace period adjustment)
- Override default rate classification (disputed delinquency)

**Approval Level**: Head of Analytics / CRO  
**Implementation**: Code comment + git commit + CHANGELOG entry

---

## 2. Governance Model

### 2.1 Three-Tier Approval Process

#### Tier 1: Operational Overrides (≤$100K impact)
- **Decision Maker**: Team Lead / Department Manager
- **Notification**: Slack #loans-operations; email to Risk@
- **Documentation**: CSV row + email justification
- **Audit Trail**: GitHub commit (if config file change)
- **Approval Time**: 1-2 business days
- **Examples**: KAM assignment correction, name normalization

#### Tier 2: Material Overrides ($100K–$1M impact)
- **Decision Maker**: Director / Risk Manager
- **Approval Process**: 
  1. Requester submits override request (email + brief memo)
  2. Risk reviews for conflict with policies
  3. Director approves/rejects with sign-off
  4. Finance spot-checks impact
- **Documentation**: Override memo + approved email chain + git commit
- **Audit Trail**: Immutable in override register (spreadsheet tracked in version control)
- **Approval Time**: 3-5 business days
- **Examples**: Industry classification bulk changes, SLA threshold adjustment

#### Tier 3: Strategic Overrides (>$1M impact)
- **Decision Maker**: CFO/CRO/Board Risk Committee
- **Approval Process**: 
  1. Prepare business case (2-3 pages, decision framework)
  2. Present to committee with risk impact analysis
  3. Board formal approval (if >$5M or policy change)
  4. Finance validates impact models
  5. Compliance confirms no regulatory conflict
- **Documentation**: Board minutes + business case + impact model + git commit
- **Audit Trail**: Board-approved memo + override register + version-controlled trace
- **Approval Time**: 10-15 business days
- **Examples**: Default rate threshold change, concentration limit increase, guardrail adjustment

### 2.2 Approval Checklist Template

```yaml
Override Request: [Brief Title]
Date Submitted: [YYYY-MM-DD]
Requested By: [Name, Title, Signature]
Impact Category: [Operational / Material / Strategic]
Requested Approval Level: [Tier 1/2/3]

JUSTIFICATION
- Business reason for override
- Why standard rule doesn't apply
- Temporary vs. permanent classification
- Expected duration (if temporary)

IMPACT ANALYSIS
- Estimated financial impact: $ [amount]
- Portfolio affected: [# loans, # customers]
- Risk metrics affected: [list KPIs]
- Operational complexity: [Low/Medium/High]

MITIGATION PLAN
- Monitoring required: [frequency, metric]
- Review schedule: [monthly/quarterly/annually]
- Rollback plan if conditions change
- Stakeholder notifications

APPROVALS
- [ ] Risk Manager approved [Name, Date]
- [ ] Finance spot-check complete [Name, Date]
- [ ] Director/CFO final approval [Name, Date]
- [ ] Compliance cleared [Name, Date]

IMPLEMENTATION
- [ ] Updated in version control (git commit ready)
- [ ] Audit trail documented
- [ ] Stakeholders notified
- [ ] Monitoring dashboard created
- [ ] Calendar reminder set for review
```

---

## 3. Audit & Compliance Requirements

### 3.1 Immutable Audit Trail

All manual overrides must maintain immutable records:

**Version Control Trail** (Primary):
- Git commits with clear messages: `"override: [category] - [brief reason] (Approved: [approver])"`
- Example: `"override: KAM assignment - Customer merger (Approved: Sales Manager on 2026-03-19)"`
- Linked to approved email / board minutes (referenced in commit message)

**Override Register** (Secondary):
- Location: `docs/operations/OVERRIDE_REGISTER.md`
- Format: Table with columns: Date, Category, Requester, Approver, Impact, Status, Expiry
- Maintained in version control (git history = audit trail)
- Updated on approval, marked complete on expiry

**Email Chain** (Tertiary):
- Approval chain archived to shared mailbox (Risk-Governance@)
- Linked to override register row (commit message includes "Ref: #123" to email thread)

### 3.2 Regular Audit Reviews

| Review Type | Frequency | Owner | Scope | Action if Issues Found |
|------------|-----------|-------|-------|----------------------|
| **Daily Monitor** | Daily | Risk Operations | All overrides > $1M, due for expiry | Alert if override exceeded boundaries |
| **Weekly Report** | Weekly | Data Governance | New overrides, missing approvals | Escalate non-compliant overrides |
| **Monthly Review** | Monthly | Risk Manager | All active overrides, impact validation | Verify financial impact matches projection |
| **Quarterly Audit** | Quarterly | Internal Audit | Override register completeness, approval levels | Sanction non-compliance; retraining |
| **Annual Assessment** | Annually | Audit Committee | Override patterns, trends, systemic issues | Policy updates; new categories as needed |

### 3.3 Compliance Flags

Automatic detection triggers for:
- **Red Flag**: Override used without documented approval (= data integrity incident)
- **Yellow Flag**: Override expired but not removed (= stale data)
- **Yellow Flag**: Same override requested 3+ times (= rule should be updated, not overridden)
- **Red Flag**: Override authorized by someone not in approval matrix (= unauthorized change)
- **Red Flag**: Override impact >2x projection (= either model failure or override misclassified)

**Response Protocol**:
- Red flags → 24-hour incident investigation + stakeholder notification
- Yellow flags → Weekly risk committee discussion; determine if rule change needed

---

## 4. Implementation Guidelines

### 4.1 Customer Override CSV Format

**File**: `data/raw/client_manual_overrides.csv`

```csv
cod_cliente,cliente,kam,industry,lt_customer_id,override_reason,effective_date,expiry_date,approved_by
12345,ABC Holdings Inc,JUAN_HUNTER,financial_services,LS-789456,KAM correction - HQ consolidation,2026-03-19,2026-12-31,Sales Manager
12346,XYZ Traders,MARIA_FARMER,agriculture_exports,,Industry reclassification,2026-03-19,,Risk Manager
```

**Column Definitions**:
- `cod_cliente`: Customer code (required, unique key)
- `cliente`: Customer name (required, for reference)
- `kam`: Key Account Manager (optional, leave blank to auto-assign)
- `industry`: Industry segment (optional, override if auto-detection wrong)
- `lt_customer_id`: LendingTree cus ID (optional, for API mapping)
- `override_reason`: Why override exists (required, for audit)
- `effective_date`: When override starts (required, YYYY-MM-DD)
- `expiry_date`: When override expires (optional, blank = until reviewed)
- `approved_by`: Who approved the override (required, Name + Title)

### 4.2 Config File Override Format

**File**: `config/business_rules.yaml`

```yaml
# Manual Overrides Section
manual_overrides:
  loan_status_exceptions:
    # Format: status_code -> canonical_status
    # Reason: [justification], Approved: [name, date], Expires: [date or 'indefinite']
    "X-GRACE": "active"  # Reason: 30-day grace period for COVID relief; Approved: CRO (2026-02-01); Expires: 2026-12-31
    "DISPUTE": "delinquent"  # Reason: Disputed payment < 7 days old; Approved: Risk Manager; Expires: indefinite (requires quarterly review)

  threshold_overrides:
    # Default rate threshold exception (old: 0.04, new: 0.05)
    default_rate_adjustment: 0.00  # Temporary +1% adjustment for Q1 2026; Approved: CFO (2026-03-01); Expires: 2026-04-30
```

### 4.3 Git Commit Message Format

```
override: [CATEGORY] - [BRIEF DESCRIPTION]

Details:
- Basis: [Why standard rule doesn't apply]
- Impact: [Affected metrics/customers]
- Approved By: [Name, Title, Approval Date]
- Ref: [Email thread ID or Board minutes reference]
- Duration: [Temporary until X OR Permanent]

TODO: [If temporary, add calendar reminder for review date]
```

Example:
```
override: KAM assignment - Customer merger creates conflict

Details:
- Basis: ABC Holdings acquired XYZ Traders; sales account consolidation pending
- Impact: 2 customers, ~$250K portfolio
- Approved By: Sales Manager (2026-03-19)
- Ref: Email thread: [Merged Customer - KAM Assignment]
- Duration: Temporary until 2026-06-30 (when merger complete)

TODO: Calendar reminder for 2026-06-15 to review and finalize assignment
```

---

## 5. Specific Override Procedures

### 5.1 Customer KAM Override Procedure

1. **Request Phase**:
   - Requester (Sales/Operations) fills out KAM override form
   - Justification: business reason (promotion, restructure, departure)
   - Impact: # customers, portfolio value

2. **Approval Phase**:
   - Sales Manager reviews: Is new KAM qualified? Are customers OK with change?
   - Finance reviews: Portfolio impact <$500K? (otherwise escalate to Director)
   - If approved, returns signed email

3. **Implementation**:
   - Data Governance adds row to `client_manual_overrides.csv`
   - Includes: cod_cliente, cliente, kam, approved_by, effective_date, expiry_date (if temporary)
   - Commits to git with message format above
   - Notifies affected teams (Slack #operations)

4. **Monitoring**:
   - KAM.py script picks up the override on next run
   - Weekly: Risk review to ensure no orphaned overrides
   - Monthly (or at expiry): Sales Manager confirms override still needed

5. **Cleanup**:
   - Reminder email at expiry - 2 weeks
   - Either renew (new approval) or delete (remove CSV row, commit)

---

### 5.2 Default Rate Threshold Override Procedure

1. **Request Phase**:
   - Submitted by: Head of Risk or CRO
   - Justification: market adjustment, portfolio strategy shift, stress test scenario
   - Data: Modeling impact on KPIs, affected loan segments, risk concentrations

2. **Approval Phase** (Tier 2/3):
   - For >$1M impact: Finance + CRO approval + Board Risk Committee
   - Risk validates: Does override conflict with regulatory capital requirements?
   - Compliance: Confirm no regulatory breach (Basel III LCR, local limits)

3. **Implementation**:
   - Update `config/business_parameters.yml`: `max_default_rate: 0.05` (from 0.04)
   - Git commit with detailed message (link to board minutes / approval)
   - Update GOVERNANCE.md "Active Guardrail Adjustments" section
   - Notify: Data Engineering, Analytics, Risk Reporting

4. **Monitoring**:
   - Daily: Is actual default rate approaching new threshold?
   - Weekly: Risk committee reviews utilization of threshold budget
   - Monthly: Impact analysis on KPI performance, concentration metrics

5. **Cleanup**:
   - Set calendar reminder for expiry date (typically 1-2 quarters)
   - At expiry: Revert to original threshold; update git history
   - Post-analysis: What did we learn? Should rule change permanently?

---

## 6. Escalation Procedures

### If Override Approval Is Delayed
- **Day 3**: Request escalation to director-level
- **Day 5**: CCO (Chief Compliance Officer) involvement
- **Day 10**: CFO decision or defer to Board Risk Committee

### If Override Impact Exceeds Projection
- **Scenario**: Override was to increase default rate threshold by 1%; actual impact is +3%
- **Immediate**: Risk committee emergency meeting (within 24 hours)
- **Action**: Either (A) tighten other controls to compensate, or (B) revert override
- **Investigation**: Why did projection miss? Improve modeling for future overrides
- **Learning**: Remove override category or establish guardrail to prevent future overruns

### If Override Discovered Without Approval (Data Integrity Incident)
- **Immediate**: Suspect data integrity; likely caused by:
  - Manual CSV edit without git commit
  - Database direct update (bypassing procedures)
  - Unauthorized person with CSV access
- **Response**: 
  1. Revert override to baseline (immediate)
  2. 24-hour investigation (audit logs, access control)
  3. Incident report to Board Risk Committee
  4. Policy update to prevent recurrence

---

## 7. Override Register & Monitoring Dashboard

### 7.1 Override Register Location

**File**: `docs/operations/OVERRIDE_REGISTER.md` (centralized tracking)

**Template**:
```markdown
# Manual Overrides Register

## Active Overrides

| ID | Date | Category | Requester | Approver | Impact | Status | Expiry | Review Date | Notes |
|---|---|---|---|---|---|---|---|---|---|
| OR-001 | 2026-03-19 | KAM | Operations | Sales Mgr | $250K | Active | 2026-06-30 | 2026-06-15 | Customer merger consolidation |
| OR-002 | 2026-03-18 | Default Rate | Risk | CFO | $1.5M | Active | 2026-06-30 | 2026-06-15 | Market stress scenario |

## Expired/Removed Overrides

| ID | Category | Duration | Final Status | Outcome Notes |
|---|---|---|---|---|
| OR-000 | Industry | 2025-12-01 → 2026-03-01 | Removed | Rule changed permanently; 5 similar requests identified |
```

### 7.2 Monitoring Dashboard

**Location**: Grafana / Risk Dashboard  
**Metrics**:
- Total active overrides (count + trend)
- Override impact by category (stacked bar)
- Overrides by expiry date (30/60/90 day horizon)
- Approval time (days to approval, by tier)
- Red_flag override incidents (trend)

**Alerts**:
- Override approved without proper authority (red alert)
- Override expired but not removed (yellow, 7-day snooze)
- Same override request 3+ times (yellow, triggers rule review)

---

## 8. Training & Governance

### 8.1 Mandatory Training

| Audience | Training | Frequency |
|----------|----------|-----------|
| All employees with override access | Manual Overrides 101 (procedures, approval matrix) | Annually + on-boarding |
| Approval signers (Sales Mgr, Risk, CFO) | Override governance & risk implications | Annually |
| Internal Audit & Compliance | Override audit procedures & red flag detection | Annually |
| Board Risk Committee | Strategic overrides case studies & approval framework | Quarterly |

### 8.2 Control Self-Assessment

**Quarterly**: Teams perform control self-assessment on overrides under their authority.

| Question | Owner | Evidence |
|----------|-------|----------|
| Are all active overrides approved and documented? | Data Governance | Override register snapshot |
| Have all expired overrides been removed? | Risk Operations | Diff between current & prior quarter |
| Was approval timeline met (per tier)? | Compliance | Email timestamps / override form |
| Any unauthorized override attempts detected? | IT Security / Audit | Access logs for CSV & config files |

---

## 9. Integration with Other Governance Frameworks

### 9.1 Relationship to Change Control
- Manual overrides are changes to system behavior
- Low-impact overrides (KAM correction) → don't require formal change request
- Medium/high-impact overrides (threshold change) → formal change request required (link to RFC #)
- Overrides > $5M → also require CAB (Change Advisory Board) review

### 9.2 Relationship to Data Governance
- Overrides stored in version-controlled files (CSV, YAML) = part of SSOT
- Weekly reconciliation: What's in override register vs. what's in production CSV?
- Lineage: Override impact should be traced through KPI calculations
- PII: No override can contain raw customer PII (use codes instead)

### 9.3 Relationship to Risk Management
- Override risk matrix: Impact × Likelihood of misapplication
- Risk tolerance: How many simultaneous overrides acceptable?
- Concentration risk: Are overrides clustered in one portfolio segment?
- Compliance risk: Do overrides conflict with regulatory requirements?

---

## 10. Enforcement & Consequences

### 10.1 Compliance Validation

**Automated Checks** (run daily):
- ✅ All override_reason fields populated
- ✅ All approved_by fields present
- ✅ No overrides missing effective_date
- ✅ Approval authority matches MATRIX (role-based validation)
- ✅ No duplicate cod_cliente entries in override CSV
- ✅ Override git commit exists for each active override

**Failure Response**:
- Automated alert to Risk@companyemail; Slack #risk-alerts
- Manual reconciliation within 24 hours

### 10.2 Violations & Consequences

| Violation | Severity | Consequence | Owner |
|-----------|----------|-------------|-------|
| Unauthorized override (no approval) | HIGH | Data integrity incident; revert immediately; HR review | Chief Data Officer |
| Expired override not removed | MEDIUM | Yellow flag; weekly escalation until corrected | Risk Manager |
| Override without documented reason | MEDIUM | Compliance finding; correct within 5 days | Data Governance |
| Approval by unauthorized person | HIGH | Revert override; audit person's access; HR review | Compliance Officer |
| Override impact >2x projection (unmitigated) | HIGH | Emergency risk committee; mitigation plan within 2 days | CRO |
| Same request denied 3+ times; then approved via override | MEDIUM | Escalate for rule change discussion | Risk Manager |

---

## 11. Policy Review & Updates

**Annual Review**: 
- Audit Committee reviews this policy
- Assess: Are overrides still necessary? Are approval tiers correct?
- Recommend: Updates based on lessons learned

**Trigger-Based Review**:
- After any HIGH severity violation → immediate policy review
- If >50% of overrides in one category → assess whether rule should change
- If >20 simultaneous overrides → assess capacity to manage risk

**Version Control**:
- This policy maintained in `docs/MANUAL_OVERRIDES_GOVERNANCE.md`
- All changes committed to git with approval
- Changelog maintained at top of this file

---

## Changelog

| Date | Change | Author | Approval |
|---|---|---|---|
| 2026-03-19 | **Initial release** - Comprehensive governance framework for manual overrides. Establishes three-tier approval process, audit requirements, procedures for specific override types, compliance validation. | Data Governance | CRO, CFO |

---

## Appendices

### Appendix A: Approval Matrix Template

```
OVERRIDE APPROVAL MATRIX (Abaco Loans Analytics)
Updated: 2026-03-19

Legend:
- A = Can approve
- N = Must notify
- C = Can comment (no approval)
- × = Not involved

OPERATIONAL OVERRIDES (Impact < $100K)
|-|-Requester-|-Team Lead-|-Risk Manager-|-Finance-|-CFO-|-Board-|
|KAM Assignment|A|A|N|×|×|×|
|Name Normalization|A|A|N|×|×|×|
|Customer ID Correction|A|×|A|N|×|×|

MATERIAL OVERRIDES (Impact $100K - $1M)
|Status Mapping Exception|N|N|A|C|×|×|
|SLA Threshold Adjustment|N|×|A|A|C|×|
|Industry Reclassification|N|N|A|C|C|×|

STRATEGIC OVERRIDES (Impact > $1M)
|Default Rate Threshold Change|N|×|A|A|A|×|
|Concentration Limit Increase|×|×|A|A|A|A|
|Business Rule Change|×|×|A|A|A|A|
```

### Appendix B: Risk Tolerance Statement

```
Manual Overrides Risk Tolerance (Board approved, 2026-Q1)

1. Total active overrides shall not exceed 25 simultaneously
2. No single customer override > $5M without Board approval
3. Combined override impact (all Tier 2/3) ≤ 10% of portfolio AUM
4. Overrides must have defined expiry (no indefinite exceptions except documented rule changes)
5. Same override category >3 times in 90 days → triggers rule change discussion
```

---

**Document Prepared By**: Data Governance Team  
**Effective**: 2026-03-19  
**Next Review**: 2027-Q1
