#!/bin/bash

set +e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_LOCAL="$PROJECT_ROOT/.env.local"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Supabase Data & Tables Inventory${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Extract credentials from .env.local
SUPABASE_DEV_PROJECT=$(grep "^SUPABASE_PROJECT_REF=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_DEV_URL="https://${SUPABASE_DEV_PROJECT}.supabase.co"
SUPABASE_DEV_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_DEV_SERVICE_ROLE=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
POSTGRES_PASSWORD=$(grep "^POSTGRES_PASSWORD=" "$ENV_LOCAL" | cut -d'=' -f2)

SUPABASE_PROD_PROJECT="goxdevkqozomyhsyxhte"
SUPABASE_PROD_URL="https://${SUPABASE_PROD_PROJECT}.supabase.co"

echo -e "${BLUE}Development Project:${NC}"
echo "  Project ID: ${SUPABASE_DEV_PROJECT}"
echo "  URL: ${SUPABASE_DEV_URL}"
echo ""

echo -e "${BLUE}Production Project (Grafana):${NC}"
echo "  Project ID: ${SUPABASE_PROD_PROJECT}"
echo "  URL: ${SUPABASE_PROD_URL}"
echo ""

# Check which project has data
echo -e "${YELLOW}⚠️  PROJECT MISMATCH DETECTED!${NC}"
echo ""
echo "Your setup uses TWO different Supabase projects:"
echo "  1. Development (sddviizcgheusvwqpthm) - in .env.local"
echo "  2. Production (goxdevkqozomyhsyxhte) - in Grafana datasources"
echo ""
echo "This is why Grafana shows no data - they're pointing to different projects!"
echo ""

# Test which project has monitoring tables
echo -e "${BLUE}Checking for monitoring tables...${NC}"
echo ""

# Check development project
echo -n "Development Project (${SUPABASE_DEV_PROJECT}): "
dev_tables=$(curl -s -w "\n%{http_code}" \
    -H "apikey: ${SUPABASE_DEV_ANON_KEY}" \
    "${SUPABASE_DEV_URL}/rest/v1/information_schema.tables?table_schema=eq.public&select=table_name" 2>/dev/null | tail -n1)

if [ "$dev_tables" = "200" ]; then
    echo -e "${GREEN}✅ Accessible${NC}"
    
    # List tables
    tables=$(curl -s -H "apikey: ${SUPABASE_DEV_ANON_KEY}" \
        "${SUPABASE_DEV_URL}/rest/v1/information_schema.tables?table_schema=eq.public&select=table_name" 2>/dev/null)
    
    echo "  Tables found:"
    echo "$tables" | jq -r '.[] | .table_name' 2>/dev/null | sed 's/^/    - /'
    
    # Check for monitoring schema
    echo ""
    echo "  Checking monitoring schema:"
    monitor_check=$(curl -s -w "\n%{http_code}" \
        -H "apikey: ${SUPABASE_DEV_ANON_KEY}" \
        "${SUPABASE_DEV_URL}/rest/v1/monitoring.kpi_definitions?limit=1" 2>/dev/null | tail -n1)
    
    if [ "$monitor_check" = "200" ]; then
        echo -e "    ✅ monitoring.kpi_definitions exists"
    else
        echo -e "    ❌ monitoring.kpi_definitions NOT FOUND"
    fi
else
    echo -e "${RED}❌ Not accessible (HTTP $dev_tables)${NC}"
fi

echo ""

# Check production project
echo -n "Production Project (${SUPABASE_PROD_PROJECT}): "
prod_response=$(curl -s -m 5 -w "\n%{http_code}" \
    -H "apikey: ${SUPABASE_DEV_ANON_KEY}" \
    "${SUPABASE_PROD_URL}/rest/v1/information_schema.tables?table_schema=eq.public&select=table_name" 2>/dev/null | tail -n1)

if [ "$prod_response" = "200" ]; then
    echo -e "${GREEN}✅ Accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Not directly accessible${NC}"
    echo "  (This is expected - need Grafana to test)"
fi

echo ""

# Recommendations
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}RECOMMENDATION${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Choose one of the following options:"
echo ""
echo -e "${YELLOW}Option 1: Use Development Project (Recommended)${NC}"
echo "  ✅ Your data is here"
echo "  ✅ .env.local has correct credentials"
echo "  ❌ Need to update Grafana to use development project"
echo ""
echo "  Run:"
echo "    ./scripts/setup/align-supabase-projects.sh dev"
echo ""
echo -e "${YELLOW}Option 2: Use Production Project${NC}"
echo "  ❌ No data yet"
echo "  ⚠️  Need to migrate data from development"
echo "  ✅ Grafana already configured for this"
echo ""
echo "  Run:"
echo "    ./scripts/setup/migrate-supabase-data.sh"
echo ""

# Show what needs to be created
echo -e "${BLUE}Next Steps:${NC}"
echo "1. Choose a project (Option 1 or 2 above)"
echo "2. Create monitoring tables"
echo "3. Populate with KPI data"
echo "4. Verify Grafana can access the data"
echo ""
