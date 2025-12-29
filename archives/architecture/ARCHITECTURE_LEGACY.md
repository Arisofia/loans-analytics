# DO NOT USE IN PRODUCTION
# Legacy architecture snapshot. Superseded by docs/ARCHITECTURE.md.

# Fintech Factory - Complete Architecture Specification

## Executive Summary

The Fintech Factory is an **agentic fintech ecosystem** designed for autonomous portfolio intelligence and stakeholder-specific insights. Built on **Vibe Solutioning** principles, it guarantees:

- **100% deterministic design**: All KPIs recomputed from base data (no upstream computed fields)
- **Zero-touch automation**: Agents operate without human intervention loops
- **Full traceability**: Every metric includes run ID, timestamp, and data version
- **7 departmental stacks**: Risk, Growth, Finance, Compliance, Technology, Marketing, Sales
- **9 integrated agents**: Codex, SonarQube, Black, Flake8, PyTest, CodeRabbit, Sourcery, MCP, Gap Resolver
- **Multi-stakeholder outputs**: Executive dashboards, investor decks, compliance reports, etc.

## Repository Structure (10 Sections)

### 1. DATA LAYER (`/data`)

Source of truth for all KPI calculations

- `raw/cascade/` - Raw exports from Cascade Debt platform
- `warehouse/` - Computed metrics in BigQuery
- `snapshots/` - Daily immutable snapshots for regression testing
- `validation/` - Data quality checks and anomaly detection

### 2. ACCESS & CREDENTIALS (`/config/access`)

Secure integration with external systems

- `secrets.example.yaml` - Template for credentials (never committed)
- `integrations/` - OAuth, API keys, service accounts
- `roles.yaml` - IAM policies and access control

### 3. KPI & SCHEMA (`/config/kpis`, `/config/schemas`)

Business logic definitions

- `kpi_definitions.yaml` - All 20+ KPI formulas with thresholds
- `data_schemas/` - Loan, client, transaction data models
- `validation_rules.yaml` - Data quality gates

### 4. POLYGLOT CODEBASE

**Python** (`/python`)

- `ingestion/` - Cascade data extraction
- `transform/` - KPI calculation engines
- `models/` - Pandas DataFrames for analysis
- `agents/` - Agent integrations
- `reporting/` - Output generators

**Node.js/TypeScript** (`/services`)

- `slack_bot/` - Real-time alerts
- `hubspot_sync/` - CRM integration
- `meta_business/` - Advertising sync
- `webhooks/` - Event handlers

**Kotlin** (`/kotlin`)

- Core microservices for high-throughput operations

**SQL** (`/sql/models`)

- BigQuery views for dimensional analytics

### 5. AGENTS & ORCHESTRATION

**Agent Specs** (`/config/agents/specs`)

- `risk_agent.yaml` - Portfolio risk monitoring
- `growth_agent.yaml` - Origination tracking
- `compliance_agent.yaml` - Audit automation
- Additional specialized agents

**Orchestration** (`/config/orchestration`)

- `daily_pipeline.yaml` - 24-hour workflow
- `weekly_reports.yaml` - Departmental summaries
- `monthly_investor_package.yaml` - Board deliverables

### 6. KNOWLEDGE & BRANDING

**Business Context** (`/docs/knowledge`)

- Fintech industry playbooks
- Portfolio management best practices
- Regulatory framework documentation

**Brand Assets** (`/docs/branding`)

- Logo, colors, fonts
- Report templates (PDF, HTML, Markdown)

### 7. DASHBOARDS & VISUALIZATION

**Web Dashboards** (`/dashboards`)

- Executive dashboard (HTML/React)
- Risk monitoring (Grafana)
- Growth metrics (Metabase)

**PDF Reports** (`/templates/reports`)

- Investor deck template
- Committee briefs
- Monthly compliance report

### 8. COMPLIANCE & AUDIT

**Audit Trail** (`/audit`)

- Complete transaction log
- Change tracking
- Regulatory reporting

**Policies** (`/compliance`)

- Data retention policy
- Privacy & security
- Regulatory requirements

### 9. DOCUMENTATION & RUNBOOKS

**Guides** (`/docs`)

- Architecture overview
- Agent deployment guide
- Integration setup instructions
- Troubleshooting playbooks

**Runbooks** (`/docs/runbooks`)

- Daily health checks
- Incident response
- Escalation procedures

### 10. OUTPUT TEMPLATES

**Multi-Format Exports** (`/templates`)

- Notion page templates
- Slack message formats
- Email templates
- API response schemas

## Departmental Intelligence Stacks

### Risk Stack

**Agents**: Risk Analyst, Prediction Engine
**KPIs**: PAR_90, RDR_90, Portfolio Health, Collection Rate
**Outputs**: Daily alerts, Weekly deep dive, Monthly trend analysis

### Growth Stack

**Agents**: Growth Optimizer, Market Analyzer
**KPIs**: Origination Volume, Active Clients, Retention Rate
**Outputs**: Daily metrics, Opportunity brief, Growth deck

### Finance Stack

**Agents**: Finance Controller, ARR Optimizer
**KPIs**: ARR, Write-Off Rate, Revenue Forecast
**Outputs**: Cash flow report, Forecast, Board package

### Compliance Stack

**Agents**: Audit Enforcer, Regulatory Bot
**KPIs**: Active Audit Flags, Data Quality Score
**Outputs**: Hourly alerts, Daily audit log, Monthly compliance report

### Technology Stack

**Agents**: System Monitor, Performance Optimizer
**KPIs**: Data Quality, System Uptime
**Outputs**: Real-time metrics, Tech digest, Architecture review

### Marketing Stack

**Agents**: Campaign Optimizer, Segment Analyzer
**KPIs**: Origination Volume, Customer Acquisition Cost
**Outputs**: Campaign metrics, Marketing brief, Exec summary

### Sales Stack

**Agents**: Pipeline Tracker, Deal Optimizer
**KPIs**: Origination Volume, Retention, Avg Loan Size
**Outputs**: Daily pipeline, Deals update, Compensation

## Integration Ecosystem

- **Cascade Debt**: Loan data source (CSV/JSON exports)
- **Notion**: Collaborative workspace & database
- **Slack**: Real-time alerts & notifications
- **HubSpot**: CRM & sales pipeline
- **Meta**: Advertising & campaign tracking
- **Azure**: Cloud infrastructure
- **Google Workspace**: Documentation & collaboration
- **Figma**: Design & presentation templates

## Deployment Phases

### Phase 1: Foundation (Week 1-2)

- Set up PostgreSQL, BigQuery, Airflow
- Configure Cascade data ingestion
- Deploy initial KPI calculations

### Phase 2: Integrations (Week 3-4)

- Connect all 8+ external services
- Build alerting system (Slack/Email)
- Test data flows end-to-end

### Phase 3: Agents (Week 5-6)

- Activate departmental stacks
- Enable autonomous workflows
- Configure approval thresholds

### Phase 4: Dashboards (Week 7-8)

- Deploy web visualizations
- Generate static reports
- Enable stakeholder access

## Vibe Solutioning Principles

1. **Rebuild from Base**: Every metric recomputed from raw source data
2. **Continuous Validation**: Regressions, snapshots, and bias detection
3. **Absolute Traceability**: Complete audit trail for every calculation
4. **Stability First**: Deterministic, reproducible results
5. **Excellence Standard**: Outcomes that are superior, professional, robust

## Success Metrics

- ✅ Zero manual data entry required
- ✅ All KPIs validated with > 95% accuracy
- ✅ Stakeholder dashboards updated < 15 minutes after source data
- ✅ Compliance audit flags resolved within SLA
- ✅ Agent automation rate > 90%
