#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "CREDENTIAL SCAN - Check for Exposed Secrets"
echo "=========================================="
echo ""

FOUND_ISSUES=0

# Patterns to check for
PATTERNS=(
    "sk-""proj-"  # OpenAI keys
    "sk-""ant-"   # Anthropic keys
    "HUBSPOT_TOKEN="
)

echo "Scanning codebase for exposed credentials..."
echo ""

for pattern in "${PATTERNS[@]}"; do
    echo -n "Checking for '$pattern': "
    if grep -r "$pattern" --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml" \
        --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=__pycache__ . 2>/dev/null | \
        grep -v "^Binary" > /tmp/scan_results.txt; then
        echo "⚠️  FOUND"
        cat /tmp/scan_results.txt | head -5
        FOUND_ISSUES=$((FOUND_ISSUES + 1))
        echo ""
    else
        echo "✅ OK"
    fi
done

if [ $FOUND_ISSUES -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ No obvious exposed credentials found"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "⚠️  $FOUND_ISSUES potential issues found"
    echo "=========================================="
    echo ""
    echo "Review these findings and remove any exposed credentials."
fi
