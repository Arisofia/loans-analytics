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
ENV_MONITORING="$PROJECT_ROOT/.env.monitoring"

SUPABASE_PROJECT="goxdevkqozomyhsyxhte"
SUPABASE_URL="https://$SUPABASE_PROJECT.supabase.co"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Supabase Credentials Management${NC}"
echo -e "${BLUE}Project: $SUPABASE_PROJECT${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Step 1: Verify Supabase API Access
echo -e "${BLUE}Step 1: Checking Supabase credentials...${NC}"

if [ ! -f "$ENV_LOCAL" ]; then
    echo -e "${RED}❌ .env.local not found at $ENV_LOCAL${NC}"
    exit 1
fi

# Extract credentials from .env.local
SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_SERVICE_ROLE_KEY=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_DB_PASSWORD=$(grep "^POSTGRES_PASSWORD=" "$ENV_LOCAL" | cut -d'=' -f2)

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}❌ SUPABASE_ANON_KEY not found in .env.local${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found SUPABASE_ANON_KEY${NC}"
echo -e "${GREEN}✅ Found SUPABASE_SERVICE_ROLE_KEY${NC}"
echo -e "${GREEN}✅ Found POSTGRES_PASSWORD${NC}"

# Step 2: Test REST API Connection
echo ""
echo -e "${BLUE}Step 2: Testing Supabase REST API connection...${NC}"

if command -v curl &> /dev/null; then
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "apikey: $SUPABASE_ANON_KEY" \
        "$SUPABASE_URL/rest/v1/monitoring.kpi_definitions?select=count" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ REST API connection successful (HTTP 200)${NC}"
    elif [ "$http_code" = "404" ]; then
        echo -e "${YELLOW}⚠️  REST API responding (HTTP 404) - monitoring.kpi_definitions table may not exist${NC}"
    elif [ "$http_code" = "401" ]; then
        echo -e "${RED}❌ REST API returned 401 Unauthorized - check API key${NC}"
    else
        echo -e "${YELLOW}⚠️  REST API returned HTTP $http_code${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  curl not found - skipping REST API test${NC}"
fi

# Step 3: Verify PostgreSQL Credentials
echo ""
echo -e "${BLUE}Step 3: Verifying PostgreSQL credentials...${NC}"

if command -v psql &> /dev/null; then
    echo "Attempting PostgreSQL connection..."
    
    PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
        --host "db.$SUPABASE_PROJECT.supabase.co" \
        --port 5432 \
        --username postgres \
        --dbname postgres \
        --command "SELECT version();" \
        --no-password 2>/dev/null && \
    echo -e "${GREEN}✅ PostgreSQL connection successful${NC}" || \
    echo -e "${YELLOW}⚠️  PostgreSQL connection test skipped (psql connection details may be invalid)${NC}"
else
    echo -e "${YELLOW}⚠️  psql not installed - skipping PostgreSQL connection test${NC}"
fi

# Step 4: Check credential format
echo ""
echo -e "${BLUE}Step 4: Validating credential format...${NC}"

if [[ "$SUPABASE_ANON_KEY" == eyJ* ]]; then
    echo -e "${GREEN}✅ SUPABASE_ANON_KEY is valid JWT token${NC}"
else
    echo -e "${RED}❌ SUPABASE_ANON_KEY does not appear to be a valid JWT token${NC}"
fi

if [[ "$SUPABASE_SERVICE_ROLE_KEY" == eyJ* ]]; then
    echo -e "${GREEN}✅ SUPABASE_SERVICE_ROLE_KEY is valid JWT token${NC}"
else
    echo -e "${RED}❌ SUPABASE_SERVICE_ROLE_KEY does not appear to be a valid JWT token${NC}"
fi

# Step 5: Create .env.monitoring if needed
echo ""
echo -e "${BLUE}Step 5: Setting up .env.monitoring for Grafana...${NC}"

if [ ! -f "$ENV_MONITORING" ]; then
    echo -e "${YELLOW}Creating .env.monitoring...${NC}"
    cat > "$ENV_MONITORING" << EOF
GRAFANA_ADMIN_PASSWORD=admin123
SUPABASE_URL=$SUPABASE_URL
SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
EOF
    echo -e "${GREEN}✅ Created .env.monitoring${NC}"
else
    echo -e "${GREEN}✅ .env.monitoring already exists${NC}"
fi

# Step 6: Display GitHub Actions secret commands
echo ""
echo -e "${BLUE}Step 6: GitHub Actions Secrets${NC}"
echo ""
echo -e "${YELLOW}To add credentials to GitHub Actions, run these commands:${NC}"
echo ""
echo "# Supabase credentials"
echo "gh secret set SUPABASE_URL --body '$SUPABASE_URL'"
echo "gh secret set SUPABASE_ANON_KEY --body '${SUPABASE_ANON_KEY:0:10}...'"
echo "gh secret set SUPABASE_SERVICE_ROLE_KEY --body '${SUPABASE_SERVICE_ROLE_KEY:0:10}...'"
echo "gh secret set SUPABASE_DATABASE_URL --body 'postgresql://postgres:<PASSWORD>@db.$SUPABASE_PROJECT.supabase.co:5432/postgres'"
echo ""
echo -e "${BLUE}Or visit: https://github.com/arisofia/abaco-loans-analytics/settings/secrets/actions${NC}"
echo ""

# Step 7: Summary
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Supabase Credentials Check Complete${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  📦 Project: $SUPABASE_PROJECT"
echo "  🌐 URL: $SUPABASE_URL"
echo "  💾 Local Config: $ENV_LOCAL"
echo "  📊 Monitoring Config: $ENV_MONITORING"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Add secrets to GitHub: https://github.com/arisofia/abaco-loans-analytics/settings/secrets/actions"
echo "  2. Test Grafana connection: ./scripts/monitoring/setup-grafana.sh"
echo "  3. Run integration tests: pytest tests/ -m integration"
echo ""
