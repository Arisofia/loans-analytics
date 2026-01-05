#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "CREDENTIAL SCAN - Check for Exposed Secrets"
echo "=========================================="
echo ""

FOUND_ISSUES=0

# Patterns to check for
PATTERNS=(
    "sk-""proj-"  # OpenAI-style keys (obfuscated to avoid committing literals)
    "sk-""ant-"   # Anthropic-style keys (obfuscated to avoid committing literals)
    "HUBSPOT_TOKEN="
)

echo "Scanning codebase for exposed credentials..."
echo ""

tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

for pattern in "${PATTERNS[@]}"; do
    printf '%b' "Checking for '$pattern': "
    if grep -r --no-messages "$pattern" --include="*.py" --include="*.sh" --include="*.yml" --include="*.yaml" \
        --exclude-dir=node_modules --exclude-dir=.venv --exclude-dir=__pycache__ . > "$tmpfile" 2>/dev/null && [ -s "$tmpfile" ]; then
        printf '%b\n' "⚠️  FOUND"
        head -n 5 "$tmpfile"
        FOUND_ISSUES=$((FOUND_ISSUES + 1))
        printf '%b\n' ""
    else
        printf '%b\n' "✅ OK"
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
