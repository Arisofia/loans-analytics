# Available Tools, Extensions, and Workflow Configuration

## Overview

This document comprehensively catalogs all available tools, extensions, integrations, and workflow patterns discovered from Sourcery diagrams and feedback across the Fintech Factory agent ecosystem. It serves as the canonical reference for building the orchestration layer and configuring agent workflows.

## 1. Infrastructure & Deployment Tools

### 1.1 GitHub Actions
**Status**: Fully Available
**Triggers**: 
- Daily scheduled workflows (e.g., `0 3 * * *` for 03:00 UTC)
- Push events with branch filters
- Pull request events
- Manual dispatch (workflow_dispatch)

**Key Patterns from Sourcery Feedback**:
- Environment variables pulled from GitHub Secrets: `CASCADE_API_KEY`, `CASCADE_PARTNER_ID`
- Git status checks: `git diff --quiet || git commit ...` for conditional commits
- Guard patterns: `git status` checks before executing operations
- Error handling: JSON validation, retry logic with exponential backoff
- Team notifications for repeated failures

**Example Workflow Triggers** (from PR #203):
```yaml
name: Cascade Daily Export
schedule:
  - cron: '0 3 * * *'  # Daily at 03:00 UTC
steps:
  - name: Export Cascade Data
    env:
      CASCADE_API_KEY: ${{ secrets.CASCADE_API_KEY }}
      CASCADE_PARTNER_ID: ${{ secrets.CASCADE_PARTNER_ID }}
    run: |
      # Fetch from Cascade API
      # Validate JSON structure
      # Commit changes if different
```

### 1.2 Vercel Deployment
**Status**: Integrated (currently paused via `vercel.json` with `"disabled": true`)
**Configuration**: Uses `vercel.json` schema version 2
**Known Issues**: 
- Schema validation on `version` field (must be <= 2)
- Requires resolution of `disabled` property support

### 1.3 Azure Blob Storage
**Status**: Fully Available
**Integration Points**:
- KPI data export (`AzureBlobKPIExporter`)
- Portfolio calculations CSV storage
- Validation: `blob_name` must be string type

**Export Contract**:
```python
upload_metrics(metrics_payload: Dict, blob_name: str)
```

## 2. Data Integration & API Tools

### 2.1 Cascade Platform (Debt Analytics)
**Status**: Fully Operational
**Data Export**: Daily via GitHub Actions at 03:00 UTC
**Authentication**: Via GitHub Secrets (`CASCADE_API_KEY`, `CASCADE_PARTNER_ID`)
**Available Views** (from PR #203):
- Portfolio metrics and characteristics
- Delinquency analysis
- Collection data
- Risk metrics
- Abaco risk overview JSON

**Data Quality Checks** (Pre-merge validation):
- Numeric validation (currency, percentages)
- Percentage range validation (0-100%)
- Date format and recency validation
- Null value validation
- **Monotonicity validation**: Customer/loan counts (with exception handling for charge-offs, portfolio run-off)
- Stale data warning if no update > 24 hours

### 2.2 Supabase
**Status**: Fully Integrated
**Configuration**: 
- Client configuration with `isSupabaseConfigured` guard
- Environment variables with trimming/validation
- Fallback behavior when env vars missing

**Available Features**:
- Landing page data fetching with diagnostics
- Schema validation using Zod
- Encrypted columns for sensitive data
- Local development workflow (see `docs/supabase-local.md`)

**Diagnostic Logging**:
- `logLandingPageDiagnostic()` - diagnostic logging for data fetching
- Schema validation errors trigger fallback data

### 2.3 Kafka Event Bus
**Status**: Architecturally Available
**Integration**: Nine autonomous agents subscribe to Kafka event topics
**Message Topics** (from PR #202):
- Compliance events
- Analytics computation events
- Workflow execution events
- Risk alert events

## 3. Quality Assurance & Code Analysis Tools

### 3.1 SonarQube
**Status**: Fully Integrated
**Configuration**:
- Project sources: `apps/`, `streamlit_app/`, `src/`
- Test coverage paths for JS, Python, Java
- SonarCloud integration via GitHub Actions
- Ingestion testing flows for clean analysis
- KPI validation rules

**Coverage Reports**:
- JavaScript/TypeScript: Jest coverage
- Python: pytest coverage with `--cov` flags
- Java: Gradle JUnit Platform coverage

### 3.2 CodeRabbit
**Status**: Fully Integrated
**Role**: Code quality and optimization reviews
**Configuration**: Referenced in compliance automation workflows

### 3.3 Sourcery
**Status**: Fully Integrated
**Role**: AI-powered code refactoring and pattern analysis
**Available Features**:
- Automatic refactoring suggestions
- Architecture diagram generation (Mermaid)
- Workflow sequence diagrams
- Class diagrams for data models
- Flow diagrams for process pipelines

### 3.4 CodeQL
**Status**: Fully Integrated
**Coverage**: Security scanning across Python, JavaScript, Java
**Analysis**: Automatic code scanning on PRs and push events

## 4. Monitoring, Alerting & Observability

### 4.1 Slack Integration
**Status**: Fully Available
**Access**: Via Slack webhooks (configured in `config/integrations/slack.yaml`)
**Message Templates**:
- Alert notifications for workflow failures
- KPI threshold violations
- Data quality issues
- Compliance failures

**Configuration**:
- Webhook URLs stored in GitHub Secrets
- Channel routing based on alert severity
- Throttling rules to prevent alert fatigue

### 4.2 Email Notifications
**Status**: Available
**Use Cases**:
- Team notifications for repeated workflow failures
- Data quality alerts
- Compliance check failures

### 4.3 Custom Dashboards
**Status**: Available via React/Streamlit
**Platforms**:
- Next.js React dashboards (web app)
- Streamlit apps for analytics and monitoring
- Grafana-style KPI visualizations

## 5. Data Quality & Validation Framework

### 5.1 Pre-Merge Data Quality Checks
From PR #203 Sourcery Feedback:

```python
# Numeric validation
- All currency fields must be Decimal type
- Percentage fields: 0 <= value <= 100

# Date validation  
- ISO 8601 format required
- Recency check: data < 24 hours old

# Monotonicity validation (with caveats)
- Customer count should not decrease
- Loan count should not decrease
- EXCEPT: charge-offs, portfolio run-off scenarios

# Null value validation
- Required fields must have non-null values
- Optional fields documented

# Struct validation
- JSON schema validation via Zod
- Field type enforcement
```

### 5.2 Financial Data Requirements
From PR #202 Governance feedback:

**Mandatory Requirements**:
1. **Decimal Usage**: All currency fields MUST use Decimal type (not float)
2. **Idempotency Keys**: Required for all payment operations
   - Format: Stable, operation-derived (NOT timestamp-based)
   - Client responsibility to maintain consistency across retries
   - Recommended: UUID per business operation
3. **Audit Logging**: All sensitive operations must be logged
4. **Encryption**: Sensitive fields in encrypted Supabase columns
5. **KMS Integration**: Key management for sensitive credentials

## 6. Environment Configuration

### 6.1 GitHub Secrets
**Required Secrets** (from PR #202):
- `CASCADE_API_KEY` - Cascade Debt platform authentication
- `CASCADE_PARTNER_ID` - Cascade partner identification
- `SLACK_WEBHOOK_URL` - Slack notifications
- `SONAR_TOKEN` - SonarQube authentication (check spelling)
- `.env.local` and `.vercel` files must be in `.gitignore`

### 6.2 Environment Variable Configuration
**Landing Page Env Vars** (PR #200):
- `NEXT_PUBLIC_ALERT_*` - Alert thresholds
- Supabase configuration variables
- Analytics instrumentation settings

## 7. Sourcery Diagrams & Workflow Patterns

### 7.1 Available Sequence Diagrams
From reviewed PRs:

**PR #203 - Cascade Daily Update**:
1. Sequence diagram: Daily Cascade data update via GitHub Actions
2. Flow diagram: Cascade data quality checks before merge

**PR #202 - Compliance & Governance**:
1. Sequence diagram: Debugging a compliance failure
2. Flow diagram: Vibe Solutioning deployment pipeline

**PR #200 - Analytics Stack**:
1. Sequence diagram: Landing page data fetch with Supabase, diagnostics, SEO JSON-LD
2. Sequence diagram: Streamlit file ingestion, normalization, KPI computation
3. Class diagram: Landing page types and data definitions
4. Flow diagram: GitHub workflow and quality gates from runbook

**PR #199 - Conflict Resolution**:
1. Sequence diagram: pr_status GitHub CLI helper
2. Class diagram: Loan analytics and KPI export

### 7.2 Workflow Orchestration Patterns

**Pattern 1: Daily Data Export** (Cascade, Abaco Risk Analytics)
```
Trigger: Cron schedule @ 03:00 UTC daily
Actions:
  1. Fetch from Cascade/source API
  2. Validate JSON structure
  3. Compute quality metrics
  4. Commit to repo if changed
  5. Alert if stale (> 24 hours)
Output: JSON file in `exports/` directory
```

**Pattern 2: Data Quality Validation**
```
Trigger: PR submission or daily export
Checks:
  1. Type validation (Decimal, string, etc.)
  2. Range validation (percentages 0-100)
  3. Monotonicity (with exception handling)
  4. Null value validation
  5. Date recency check
Result: Pass/Fail with detailed feedback
```

**Pattern 3: Compliance Pipeline**
```
Trigger: Push to main, PR submission
Steps:
  1. SonarQube quality gate check
  2. CodeQL security scan
  3. CodeRabbit code quality review
  4. Sourcery refactoring suggestions
  5. Branch protection enforcement
Result: Auto-approve if all gates pass, request changes if failures
```

## 8. Available Integrations Reference

| Integration | Status | Type | Configuration |
|---|---|---|---|
| Cascade Platform | ✅ Active | Data Source | `config/integrations/cascade.yaml` |
| Slack | ✅ Active | Notification | Webhook via GitHub Secrets |
| HubSpot | ✅ Available | CRM | API token in GitHub Secrets |
| Notion | ✅ Available | Knowledge Base | Database credentials |
| SonarQube | ✅ Active | QA | `sonar-project.properties` |
| CodeRabbit | ✅ Active | QA | Automatic on PRs |
| Sourcery | ✅ Active | QA | Bot integration |
| CodeQL | ✅ Active | Security | GitHub Actions workflow |
| Vercel | ⏸️ Paused | Deployment | `vercel.json` config |
| Azure Blob | ✅ Active | Storage | Service principal auth |
| Supabase | ✅ Active | Database | Connection string in env |
| Kafka | 🏗️ Ready | Event Bus | Topic subscriptions for agents |

## 9. Building the Orchestration Layer

### 9.1 Required Components

**Agent Orchestrator**:
- Manages all 9 agents (Risk, Growth, Compliance, Tech, Finance, Sales, Customer, Market, Portfolio)
- Subscribes to Kafka events
- Executes workflows based on triggers and schedules
- Handles error recovery and retries

**Trigger Resolver**:
- Parses cron schedules (daily, weekly, monthly)
- Monitors external events (Cascade export completion, data quality failures)
- Manages manual triggers via GitHub Actions

**Data Quality Engine**:
- Applies pre-merge validations
- Enforces Decimal/idempotency requirements
- Triggers alerts on violations

**Notification Service**:
- Routes alerts to Slack/email
- Manages throttling and deduplication
- Maintains audit trail

### 9.2 Workflow Configuration Format

```yaml
agent:
  name: Risk Agent
  triggers:
    - type: schedule
      cron: '0 * * * *'  # Hourly
    - type: event
      topic: 'cascade.export.complete'
  
  actions:
    - fetch_cascade_data
    - compute_risk_metrics
    - validate_quality
    - export_to_blob_storage
    - notify_slack
  
  error_handling:
    retry_count: 3
    retry_delay_ms: 5000
    on_failure: 'notify_team'
```

## 10. Next Steps

1. **Create Agent Orchestrator** - Main entry point for all 9 agents
2. **Implement Workflow DAGs** - Using Airflow or native Python scheduler
3. **Deploy Kafka Topics** - Set up event subscriptions for agents
4. **Configure Secrets** - Populate GitHub Secrets for all integrations
5. **Create Monitoring Dashboards** - Wire up SonarQube, custom KPI boards
6. **Document Runbooks** - Add troubleshooting and rollback procedures
7. **Enable Auto-scaling** - Configure based on event volume and compute needs

---

**Last Updated**: 2025-12-05
**Source PRs**: #210, #211, #212, #202, #203, #200, #199
**Reviewed by**: Sourcery AI, Architecture Review
