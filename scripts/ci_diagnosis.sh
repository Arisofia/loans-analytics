#!/bin/bash
set -e

echo "=========================================="
echo "CI WORKFLOW FAILURE DIAGNOSIS"
echo "=========================================="
echo ""

REPORT_FILE="CI_DIAGNOSIS_REPORT.md"
> "$REPORT_FILE"

{
    echo "# CI Workflow Failure Diagnosis Report"
    echo "**Generated**: $(date)"
    echo "**Repository**: $(pwd)"
    echo ""
    
    echo "## 1. ENVIRONMENT CHECK"
    echo "### Python Version"
    python3 --version
    echo ""
    
    echo "### Critical Dependencies"
    python3 -c "import pandas; print(f'✓ pandas {pandas.__version__}')" || echo "✗ pandas MISSING"
    python3 -c "import pytest; print(f'✓ pytest {pytest.__version__}')" || echo "✗ pytest MISSING"
    python3 -c "import mypy; print(f'✓ mypy {mypy.__version__}')" || echo "✗ mypy MISSING"
    echo ""
    
    echo "## 2. WORKFLOW SYNTAX CHECK"
    echo "### YAML Validation"
    if command -v yamllint &> /dev/null; then
        yamllint .github/workflows/ci.yml && echo "✓ ci.yml: VALID" || echo "✗ ci.yml: INVALID"
    else
        echo "⚠ yamllint not installed, skipping"
    fi
    echo ""
    
    echo "## 3. TEST EXECUTION"
    echo "### Running Tests..."
    echo ""
} >> "$REPORT_FILE"

# Run tests with verbose output
echo "Running pytest..."
if python3 -m pytest tests/ -v --tb=short 2>&1 | tee -a "$REPORT_FILE"; then
    TEST_RESULT="✓ PASSED"
else
    TEST_RESULT="✗ FAILED"
fi

{
    echo ""
    echo "**Result**: $TEST_RESULT"
    echo ""
    
    echo "## 4. LINTING CHECKS"
    echo "### Pylint"
} >> "$REPORT_FILE"

# Pylint
echo "Running pylint..."
PYTHONPATH=src python3 -m pylint src --fail-under=8.0 2>&1 | tee -a "$REPORT_FILE" || echo "Pylint check completed with warnings"

{
    echo ""
    echo "### Flake8"
} >> "$REPORT_FILE"

# Flake8
echo "Running flake8..."
PYTHONPATH=src python3 -m flake8 src 2>&1 | tee -a "$REPORT_FILE" || echo "Flake8 check completed with warnings"

{
    echo ""
    echo "### Ruff"
} >> "$REPORT_FILE"

# Ruff
echo "Running ruff..."
PYTHONPATH=src python3 -m ruff check src 2>&1 | tee -a "$REPORT_FILE" || echo "Ruff check completed with warnings"

{
    echo ""
    echo "## 5. TYPE CHECKING"
    echo "### mypy"
} >> "$REPORT_FILE"

# mypy
echo "Running mypy..."
PYTHONPATH=src python3 -m mypy src --ignore-missing-imports 2>&1 | tee -a "$REPORT_FILE" || echo "mypy check completed with warnings"

{
    echo ""
    echo "## 6. CI WORKFLOW VALIDATION"
    echo ""
    echo "### Workflow Jobs Analysis"
    echo ""
    echo "**Detected Jobs in ci.yml**:"
    grep "^  [a-z-]*:" .github/workflows/ci.yml | sed 's/://g' | awk '{print "- " $1}'
    echo ""
    
    echo "### Key Failure Points"
    echo "- Secret handling (FIGMA_TOKEN, SLACK_WEBHOOK_URL, Vercel tokens)"
    echo "- External API integrations (HubSpot, Supabase)"
    echo "- Artifact uploads and caching"
    echo "- Dependency installation (pnpm, pip)"
    echo ""
    
    echo "## 7. SUMMARY"
    echo ""
    echo "**Report saved to**: $REPORT_FILE"
    
} >> "$REPORT_FILE"

cat "$REPORT_FILE"
echo ""
echo "✅ Diagnosis complete. Report saved to: $REPORT_FILE"
