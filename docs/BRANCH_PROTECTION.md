# Branch Protection Requirements for Multi-Agent System

This document outlines the required branch protection rules for the Abaco Loans Analytics repository to ensure quality gates are enforced.

## Required Status Checks

The following status checks must pass before merging to `main`:

### F1: Multi-Agent Tests
- **Workflow**: `Multi-Agent Tests` (multi-agent-tests.yml)
- **Purpose**: Ensures all agent orchestration, protocol, and scenario tests pass
- **Required for**: All PRs affecting `src/agents/**` or `tests/agents/**`
- **Coverage Target**: 85%+ for agent code

### F2: Cost Regression Detection
- **Workflow**: `Cost Regression Detection` (cost-regression-detection.yml)
- **Purpose**: Detects cost regressions in token usage and API calls
- **Required for**: All PRs affecting `src/agents/**`
- **Alert Threshold**: 10% increase over baseline

### F3: Security & Quality Gates

#### Agent Checklist Validation
- **Workflow**: `Agent Code Checklist` (agent-checklist-validation.yml)
- **Purpose**: Validates agent implementation against required checklist
- **Required for**: All PRs affecting `src/agents/**`

#### CodeQL Security Scan
- **Workflow**: `CodeQL Analysis` (codeql.yml)
- **Purpose**: Scans for security vulnerabilities with LLM-specific rules
- **Required for**: All PRs affecting code
- **Severity**: Must resolve all Critical and High severity issues

#### SonarQube Quality Gate
- **Workflow**: `SonarQube` (sonarqube.yml)
- **Purpose**: Enforces code quality standards
- **Required for**: All PRs
- **Standards**: 
  - No critical bugs
  - No blockers
  - Technical debt ratio < 5%

### F4: Performance Monitoring

#### Smoke Tests
- **Workflow**: `Smoke Tests` (smoke-tests.yml)
- **Purpose**: Validates system health and basic functionality
- **Runs**: On schedule (every 30 minutes) and on-demand
- **Not blocking**: Informational, alerts on failure

#### Performance Monitoring
- **Workflow**: `Performance Monitoring` (performance-monitoring.yml)
- **Purpose**: Tracks latency and performance metrics
- **Required for**: All PRs affecting `src/agents/**`
- **P99 Target**: < 200ms for agent operations

### Additional Required Checks

#### Code Review
- **Requirement**: At least 1 approval from code owners
- **Code Owners**: See `.github/CODEOWNERS`

#### CI Pipeline
- **Workflow**: `CI` (ci.yml)
- **Checks**:
  - Code formatting (black, isort)
  - Linting (ruff, flake8)
  - Type checking (mypy)
  - Unit tests

## Configuring Branch Protection

To configure these rules in GitHub:

1. Navigate to **Settings** → **Branches** → **Branch protection rules**
2. Add rule for branch pattern: `main`
3. Enable the following:

### Protect matching branches
- ✅ Require a pull request before merging
  - ✅ Require approvals: 1
  - ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
  - ✅ Require branches to be up to date before merging
  - **Required status checks**:
    - `Multi-Agent Tests / test (3.11)`
    - `Multi-Agent Tests / test (3.12)`
    - `Cost Regression Detection / cost-benchmark`
    - `Agent Code Checklist / checklist`
    - `CodeQL Analysis / analyze (python)`
    - `SonarQube / sonarqube`
    - `CI / quality`
- ✅ Require conversation resolution before merging
- ✅ Require signed commits (optional)
- ✅ Include administrators (optional)
- ✅ Restrict who can push to matching branches (optional)

## Override Procedures

In emergency situations, administrators may bypass these requirements, but must:

1. Document the reason in the PR description
2. Create a follow-up issue to address skipped checks
3. Notify the team via Slack/Teams
4. Schedule a post-incident review

## Updating Requirements

Changes to branch protection requirements must be:

1. Proposed via RFC (Request for Comments) issue
2. Reviewed by engineering leads
3. Approved by at least 2 code owners
4. Documented in this file
5. Communicated to all team members

## Monitoring and Alerts

- **Slack/Teams Notifications**: Failed status checks post to `#eng-alerts`
- **Email Alerts**: Critical security findings sent to security team
- **Dashboard**: View status at [CI Dashboard URL]

## Related Documentation

- [Agent Implementation Checklist](../docs/agent-implementation-checklist.md)
- [Cost Optimization Guide](../docs/cost-optimization.md)
- [Performance Benchmarks](../docs/performance-benchmarks.md)
- [Security Guidelines](../SECURITY.md)

---

**Last Updated**: 2026-01-28  
**Owner**: Engineering Team  
**Review Frequency**: Quarterly
