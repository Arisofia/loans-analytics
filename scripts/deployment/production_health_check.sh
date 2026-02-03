#!/bin/bash
# Production Health Check Script
# Usage: ./scripts/production_health_check.sh [app-service-url]
# Example: ./scripts/production_health_check.sh https://abaco-loans-prod.azurewebsites.net

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_URL="${1:-https://abaco-loans-prod.azurewebsites.net}"
HEALTH_ENDPOINT="/health"
TIMEOUT=10

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Production Health Check - $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Function to print status
print_status() {
    local check=$1
    local status=$2
    local message=$3
    
    if [ "$status" = "✅" ]; then
        echo -e "${GREEN}${status} ${check}${NC}: ${message}"
    elif [ "$status" = "⚠️" ]; then
        echo -e "${YELLOW}${status} ${check}${NC}: ${message}"
    else
        echo -e "${RED}${status} ${check}${NC}: ${message}"
    fi
}

# 1. Health Endpoint Check
echo -e "${BLUE}[1] Application Health${NC}"
echo "────────────────────────────────────────────────────────────"

RESPONSE=$(curl -s -w "\n%{http_code}" -m $TIMEOUT "${APP_URL}${HEALTH_ENDPOINT}" 2>&1 || echo "000")
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" = "200" ]; then
    print_status "Health Endpoint" "✅" "Responding normally (HTTP $HTTP_CODE)"
    
    # Parse health response if JSON
    if echo "$BODY" | jq . > /dev/null 2>&1; then
        STATUS=$(echo "$BODY" | jq -r '.status' 2>/dev/null || echo "unknown")
        print_status "Status Field" "✅" "$STATUS"
        
        # Check sub-components
        if echo "$BODY" | jq '.checks' > /dev/null 2>&1; then
            echo "  Sub-component status:"
            echo "$BODY" | jq -r '.checks | to_entries[] | "    • \(.key): \(.value)"' 2>/dev/null || echo "    (Unable to parse components)"
        fi
    fi
else
    print_status "Health Endpoint" "❌" "Not responding (HTTP $HTTP_CODE)"
fi
echo ""

# 2. Response Time Check
echo -e "${BLUE}[2] Response Time${NC}"
echo "────────────────────────────────────────────────────────────"

RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" -m $TIMEOUT "$APP_URL" 2>&1 || echo "timeout")

if [ "$RESPONSE_TIME" != "timeout" ]; then
    RESPONSE_TIME_MS=$(echo "$RESPONSE_TIME" | awk '{printf "%.0f", $1 * 1000}')
    
    if [ "$RESPONSE_TIME_MS" -lt 1000 ]; then
        print_status "Response Time" "✅" "${RESPONSE_TIME_MS}ms (excellent)"
    elif [ "$RESPONSE_TIME_MS" -lt 5000 ]; then
        print_status "Response Time" "✅" "${RESPONSE_TIME_MS}ms (acceptable)"
    else
        print_status "Response Time" "⚠️" "${RESPONSE_TIME_MS}ms (slow)"
    fi
else
    print_status "Response Time" "❌" "Request timed out after ${TIMEOUT}s"
fi
echo ""

# 3. Git Status Check
echo -e "${BLUE}[3] Git Status${NC}"
echo "────────────────────────────────────────────────────────────"

CURRENT_COMMIT=$(git log --oneline -1 2>/dev/null | cut -d' ' -f1 || echo "unknown")
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null | head -1 || echo "unknown")

print_status "Current Branch" "✅" "$CURRENT_BRANCH"
print_status "Latest Commit" "✅" "$CURRENT_COMMIT: $COMMIT_MSG"

if git status --porcelain | grep -q .; then
    print_status "Uncommitted Changes" "⚠️" "Working directory has changes"
else
    print_status "Uncommitted Changes" "✅" "Working directory clean"
fi
echo ""

# 4. Code Quality Check
echo -e "${BLUE}[4] Code Quality${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -f "pyproject.toml" ]; then
    # Try running pylint check
    if command -v pylint &> /dev/null; then
        PYLINT_SCORE=$(python -m pylint src/pipeline --rcfile=.pylintrc 2>&1 | grep -oP 'rated at \K[0-9.]+' || echo "unknown")
        if [ "$PYLINT_SCORE" != "unknown" ]; then
            if (( $(echo "$PYLINT_SCORE >= 9.0" | bc -l) )); then
                print_status "Pylint Score" "✅" "$PYLINT_SCORE/10 (excellent)"
            else
                print_status "Pylint Score" "⚠️" "$PYLINT_SCORE/10"
            fi
        fi
    fi
    
    # Check for active TODOs
    TODO_COUNT=$(grep -r "TODO:" src/ python/ --include="*.py" 2>/dev/null | wc -l || echo "0")
    if [ "$TODO_COUNT" = "0" ]; then
        print_status "Active TODOs" "✅" "None found"
    else
        print_status "Active TODOs" "⚠️" "$TODO_COUNT found"
    fi
fi
echo ""

# 5. Python Environment Check
echo -e "${BLUE}[5] Environment${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -n "$VIRTUAL_ENV" ]; then
    print_status "Virtual Environment" "✅" "Active ($VIRTUAL_ENV)"
else
    print_status "Virtual Environment" "⚠️" "Not activated"
fi

PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}' || echo "unknown")
print_status "Python Version" "✅" "$PYTHON_VERSION"

# Check required packages
REQUIRED_PACKAGES=("pandas" "pydantic" "asyncpg" "opentelemetry")
for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if python -c "import ${pkg//-/_}" 2>/dev/null; then
        print_status "Package: $pkg" "✅" "Installed"
    else
        print_status "Package: $pkg" "❌" "Not installed"
    fi
done
echo ""

# 6. Test Status
echo -e "${BLUE}[6] Tests${NC}"
echo "────────────────────────────────────────────────────────────"

if [ -d "tests" ] && command -v pytest &> /dev/null; then
    TEST_RESULT=$(pytest tests/ -q --tb=no 2>&1 | tail -1)
    print_status "Test Suite" "✅" "$TEST_RESULT"
else
    print_status "Test Suite" "⚠️" "Pytest not available or tests directory missing"
fi
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

HEALTH_OK=0
HEALTH_WARN=0

if [ "$HTTP_CODE" = "200" ]; then
    ((HEALTH_OK++))
else
    ((HEALTH_WARN++))
fi

if [ "$RESPONSE_TIME_MS" -lt 5000 ] 2>/dev/null; then
    ((HEALTH_OK++))
fi

if [ "$TODO_COUNT" = "0" ] 2>/dev/null; then
    ((HEALTH_OK++))
fi

if [ -n "$VIRTUAL_ENV" ]; then
    ((HEALTH_OK++))
fi

echo -e "${GREEN}✅ Healthy Checks: $HEALTH_OK${NC}"
echo -e "${YELLOW}⚠️ Warning Checks: $HEALTH_WARN${NC}"

if [ "$HEALTH_WARN" -eq 0 ]; then
    echo -e "${GREEN}Overall Status: HEALTHY${NC}"
    exit 0
else
    echo -e "${YELLOW}Overall Status: DEGRADED (requires attention)${NC}"
    exit 1
fi
