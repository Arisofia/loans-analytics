#!/bin/bash
set -e

# ==============================================================================
# Hardened Production Deployment Script for Abaco Loans Analytics
# ==============================================================================
# Ensures a clean, traceable, and validated deployment to production.
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================================${NC}"
echo -e "${BLUE}🚀 Abaco Loans Analytics - Hardened Production Deployment${NC}"
echo -e "${BLUE}======================================================================${NC}"

# 1. Environment & Prerequisites
echo -e "\n${BLUE}[1/6] Checking environment...${NC}"
if [[ "$OSTYPE" != "darwin"* && "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}❌ Unsupported OS: $OSTYPE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ OS check passed ($OSTYPE)${NC}"

# Check for required tools
REQUIRED_TOOLS=("git" "python3" "docker" "docker-compose")
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
        echo -e "${RED}❌ Required tool not found: $tool${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✅ All required tools are available${NC}"

# 2. Git Status Verification (Mandatory for Traceability)
echo -e "\n${BLUE}[2/6] Verifying Git status...${NC}"

if [ "${GITHUB_ACTIONS}" != "true" ]; then
    git fetch origin main --quiet

    # Check for uncommitted changes
    if [[ -n $(git status --porcelain) ]]; then
        echo -e "${RED}❌ Uncommitted changes detected.${NC}"
        echo -e "${YELLOW}   Production deployment requires a perfectly clean state for traceability.${NC}"
        git status -sb
        exit 1
    fi

    # Check if in sync with origin/main
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${RED}❌ Local branch is not in sync with origin/main.${NC}"
        echo -e "${YELLOW}   Please push or pull changes before deploying to production.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Git state is clean and in sync with origin/main${NC}"
else
    echo -e "${GREEN}✅ CI environment detected, using current checkout state.${NC}"
fi

# 3. Security Scan
echo -e "\n${BLUE}[3/6] Running security scan...${NC}"
if [ -f "Makefile" ] && grep -q "security-check" Makefile; then
    make security-check || { echo -e "${RED}❌ Security check failed${NC}"; exit 1; }
else
    echo -e "${YELLOW}⚠️  security-check target not found in Makefile, running bandit manually...${NC}"
    python3 -m bandit -r src/ python/ --quiet || { echo -e "${RED}❌ Bandit security scan failed${NC}"; exit 1; }
fi
echo -e "${GREEN}✅ Security scan passed${NC}"

# 4. Quality Gate
echo -e "\n${BLUE}[4/6] Running quality gate (lint, type-check, tests)...${NC}"
make lint || { echo -e "${RED}❌ Linting failed${NC}"; exit 1; }
make type-check || { echo -e "${RED}❌ Type check failed${NC}"; exit 1; }
make test || { echo -e "${RED}❌ Tests failed${NC}"; exit 1; }
echo -e "${GREEN}✅ Quality gate passed${NC}"

# 5. Deployment Phase
echo -e "\n${BLUE}[5/6] Executing deployment...${NC}"
# Use the canonical deployment stack if available
if [ -f "scripts/deployment/deploy_stack.sh" ]; then
    echo -e "${BLUE}📦 Triggering stack deployment...${NC}"
    bash scripts/deployment/deploy_stack.sh
else
    echo -e "${YELLOW}⚠️  scripts/deployment/deploy_stack.sh not found, running alternative...${NC}"
    docker-compose -f docker-compose.dashboard.yml build
    docker-compose -f docker-compose.dashboard.yml up -d
fi
echo -e "${GREEN}✅ Deployment phase complete${NC}"

# 6. Post-Deployment Verification
echo -e "\n${BLUE}[6/6] Running post-deployment health checks...${NC}"
if [ -f "scripts/deployment/production_health_check.sh" ]; then
    # Default to localhost for verification if no URL provided
    bash scripts/deployment/production_health_check.sh http://localhost:8501
else
    echo -e "${YELLOW}⚠️  scripts/deployment/production_health_check.sh not found, performing basic ping...${NC}"
    curl -s --head http://localhost:8501 | head -n 1 || { echo -e "${RED}❌ Health check failed${NC}"; exit 1; }
fi

echo -e "\n${GREEN}======================================================================${NC}"
echo -e "${GREEN}✅ Production deployment completed successfully!${NC}"
echo -e "${BLUE}   Commit: $(git rev-parse --short HEAD)${NC}"
echo -e "${BLUE}   Time:   $(date)${NC}"
echo -e "${GREEN}======================================================================${NC}"
