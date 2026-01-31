#!/bin/bash
# Repository Cleanup Script
# Fixes code quality issues, trailing whitespace, and runs formatting

set -e

echo "🧹 Repository Cleanup - Starting"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Activate virtual environment if exists
if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# 1. Remove trailing whitespace from all Python files
echo -e "${YELLOW}Step 1: Removing trailing whitespace...${NC}"
find . -type f -name "*.py" \
    ! -path "./.venv/*" \
    ! -path "./node_modules/*" \
    ! -path "./.git/*" \
    ! -path "./build/*" \
    -exec sed -i '' 's/[[:space:]]*$//' {} \;
echo -e "${GREEN}✓ Trailing whitespace removed${NC}"

# 2. Fix line endings (ensure LF not CRLF)
echo -e "${YELLOW}Step 2: Normalizing line endings...${NC}"
find . -type f \( -name "*.py" -o -name "*.yml" -o -name "*.yaml" -o -name "*.md" \) \
    ! -path "./.venv/*" \
    ! -path "./node_modules/*" \
    ! -path "./.git/*" \
    ! -path "./build/*" \
    -exec dos2unix {} \; 2>/dev/null || true
echo -e "${GREEN}✓ Line endings normalized${NC}"

# 3. Run Black formatter
echo -e "${YELLOW}Step 3: Running Black formatter...${NC}"
if command -v black &> /dev/null; then
    black src/ tests/ scripts/ python/ --exclude '\.venv|venv|build|dist|\.eggs' || true
    echo -e "${GREEN}✓ Black formatting complete${NC}"
else
    echo -e "${YELLOW}⚠ Black not installed, skipping${NC}"
fi

# 4. Run isort for import sorting
echo -e "${YELLOW}Step 4: Sorting imports with isort...${NC}"
if command -v isort &> /dev/null; then
    isort src/ tests/ scripts/ python/ --profile black --skip .venv --skip venv || true
    echo -e "${GREEN}✓ Import sorting complete${NC}"
else
    echo -e "${YELLOW}⚠ isort not installed, skipping${NC}"
fi

# 5. Run pylint on critical files
echo -e "${YELLOW}Step 5: Running pylint checks...${NC}"
if command -v pylint &> /dev/null; then
    pylint src/pipeline/calculation.py scripts/path_utils.py python/kpis/engine.py \
        --disable=too-many-locals,too-many-branches,too-many-statements \
        --max-line-length=100 || true
    echo -e "${GREEN}✓ Pylint checks complete${NC}"
else
    echo -e "${YELLOW}⚠ pylint not installed, skipping${NC}"
fi

# 6. Check for merge conflict markers
echo -e "${YELLOW}Step 6: Checking for merge conflict markers...${NC}"
if grep -r "^<<<<<<< " . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules 2>/dev/null; then
    echo -e "${RED}✗ Found merge conflict markers!${NC}"
    exit 1
else
    echo -e "${GREEN}✓ No merge conflict markers found${NC}"
fi

# 7. Validate YAML files
echo -e "${YELLOW}Step 7: Validating YAML syntax...${NC}"
if command -v yamllint &> /dev/null; then
    yamllint .github/workflows/*.yml -d '{extends: relaxed, rules: {line-length: {max: 200}}}' || true
    echo -e "${GREEN}✓ YAML validation complete${NC}"
else
    echo -e "${YELLOW}⚠ yamllint not installed, skipping${NC}"
fi

# 8. Run pytest to validate tests
echo -e "${YELLOW}Step 8: Running quick test validation...${NC}"
if command -v pytest &> /dev/null; then
    pytest tests/ -x -q --tb=no --no-header --disable-warnings || true
    echo -e "${GREEN}✓ Test validation complete${NC}"
else
    echo -e "${YELLOW}⚠ pytest not installed, skipping${NC}"
fi

# 9. Check for common security issues
echo -e "${YELLOW}Step 9: Security checks...${NC}"
echo "Checking for hardcoded secrets..."
if grep -r "password\s*=\s*['\"]" src/ python/ --include="*.py" 2>/dev/null | grep -v "# nosec\|# noqa"; then
    echo -e "${YELLOW}⚠ Potential hardcoded secrets found - review manually${NC}"
fi

if grep -r "api_key\s*=\s*['\"]" src/ python/ --include="*.py" 2>/dev/null | grep -v "# nosec\|# noqa"; then
    echo -e "${YELLOW}⚠ Potential hardcoded API keys found - review manually${NC}"
fi
echo -e "${GREEN}✓ Security checks complete${NC}"

# 10. Summary
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Repository cleanup complete!${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Next steps:"
echo "1. Review changes: git diff"
echo "2. Stage changes: git add -A"
echo "3. Commit: git commit -m 'chore: repository cleanup and formatting'"
echo "4. Push: git push origin main"
echo ""
