# Vibe Solutioning: Fintech Factory Governance Framework

## Overview

**Vibe Solutioning** is Abaco Capital's engineering philosophy transforming from **fragile magic to robust, predictable excellence**. This framework establishes the governance, compliance, and operational systems for production-grade fintech software.

**The Fintech Factory**: Money as raw material flowing through an intelligent assembly line, guided by AI agents, enforced by Code is Law principles.

## Core Philosophy

### Three Pillars

1. **Zero Tolerance for Fragility**
   - No syntax errors
   - No infinite loops
   - No incomplete code
   - No unhandled edge cases
   - Production-ready from day one

2. **Traceability is King**
   - Every financial decision must be traceable to the exact code/data source
   - Comprehensive audit trails
   - Deterministic computations (no floating-point for currency)
   - Immutable event logs

3. **Code is Law**
   - Compliance embedded, not retrofitted
   - Governance enforced by CI/CD pipeline
   - Human review as fallback, automation as primary
   - Regulatory requirements hardcoded

## Governance Stack

### 1. Compliance Automation (`.github/workflows/compliance.yml`)

**Purpose**: Enforce governance rules on every commit and pull request.

**Triggers**:

- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`
- Weekly compliance audit (every Sunday)

**Jobs**:

#### Compliance Checks

- CodeRabbit analysis (assertive profile, strict mode)
- Audit trail generation
- Secret detection (no hardcoded credentials)
- Sourcery compliance checks
- Financial data validation (Decimal enforcement)
- Traceability verification

#### SonarQube Quality Gates

- Code metrics and coverage
- Quality gate enforcement (zero critical issues)
- > 90% test coverage requirement

#### Security & Dependency Audit

- Vulnerable dependency detection
- Dependabot result integration

#### Compliance Reporting

- Automated PR comments with compliance status
- Artifact uploads (90-day retention)
- CI/CD dashboard integration

### 2. Code Quality Configuration (`.coderabbit.yaml`)

**Profile**: `assertive`

- Real-time code reviews
- Request changes on violations
- High-level summaries
- Collapse walkthroughs
- Auto-review enabled

**Enforcement by Path**:

```yaml
src/payments/**:
  - CRITICAL: Verify idempotency keys are checked
  - CRITICAL: Ensure ISO 4217 currency codes
  - SECURITY: No raw SQL; use ORM parameterization
  - COMPLIANCE: Do not log PII (name, document number, PAN, CVV)

src/auth/**:
  - SECURITY: Verify JWT signature validation
  - COMPLIANCE: Ensure logging excludes 'password', 'token', 'cvv'
  - COMPLIANCE: Ensure password hashing uses modern algorithms

src/inference/**:
  - DATA: Record inference input hash and model version for auditability
  - SAFETY: Log only feature vectors (no raw PII)
```

### 3. Refactoring Rules (`.sourcery.yaml`)

**Principles**:

- Rank-ordering + survival analysis pattern for complex models
- State must be per-platform (not global)
- Lint mode enabled (detect issues without fix)
- Test command integration

### 4. Audit Trail Generation (`scripts/generate_audit_log.sh`)

**Output**: `audit_log.json` (90-day retention)

**Metadata**:

```json
{
  "generated_at": "2024-01-15T14:30:45Z",
  "commit_sha": "abc123def456...",
  "branch": "feature/new-agent",
  "pull_request": 42,
  "repository": "Abaco-Technol/abaco-loans-analytics",
  "actor": "developer@abaco.com",
  "workflow_run_id": "9123456789",
  "compliance_framework": "Vibe Solutioning"
}
```

**Events Tracked**:

- `code_quality_violation`: Financial float vs Decimal
- `security_violation`: Hardcoded secrets detected
- `fragility_violation`: eval(), bare except, etc.
- `code_maturity`: TODO/FIXME markers
- `traceability_check`: Audit logging in critical operations
- `workflow_start/end`: Audit execution lifecycle

## Nine Autonomous Agents

### Agent Contracts

| Agent          | Primary Duty                             | Governance                           |
| -------------- | ---------------------------------------- | ------------------------------------ |
| **Founder**    | Business metrics & OKRs                  | Quarterly reviews, KPI dashboards    |
| **Investor**   | Capital allocation & returns             | Monthly P&L, IRR tracking            |
| **CTO**        | Technical architecture & velocity        | Sprint planning, tech debt backlog   |
| **Compliance** | Regulatory adherence & audits            | Real-time governance enforcement     |
| **Fraud**      | Transaction analysis & anomaly detection | Daily model retraining, 99.5% recall |
| **Growth**     | Acquisition & retention metrics          | Weekly cohort analysis               |
| **Risk**       | Portfolio risk & stress testing          | Daily VaR calculations               |
| **Integrator** | Platform connections & APIs              | Token management, sync logs          |
| **MLOps**      | Model lifecycle & experimentation        | CI/CD for models, auto-retraining    |

### Event Subscriptions

All agents subscribe to **Kafka topics** by type:

- `financial.transaction` → Fraud, Compliance, Risk
- `user.lifecycle` → Growth, Investor
- `system.deployment` → CTO, MLOps
- `external.sync` → Integrator

## Integrations Page

### Purpose

Manage API tokens for external platforms (Meta, LinkedIn, custom APIs) with:

- Encrypted storage (AES-256-GCM)
- Per-platform token isolation
- Automatic sync logging
- Error handling & retry logic

### Token Lifecycle

1. **Validation**: Test token before storing
2. **Encryption**: AES-256-GCM with KMS in production
3. **Storage**: Supabase encrypted columns
4. **Sync**: Background worker with exponential backoff
5. **Audit**: All operations logged to `sync_logs` table

### Critical Rules

❌ **NEVER**:

- Store tokens in plaintext
- Commit .env files
- Use eval() for token validation
- Share state across platforms

✅ **ALWAYS**:

- Validate provider tokens before storing
- Log all integration events
- Implement exponential backoff (3 retry attempts)
- Test with real provider APIs
- Document business rationale
- Handle partial failures explicitly

## Deployment Pipeline

```
┌─────────────────────────────────────────────┐
│ Developer commits code                      │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────┐
│ Compliance.yml workflow triggers            │
│  - CodeRabbit analysis                      │
│  - SonarQube scan                           │
│  - Audit trail generation                   │
│  - Security checks                          │
└────────────┬────────────────────────────────┘
             │
             ▼
         ┌───────┐
         │ PASS? │
         └───┬───┘
             │
        NO   │   YES
        ┌────┘────┐
        │         │
        ▼         ▼
      BLOCK    REVIEW
             (Human)
             └────┬──┘
                  │
                  ▼
         ┌─────────────────┐
         │ Auto-merge      │
         │ (main branch)   │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Deploy          │
         │ (Staging/Prod)  │
         └─────────────────┘
```

## Financial Data Requirements

### Currency Handling

✅ **CORRECT**:

```python
from decimal import Decimal
amount = Decimal('1234.56')  # Always use Decimal for currency
rate = Decimal('0.05')       # Interest rates too
```

❌ **WRONG**:

```python
amount = 1234.56         # Float causes rounding errors
rate = 0.05              # Currency precision loss
```

### Idempotency Keys

All payments must include an idempotency key:

```python
idempotency_key = f"{user_id}_{timestamp}_{operation_id}"
# Ensures no duplicate charges if retry occurs
```

## Compliance Checklist

Before every commit:

- [ ] All financial calculations use `Decimal` (not float)
- [ ] Payment operations have idempotency keys
- [ ] No hardcoded secrets (passwords, API keys, tokens)
- [ ] PII logging excluded (name, document number, account number)
- [ ] Database queries use ORM parameterization (no raw SQL)
- [ ] Error messages don't expose sensitive details
- [ ] Audit trail logs include: timestamp, user, action, result
- [ ] Critical operations have retry logic with backoff
- [ ] Edge cases handled explicitly (not silently ignored)

## Environment Configuration

### GitHub Secrets (Required)

```bash
SONARQUBE_TOKEN        # SonarQube authentication
SOURCERY_TOKEN         # Sourcery refactoring service
CODERABBIT_TOKEN       # CodeRabbit code review
SUPABASE_SERVICE_KEY   # Supabase edge function deployment
KMS_ENCRYPTION_KEY     # Token encryption key

### Branch Protection (main)

- Require pull request reviews (1+ approver)
- Dismiss stale PR approvals on new commits
- Require status checks pass:
  - `compliance-checks`
  - `sonar-analysis`
  - `dependency-check`
- Require branches be up to date before merging
- Include administrators in restrictions

## Ownership & Reviews

- Workflow and secrets ownership is tracked in `docs/workflow-ownership.md`; updates to CI/CD, compliance, or deploy workflows require approval from the documented owners.
- Data/analytics changes (ingestion, transformation, KPI) must be reviewed by the Data/Analytics owner; security/compliance changes require the Security/Compliance owner; frontend CI changes require the Frontend owner.
- Secrets usage must be justified in PR descriptions and reviewed by the responsible owner before merge.

## Monitoring & Alerts

### Dashboards

- **Compliance Dashboard**: Real-time governance status
- **KPI Dashboard**: Business metrics by stakeholder
- **Audit Trail**: Searchable event log (Ctrl+F by event type)
- **Agent Status**: Health checks and message queue depth

### Dashboard Stack & Progress

| Component             | Status        | Files                                                                 |
|----------------------|---------------|-----------------------------------------------------------------------|
| **Authentication**   | ✅ Production | Auth UI components, Login/SignUp/Password reset forms                 |
| **Financial Dashboard** | ✅ Live    | `/app/dashboard/financial/` with 4 dashboard cards                    |
| **API Endpoint**      | ✅ Live       | `/api/financial-intelligence/route.ts` with timing metadata          |
| **UI Components**     | ✅ Complete   | Radix UI + custom ABACO design system                                 |
| **Data Visualization**| ✅ Live       | Charts, metrics cards, risk analysis cards                            |

Key Dashboard Components:
- `FinancialMetrics.tsx` – Live KPI cards with formatting
- `GrowthChart.tsx` – SVG area chart with 12-month trends
- `RiskAnalysis.tsx` – VaR, sector exposures, stress scenarios
- `AIInsights.tsx` – Provider health + confidence scoring

### Alerts

- Critical compliance violations → Slack #security
- Failed SonarQube quality gate → Slack #engineering
- Audit log failures → Slack #devops
- Agent heartbeat missing → Slack #ops

### ML Stack & Progress

| Layer              | Status        | Details                                                                    |
|--------------------|---------------|----------------------------------------------------------------------------|
| **Database Schema** | ✅            | 4 tables: predictions, feedback, weight_adjustments, learning_metrics        |
| **ML Types**        | ✅            | `types/ml.ts` with Zod schemas for validation                              |
| **Prediction API**  | ✅            | `/api/ml/predictions/route.ts` (POST + GET)                                 |
| **Feedback API**    | ✅            | `/api/ml/feedback/route.ts` (POST + GET)                                     |
| **Integration Layer** | ✅          | Base integration + Grok (xAI) integration with fallbacks                   |
| **Learning Engine** | ✅            | `lib/ml/continue-learning.ts` with Brier score & accuracy metrics           |
| **Test Suite**      | ✅            | 16 comprehensive test files covering all layers                            |

### Data & Integration Layer (90% Complete)

| Component                      | Status | Details                                                                        |
|--------------------------------|--------|--------------------------------------------------------------------------------|
| **Supabase Client**            | ✅     | SSR-enabled with cookies, auth context                                         |
| **Financial Intelligence Dataset** | ✅ | Canonical dataset in `lib/data/financial-intelligence.ts`                     |
| **Risk Indicators**            | ✅     | `lib/risk-indicators.ts` with portfolio analysis                               |
| **AI Integrations**            | ✅     | xAI Grok + OpenAI with fallback chains                                         |
| **Base Integrations**          | ✅     | Rate limiting (5 rps), exponential backoff, timeout handling                   |

### Testing Infrastructure (Mature)

**MVP 16 test files covering:**
- **ML Layer** (`lib/ml/*`)
- **Integrations** (`lib/integrations/*`)
- **Supabase clients** (`lib/supabase/*`)
- **Components** (Auth forms, UI components)
- **Risk indicators**
- **API endpoints** (`/app/api/*`)

**Test Framework**: Jest + React Testing Library

## How to Use

### Creating a Feature

1. Branch from `main`
2. Implement feature with full traceability
3. Submit PR (auto-trigger compliance workflow)
4. Address compliance violations if any
5. Get human review + auto-merge on pass

### Debugging Compliance Failures

1. Check PR compliance comment for violation type
2. Review `audit_log.json` artifact (90-day retention)
3. Look at CodeRabbit/SonarQube reports
4. Fix violation and re-push (auto-retry)

### Releasing to Production

1. Ensure all PRs merged to `main`
2. Tag release: `git tag v1.2.3`
3. Deployment workflow triggers automatically
4. Compliance gates must pass before production
5. Rollback if audit trail shows critical issues

## References

- [Compliance Automation](.github/workflows/compliance.yml)
- [CodeRabbit Config](.coderabbit.yaml)
- [Sourcery Config](.sourcery.yaml)
- [Audit Log Generator](scripts/generate_audit_log.sh)
- [CI/CD Pipeline](docs/DEPLOYMENT.md)
```
