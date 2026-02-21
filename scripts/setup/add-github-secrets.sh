#!/bin/bash

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_LOCAL="$PROJECT_ROOT/.env.local"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}GitHub Actions Secrets Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) is not installed${NC}"
    echo ""
    echo "Install GitHub CLI:"
    echo "  macOS:  brew install gh"
    echo "  Linux:  sudo apt install gh"
    echo "  Windows: choco install gh"
    echo ""
    echo "Then authenticate:"
    echo "  gh auth login"
    exit 1
fi

# Check if authenticated
if ! gh auth status &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with GitHub${NC}"
    echo ""
    echo "Authenticate first:"
    echo "  gh auth login"
    exit 1
fi

echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
echo ""

# Extract credentials from .env.local
if [ ! -f "$ENV_LOCAL" ]; then
    echo -e "${RED}❌ .env.local not found${NC}"
    exit 1
fi

SUPABASE_URL=$(grep "^NEXT_PUBLIC_SUPABASE_URL=" "$ENV_LOCAL" | cut -d'=' -f2 || grep "^SUPABASE_URL=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_SERVICE_ROLE_KEY=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_PROJECT_REF=$(grep "^SUPABASE_PROJECT_REF=" "$ENV_LOCAL" | cut -d'=' -f2)

if [ -z "$SUPABASE_URL" ]; then
    echo -e "${RED}❌ SUPABASE_URL not found in .env.local${NC}"
    exit 1
fi

echo -e "${BLUE}Found credentials for project: $SUPABASE_PROJECT_REF${NC}"
echo ""

# Ask for confirmation
echo -e "${YELLOW}The following secrets will be added to GitHub:${NC}"
echo "  - SUPABASE_URL: $SUPABASE_URL"
echo "  - SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."
echo "  - SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:20}..."
echo "  - SUPABASE_DATABASE_URL: postgresql://postgres:***@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Adding secrets to GitHub...${NC}"
echo ""

# Add secrets
secrets=(
    "SUPABASE_URL:$SUPABASE_URL"
    "SUPABASE_ANON_KEY:$SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY:$SUPABASE_SERVICE_ROLE_KEY"
)

for secret in "${secrets[@]}"; do
    name="${secret%%:*}"
    value="${secret#*:}"
    
    echo -n "Setting $name... "
    gh secret set "$name" --body "$value" 2>/dev/null && \
        echo -e "${GREEN}✅${NC}" || \
        echo -e "${RED}❌${NC}"
done

# Add DATABASE_URL
echo -n "Setting SUPABASE_DATABASE_URL... "
SUPABASE_DATABASE_URL="postgresql://postgres:${POSTGRES_PASSWORD}@db.${SUPABASE_PROJECT_REF}.supabase.co:5432/postgres"
gh secret set SUPABASE_DATABASE_URL --body "$SUPABASE_DATABASE_URL" 2>/dev/null && \
    echo -e "${GREEN}✅${NC}" || \
    echo -e "${RED}❌${NC}"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ GitHub Secrets Added${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}View your secrets:${NC}"
echo "  https://github.com/arisofia/abaco-loans-analytics/settings/secrets/actions"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Update workflows to use the secrets"
echo "  2. Run tests in GitHub Actions"
echo "  3. Deploy to production when ready"
echo ""
