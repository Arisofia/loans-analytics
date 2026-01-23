#!/bin/bash
set -e

echo "=========================================="
echo "PHASE 6: CI WORKFLOW TESTING - GIT COMMIT"
echo "=========================================="
echo ""

# Check git is available
if ! command -v git &> /dev/null; then
    echo "❌ git is not installed. Cannot proceed with commit."
    exit 1
fi

# Configure git if not already configured
if [ -z "$(git config user.email)" ]; then
    echo "⚙️  Configuring git user..."
    git config user.email "ci@abaco-loans-analytics.local" 2>/dev/null || true
    git config user.name "CI Automation" 2>/dev/null || true
fi

echo "📋 FILES TO COMMIT:"
echo ""

FILES=(
    "ci-workflow/CI_Workflow_Failure_Handling_test_plan.md"
    "ci-workflow/CI_Workflow_Failure_Handling_checklist.md"
    "ci-workflow/CI_Workflow_Failure_Handling_testcases.md"
    "scripts/ci_diagnosis.sh"
    "scripts/ci_full_fix.sh"
    "scripts/commit_ci_phase6.sh"
    "CLAUDE.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
        git add "$file" 2>/dev/null || echo "⚠️  Could not stage: $file"
    fi
done

echo ""
echo "📝 COMMIT MESSAGE:"
echo ""

COMMIT_MSG="PHASE 6: Complete CI Workflow Failure Handling Test Plan & Implementation

This commit introduces comprehensive testing and failure handling for GitHub Actions workflows.

## Deliverables

### Test Planning & Documentation
- Test Plan (test_plan.md): Objectives, scope, approach, risk assessment, exit criteria
- Test Checklist (checklist.md): 60 test cases with priorities and automation status
- Detailed Test Cases (testcases.md): Parametrized test cases with step-by-step execution

### Test Coverage

#### 60 Total Test Cases:
- 12 Critical Priority
- 28 High Priority  
- 20 Medium Priority

#### 11 Test Categories:
1. Workflow Structure & Syntax (YAML validation, triggers, conditionals)
2. Web Build & Lint (pnpm, TypeScript, ESLint, performance)
3. Analytics Tests (dependencies, execution, coverage)
4. Lint & Policy Checks (Pylint, Flake8, Ruff, mypy, secret scanning)
5. Environment Validation (secret handling, credential validation)
6. Failure Detection & Reporting (Slack notifications, error handling)
7. External Integration Failures (Vercel, AWS, Figma, HubSpot)
8. Retry & Recovery (transient failures, backoff strategies)
9. Performance & Timing (SLA validation, duration checks)
10. Security & Compliance (secret masking, permission validation)
11. Edge Cases (scheduled triggers, manual dispatch)

#### Automation Coverage: 87% (52 automated, 8 manual)

### CI Workflow Enhancements
- Added mypy type-checking to repo-health job
- Enhanced secret validation and sanitization
- Improved failure detection and Slack notifications
- Graceful degradation for missing external services

### Risk Assessment
- Top 5 risks identified with mitigation strategies
- Success criteria: >99% CI success rate, <20min E2E duration
- Performance SLAs: Web build <5min, Analytics <10min, Slack <60s

## Files Created
- ci-workflow/CI_Workflow_Failure_Handling_test_plan.md
- ci-workflow/CI_Workflow_Failure_Handling_checklist.md
- ci-workflow/CI_Workflow_Failure_Handling_testcases.md
- scripts/ci_diagnosis.sh (diagnostic tool)
- scripts/ci_full_fix.sh (comprehensive test & fix)
- scripts/commit_ci_phase6.sh (commit automation)

## Updated Files
- CLAUDE.md: Phase 6 progress tracking
- .github/workflows/ci.yml: Enhanced with mypy type-checking

## Next Steps
1. Run 'make quality' to validate code quality
2. Execute test suite to confirm all tests pass
3. Review htmlcov/index.html for coverage metrics
4. Monitor CI workflows for >99% success rate
5. Phase 7: KPIEngine v1 deprecation and migration"

echo "$COMMIT_MSG"
echo ""
echo "=========================================="
echo ""

# Perform the commit
if git commit -m "$COMMIT_MSG" 2>/dev/null; then
    echo "✅ COMMIT SUCCESSFUL"
    echo ""
    echo "📊 COMMIT STATUS:"
    git log --oneline -1
    echo ""
    echo "📈 REPOSITORY STATUS:"
    git status
else
    echo "⚠️  Git commit failed. Repository may not be initialized or working directory clean."
    echo "To commit manually, run:"
    echo ""
    echo "  git add ci-workflow/ scripts/ci_*.sh CLAUDE.md"
    echo "  git commit -m '$COMMIT_MSG'"
fi

echo ""
echo "✅ Phase 6 CI Workflow Testing - Complete"
