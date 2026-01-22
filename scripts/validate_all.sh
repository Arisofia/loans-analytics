#!/bin/bash
# Comprehensive repository validation script
# Validates all code, configurations, and build artifacts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Repository Validation${NC}"
echo -e "${BLUE}=====================================${NC}"

# 1. Check for merge conflicts
echo -e "\n${BLUE}1. Checking for merge conflict markers...${NC}"
if grep -r "<<<<<<\|>>>>>>\|=======" --include="*.yml" --include="*.yaml" --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx" . 2>/dev/null | grep -v node_modules | grep -v .git; then
    echo -e "${RED}✗ Merge conflict markers found!${NC}"
    FAILED=1
else
    echo -e "${GREEN}✓ No merge conflict markers${NC}"
fi

# 2. Validate YAML files
echo -e "\n${BLUE}2. Validating YAML files...${NC}"
if command -v yamllint &>/dev/null; then
    if yamllint -d relaxed .github/workflows/*.yml 2>&1; then
        echo -e "${GREEN}✓ YAML files are valid${NC}"
    else
        echo -e "${YELLOW}⚠ YAML validation warnings (non-critical)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ yamllint not installed${NC}"
fi

# 3. Validate TypeScript configs
echo -e "\n${BLUE}3. Checking tsconfig.json files...${NC}"
for tsconfig in tsconfig.json apps/*/tsconfig.json; do
    if [ -f "$tsconfig" ]; then
        if grep -q "ignoreDeprecations" "$tsconfig"; then
            echo -e "${RED}✗ Invalid ignoreDeprecations in $tsconfig${NC}"
            FAILED=1
        else
            echo -e "${GREEN}✓ $tsconfig is valid${NC}"
        fi
    fi
done

# 4. Validate Python syntax
echo -e "\n${BLUE}4. Validating Python syntax...${NC}"
if python -m compileall -q src/ 2>&1; then
    echo -e "${GREEN}✓ Python syntax is valid${NC}"
else
    echo -e "${RED}✗ Python syntax errors found${NC}"
    FAILED=1
fi

# 5. Check shell scripts
echo -e "\n${BLUE}5. Checking shell scripts with shellcheck...${NC}"
if command -v shellcheck &>/dev/null; then
    SHELL_ERRORS=0
    while IFS= read -r script; do
        if ! shellcheck "$script" 2>&1; then
            SHELL_ERRORS=$((SHELL_ERRORS + 1))
        fi
    done < <(find . -name "*.sh" -type f ! -path "./node_modules/*" ! -path "./.git/*")
    
    if [ $SHELL_ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ All shell scripts pass shellcheck${NC}"
    else
        echo -e "${YELLOW}⚠ $SHELL_ERRORS shell script(s) have warnings${NC}"
    fi
else
    echo -e "${YELLOW}⚠ shellcheck not installed${NC}"
fi

# 6. Validate notebooks
echo -e "\n${BLUE}6. Validating Jupyter notebooks...${NC}"
if [ -d "notebooks" ]; then
    NOTEBOOK_ERRORS=0
    for notebook in notebooks/*.ipynb; do
        if [ -f "$notebook" ]; then
            if python -c "import nbformat; nbformat.read('$notebook', as_version=4)" 2>&1; then
                echo -e "${GREEN}✓ $notebook is valid${NC}"
            else
                echo -e "${RED}✗ $notebook is invalid${NC}"
                NOTEBOOK_ERRORS=$((NOTEBOOK_ERRORS + 1))
            fi
        fi
    done
    
    if [ $NOTEBOOK_ERRORS -gt 0 ]; then
        FAILED=1
    fi
else
    echo -e "${YELLOW}⚠ No notebooks directory${NC}"
fi

# 7. Check package.json has test script
echo -e "\n${BLUE}7. Checking package.json test scripts...${NC}"
if [ -f "package.json" ]; then
    if grep -q '"test"' package.json; then
        echo -e "${GREEN}✓ Root package.json has test script${NC}"
    else
        echo -e "${RED}✗ Root package.json missing test script${NC}"
        FAILED=1
    fi
fi

# 8. Validate JSON files
echo -e "\n${BLUE}8. Validating JSON files...${NC}"
JSON_ERRORS=0
for json in tsconfig*.json package*.json vercel.json; do
    if [ -f "$json" ]; then
        if python -m json.tool "$json" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $json is valid${NC}"
        else
            echo -e "${RED}✗ $json is invalid${NC}"
            JSON_ERRORS=$((JSON_ERRORS + 1))
        fi
    fi
done

if [ $JSON_ERRORS -gt 0 ]; then
    FAILED=1
fi

# Summary
echo -e "\n${BLUE}=====================================${NC}"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some validations failed${NC}"
    exit 1
fi
