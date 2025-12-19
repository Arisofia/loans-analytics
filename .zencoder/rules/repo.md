---
description: Repository Information Overview
alwaysApply: true
---

# Repository Information Overview

## Repository Summary

Abaco Loans Analytics is a multi-language monorepo containing a Next.js web dashboard, Python-based analytics pipelines, a Streamlit dashboard, and integration services. It uses TypeScript for frontend and services, and Python for data processing and analytics.

## Repository Structure

- **apps/web**: Next.js frontend application (Web Dashboard).
- **apps/analytics**: Python-based analytics engine and pipelines.
- **streamlit_app**: Streamlit dashboard for data visualization.
- **services**: TypeScript integration services (HubSpot, Slack).
- **python**: Core Python logic, ingestion, and KPI engine scripts.
- **docs**: Extensive project documentation.
- **infra**: Infrastructure configuration (Azure).

## Projects

### Web Dashboard (Next.js)

Located in `apps/web` (and root configuration).

#### Language & Runtime

**Language**: TypeScript, Node.js (v20-alpine in Docker)
**Framework**: Next.js 16, React 19
**Build System**: npm

#### Dependencies

**Main Dependencies**:

- next
- react, react-dom
- zod
- @supabase/supabase-js
- @vercel/analytics

**Development Dependencies**:

- typescript
- @types/node, @types/react
- @azure/static-web-apps-cli

#### Build & Installation

```bash
# Install dependencies
npm install --prefix apps/web

# Build application
npm run build --prefix apps/web

# Start application
npm start --prefix apps/web
```

#### Docker

**Dockerfile**: `./Dockerfile`
**Image**: `node:20-alpine`
**Configuration**: Multi-stage build (builder -> production). Runs as non-root user `nextjs`. Exposes port 3000.

### Analytics Engine

Located in `apps/analytics`.

#### Language & Runtime

**Language**: Python
**Version**: 3.9+ (implied by `pyproject.toml`)

#### Dependencies

**Main Dependencies**:

- pandas
- numpy
- azure-storage-blob
- azure-identity

**Development Dependencies**:

- pytest
- pytest-cov

#### Testing

**Framework**: Pytest
**Test Location**: `apps/analytics/tests`
**Naming Convention**: `test_*.py`

**Run Command**:

```bash
pytest apps/analytics/tests
```

### Streamlit Dashboard

Located in `streamlit_app` and root.

#### Language & Runtime

**Language**: Python

#### Dependencies

**Main Dependencies** (from root `requirements.txt`):

- streamlit
- pandas, numpy
- altair, plotly
- jinja2

#### Usage

**Entry Point**: `streamlit_app/app.py` or `streamlit_app.py` (root)

### Integration Services

Located in `services/`.

#### HubSpot Sync

**Location**: `services/hubspot_sync`
**Language**: TypeScript
**Dependencies**: `axios`
**Build**: `npm run build --prefix services/hubspot_sync`

#### Slack Bot

**Location**: `services/slack_bot`
**Language**: TypeScript
**Dependencies**: `@slack/bolt`, `axios`
**Build**: `npm run build --prefix services/slack_bot`

### Database & SQL

Located in `sql/`.

- **Migrations**: `sql/migrations/`
- **Calculations**: `sql/calculations/` (Collection rate, compliance metrics, PAR 90)
- **Views**: `v_portfolio_risk.sql`

### CI/CD & Automation

Located in `.github/workflows/`.

- **CI**: `ci.yml` (Main CI pipeline), `codeql.yml`, `snyk.yml`, `sonarqube.yml`
- **Deployment**: `deploy.yml`, `azure-static-web-apps-*.yml`
- **PR Automation**: `pr-auto-assign.yml`, `auto-close-stale-prs.yml`, `codex-pull-request-review.yml`

### Repository Tools

#### Deno Helper

**File**: `main.ts`
**Purpose**: Repository layout checker and validation tool.
**Usage**:

```bash
deno run --allow-read main.ts
```

#### Java Configuration (Inactive?)

**File**: `build.gradle`
**Details**: Configures a Spring Boot 3.1.12 application (`com.abaco.loans.Application`), but no Java source files were found in the repository.
