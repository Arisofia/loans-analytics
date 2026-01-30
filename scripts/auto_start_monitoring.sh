#!/bin/bash
#
# Auto Start Monitoring Stack
# Complete automation script for Prometheus + Grafana + Alertmanager
# 
# Usage: bash scripts/auto_start_monitoring.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Abaco Monitoring Stack - Auto Start${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Check Docker
echo -e "${YELLOW}[1/6]${NC} Checking Docker..."
if ! docker ps >/dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo -e "${YELLOW}Starting Docker Desktop...${NC}"
    open -a Docker
    
    # Wait for Docker to be ready
    echo -e "${YELLOW}Waiting for Docker daemon (max 60s)...${NC}"
    for i in {1..30}; do
        if docker ps >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Docker is ready${NC}"
            break
        fi
        echo -n "."
        sleep 2
    done
    
    if ! docker ps >/dev/null 2>&1; then
        echo -e "${RED}✗ Docker failed to start after 60s${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Docker is running${NC}"
fi
echo ""

# Step 2: Load environment variables
echo -e "${YELLOW}[2/6]${NC} Loading environment variables..."
cd "$PROJECT_ROOT"

if [[ -f .env.local ]]; then
    source "$SCRIPT_DIR/load_env.sh"
    echo -e "${GREEN}✓ Environment loaded from .env.local${NC}"
else
    echo -e "${RED}✗ .env.local not found${NC}"
    echo -e "${YELLOW}Please create .env.local with Supabase credentials${NC}"
    exit 1
fi
echo ""

# Step 3: Validate required variables
echo -e "${YELLOW}[3/6]${NC} Validating configuration..."
REQUIRED_VARS=(
    "SUPABASE_PROJECT_REF"
    "SUPABASE_SECRET_API_KEY"
    "NEXT_PUBLIC_SUPABASE_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        echo -e "${RED}✗ Missing required variable: $var${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All required variables present${NC}"
echo ""

# Step 4: Stop conflicting containers
echo -e "${YELLOW}[4/6]${NC} Checking for port conflicts..."
if docker ps --format '{{.Names}}' | grep -q "grafana-observability"; then
    echo -e "${YELLOW}Stopping conflicting Grafana container...${NC}"
    docker stop grafana-observability >/dev/null 2>&1 || true
    echo -e "${GREEN}✓ Conflicts resolved${NC}"
else
    echo -e "${GREEN}✓ No conflicts detected${NC}"
fi
echo ""

# Step 5: Start monitoring stack
echo -e "${YELLOW}[5/6]${NC} Starting monitoring stack..."
docker-compose -f docker-compose.monitoring.yml down >/dev/null 2>&1 || true
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service health
SERVICES=("prometheus" "grafana" "alertmanager")
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" --format '{{.Names}}' | grep -q "$service"; then
        echo -e "${GREEN}✓ $service is running${NC}"
    else
        echo -e "${RED}✗ $service failed to start${NC}"
        ALL_HEALTHY=false
    fi
done

if [[ "$ALL_HEALTHY" != true ]]; then
    echo -e "${RED}Some services failed to start. Check logs:${NC}"
    echo -e "${YELLOW}docker-compose -f docker-compose.monitoring.yml logs${NC}"
    exit 1
fi
echo ""

# Step 6: Configure Grafana datasource
echo -e "${YELLOW}[6/6]${NC} Configuring Grafana datasource..."
sleep 5  # Give Grafana more time to be fully ready

# Check if datasource already exists
DATASOURCE_CHECK=$(curl -s -u admin:${GRAFANA_ADMIN_PASSWORD:-admin123} \
    http://localhost:3001/api/datasources/name/Prometheus 2>/dev/null || echo "not_found")

if [[ "$DATASOURCE_CHECK" == "not_found" ]] || echo "$DATASOURCE_CHECK" | grep -q "Data source not found"; then
    echo -e "${YELLOW}Creating Prometheus datasource...${NC}"
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -u admin:${GRAFANA_ADMIN_PASSWORD:-admin123} \
        http://localhost:3001/api/datasources \
        -d '{
          "name": "Prometheus",
          "type": "prometheus",
          "url": "http://prometheus:9090",
          "access": "proxy",
          "isDefault": true
        }' 2>/dev/null || echo "error")
    
    if echo "$RESPONSE" | grep -q "Datasource added"; then
        echo -e "${GREEN}✓ Datasource created successfully${NC}"
    else
        echo -e "${YELLOW}⚠ Datasource may already exist or requires manual setup${NC}"
    fi
else
    echo -e "${GREEN}✓ Prometheus datasource already configured${NC}"
fi
echo ""

# Final summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ✓ Monitoring Stack is Ready!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo -e "  • Prometheus:    ${GREEN}http://localhost:9090${NC}"
echo -e "  • Grafana:       ${GREEN}http://localhost:3001${NC} (admin / ${GRAFANA_ADMIN_PASSWORD:-admin123})"
echo -e "  • Alertmanager:  ${GREEN}http://localhost:9093${NC}"
echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo -e "  • View logs:     ${YELLOW}docker-compose -f docker-compose.monitoring.yml logs -f${NC}"
echo -e "  • Stop stack:    ${YELLOW}docker-compose -f docker-compose.monitoring.yml down${NC}"
echo -e "  • Restart:       ${YELLOW}docker-compose -f docker-compose.monitoring.yml restart${NC}"
echo ""
echo -e "${BLUE}Targets Status:${NC}"
echo -e "  Check at: ${YELLOW}http://localhost:9090/targets${NC}"
echo ""

# Open Grafana in browser (optional)
if command -v open >/dev/null 2>&1; then
    read -p "Open Grafana in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sleep 2
        open http://localhost:3001
    fi
fi
