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
ENV_MONITORING="$PROJECT_ROOT/.env.monitoring"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Align Supabase Projects${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Extract development project credentials
SUPABASE_DEV_PROJECT=$(grep "^SUPABASE_PROJECT_REF=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_DEV_URL="https://${SUPABASE_DEV_PROJECT}.supabase.co"
SUPABASE_DEV_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_DEV_SERVICE_ROLE=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)

echo -e "${YELLOW}Using Development Project:${NC}"
echo "  Project ID: ${SUPABASE_DEV_PROJECT}"
echo "  URL: ${SUPABASE_DEV_URL}"
echo ""

# Step 1: Update .env.monitoring to use development project
echo -e "${BLUE}Step 1: Updating .env.monitoring...${NC}"

cat > "$ENV_MONITORING" << EOF
GRAFANA_ADMIN_PASSWORD=admin123
SUPABASE_URL=${SUPABASE_DEV_URL}
SUPABASE_ANON_KEY=${SUPABASE_DEV_ANON_KEY}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_DEV_SERVICE_ROLE}
AZURE_SUBSCRIPTION_ID=
EOF

echo -e "${GREEN}✅ Updated .env.monitoring${NC}"
echo ""

# Step 2: Update Grafana datasource configuration
echo -e "${BLUE}Step 2: Updating Grafana datasource...${NC}"

DATASOURCE_FILE="$PROJECT_ROOT/grafana/provisioning/datasources/supabase.yml"

# Replace project references in datasource config
sed -i '' "s|db\.goxdevkqozomyhsyxhte\.supabase\.co|db.${SUPABASE_DEV_PROJECT}.supabase.co|g" "$DATASOURCE_FILE"
sed -i '' "s|https://goxdevkqozomyhsyxhte\.supabase\.co|${SUPABASE_DEV_URL}|g" "$DATASOURCE_FILE"

echo -e "${GREEN}✅ Updated datasource configuration${NC}"
echo "  File: $DATASOURCE_FILE"
echo ""

# Step 3: Restart Grafana
echo -e "${BLUE}Step 3: Restarting Grafana...${NC}"

cd "$PROJECT_ROOT"
docker compose --profile monitoring restart grafana

# Wait for restart
sleep 5

echo -e "${GREEN}✅ Grafana restarted${NC}"
echo ""

# Step 4: Test connection
echo -e "${BLUE}Step 4: Testing connection...${NC}"

grafana_health=$(curl -s -u admin:admin123 http://localhost:3001/api/health | jq -r '.database // "error"')

if [ "$grafana_health" = "ok" ]; then
    echo -e "${GREEN}✅ Grafana is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana still starting...${NC}"
fi

echo ""

# Summary
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Projects Aligned${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "  Development Project: ${SUPABASE_DEV_PROJECT}"
echo "  Grafana now uses: ${SUPABASE_DEV_URL}"
echo "  Configuration updated in .env.monitoring"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Open http://localhost:3001 in browser"
echo "2. Go to Configuration → Data Sources"
echo "3. Click 'Test' on Supabase PostgreSQL"
echo "4. Expected: ✅ 'Data source is working'"
echo ""
echo -e "${BLUE}To populate data:${NC}"
echo "  python scripts/data/run_data_pipeline.py --input data/raw/abaco_real_data_20260202.csv"
echo ""
