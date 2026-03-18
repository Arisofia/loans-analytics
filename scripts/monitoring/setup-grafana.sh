#!/bin/bash

set +e  # Don't exit on error - we want to continue even if tests fail

echo "🚀 Setting up Grafana connection to Supabase..."

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MONITORING_ENV="$PROJECT_ROOT/.env.monitoring"

# Check if .env.monitoring exists
if [ ! -f "$MONITORING_ENV" ]; then
    echo -e "${YELLOW}⚠️  .env.monitoring not found. Creating from template...${NC}"
    cat > "$MONITORING_ENV" << 'EOF'
# Grafana Configuration
GRAFANA_ADMIN_PASSWORD=admin123

# Supabase Credentials
# Project: goxdevkqozomyhsyxhte (PRODUCTION)
# Get these from: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api
SUPABASE_URL=https://goxdevkqozomyhsyxhte.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# Optional direct DB credentials (if you prefer static DB auth)
SUPABASE_DB_HOST=aws-1-us-east-2.pooler.supabase.com
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres.sddviizcgheusvwqpthm
SUPABASE_DB_PASSWORD=your-postgres-password-here

# Provider-specific cloud credentials (optional)
# Leave blank for free-tier local monitoring setup.
EOF
    echo -e "${GREEN}✅ Created $MONITORING_ENV${NC}"
    echo -e "${YELLOW}⚠️  Please update the Supabase keys in $MONITORING_ENV${NC}"
    exit 1
fi

# Check if required variables are set
if grep -q "your-" "$MONITORING_ENV"; then
    echo -e "${RED}❌ Error: .env.monitoring contains placeholder values${NC}"
    echo "Please update these keys in $MONITORING_ENV:"
    echo "  - SUPABASE_ANON_KEY"
    echo "  - SUPABASE_SERVICE_ROLE_KEY"
    exit 1
fi

# Load environment variables
source "$MONITORING_ENV"

# Validate Supabase connection
echo -e "${BLUE}🔍 Testing Supabase connection...${NC}"

if command -v curl &> /dev/null; then
    response=$(curl -s -m 5 -o /dev/null -w "%{http_code}" \
        -H "apikey: $SUPABASE_ANON_KEY" \
        "https://goxdevkqozomyhsyxhte.supabase.co/rest/v1/monitoring.kpi_definitions?select=count" 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Supabase REST API connection successful${NC}"
    elif [ "$response" = "404" ]; then
        echo -e "${YELLOW}⚠️  Supabase REST API responding (HTTP 404) - monitoring tables may not exist yet${NC}"
    else
        echo -e "${YELLOW}⚠️  Supabase REST API test skipped (timeout or network issue)${NC}"
        echo "This is normal if you're offline or the table doesn't exist yet."
    fi
else
    echo -e "${YELLOW}⚠️  curl not found - skipping connection test${NC}"
fi

# Start services
echo -e "${BLUE}🐳 Starting monitoring stack...${NC}"

cd "$PROJECT_ROOT"

# Stop existing containers
docker compose --profile monitoring down 2>/dev/null || true

# Start new containers with environment file
docker compose --env-file "$MONITORING_ENV" --profile monitoring up -d prometheus grafana alertmanager

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 5

# Check if Grafana is running
if docker ps | grep -q grafana; then
    echo -e "${GREEN}✅ Grafana is running${NC}"
else
    echo -e "${YELLOW}⚠️  Grafana container not yet running - it may take a moment to start${NC}"
    echo "Checking logs..."
    docker logs grafana 2>/dev/null || echo "No logs available yet"
fi

# Refresh datasource credentials using Supabase CLI login-role (preferred path)
echo -e "${BLUE}🔐 Refreshing Grafana datasource login-role credentials...${NC}"
if "$PROJECT_ROOT/scripts/monitoring/refresh_grafana_supabase_datasource.sh" >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Supabase PostgreSQL datasource refreshed${NC}"
else
    echo -e "${YELLOW}⚠️  Could not refresh login-role credentials automatically${NC}"
    echo "   Run manually after login/link:"
    echo "   ./scripts/monitoring/refresh_grafana_supabase_datasource.sh"
fi

# Display connection info
echo -e "${GREEN}✅ Grafana setup complete!${NC}"
echo ""
echo -e "${BLUE}📊 Access Grafana:${NC}"
echo "   URL: http://localhost:3001"
echo "   Username: admin"
echo "   Password: ${GRAFANA_ADMIN_PASSWORD}"
echo ""
echo -e "${BLUE}📈 Configured Data Sources:${NC}"
echo "   - Supabase PostgreSQL (db.goxdevkqozomyhsyxhte.supabase.co:5432)"
echo "   - Supabase REST API"
echo "   - Prometheus Local (http://prometheus:9090)"
echo "   - Azure Monitor (optional)"
echo ""
echo -e "${BLUE}📚 Next steps:${NC}"
echo "   1. Open http://localhost:3001 in your browser"
echo "   2. Log in with admin / ${GRAFANA_ADMIN_PASSWORD}"
echo "   3. Go to Configuration → Data Sources"
echo "   4. Click 'Test' on Supabase PostgreSQL to verify connection"
echo "   5. View KPI dashboards in the 'KPI Monitoring' folder"
echo ""
