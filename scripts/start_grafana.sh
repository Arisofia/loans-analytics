#!/bin/bash

# Quick Start Script for Grafana Monitoring Stack
# This script automates the setup and startup of Prometheus + Grafana + Alertmanager

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "🚀 Abaco Grafana Monitoring Quick Start"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"
echo ""

# Load environment variables
if [ -f .env.local ]; then
    echo "📋 Loading environment variables from .env.local..."
    set -a
    source .env.local
    set +a
    echo -e "${GREEN}✅ Environment variables loaded${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: .env.local not found${NC}"
    echo "Creating .env.local from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env.local
        echo -e "${YELLOW}⚠️  Please edit .env.local with your credentials${NC}"
        exit 1
    else
        echo -e "${RED}❌ Error: .env.example not found${NC}"
        exit 1
    fi
fi

# Check required environment variables
REQUIRED_VARS=("SUPABASE_PROJECT_REF" "SUPABASE_SECRET_API_KEY")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables in .env.local"
    exit 1
fi

# Set Grafana admin password if not set
if [ -z "$GRAFANA_ADMIN_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  GRAFANA_ADMIN_PASSWORD not set${NC}"
    echo "Please enter a secure admin password for Grafana:"
    read -s -p "Password: " GRAFANA_ADMIN_PASSWORD
    echo ""
    echo "Please confirm the password:"
    read -s -p "Password: " GRAFANA_ADMIN_PASSWORD_CONFIRM
    echo ""
    
    if [ "$GRAFANA_ADMIN_PASSWORD" != "$GRAFANA_ADMIN_PASSWORD_CONFIRM" ]; then
        echo -e "${RED}❌ Error: Passwords do not match${NC}"
        exit 1
    fi
    
    # Add to .env.local
    echo "GRAFANA_ADMIN_PASSWORD=$GRAFANA_ADMIN_PASSWORD" >> .env.local
    echo -e "${GREEN}✅ Password saved to .env.local${NC}"
fi

export GRAFANA_ADMIN_PASSWORD

echo ""
echo "📊 Starting monitoring stack..."
echo ""

# Stop existing containers if running
if docker ps | grep -q "prometheus\|grafana\|alertmanager"; then
    echo "Stopping existing monitoring containers..."
    docker-compose -f docker-compose.monitoring.yml down
fi

# Start the stack
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Check if services are running
if docker ps | grep -q "prometheus"; then
    echo -e "${GREEN}✅ Prometheus is running${NC}"
else
    echo -e "${RED}❌ Prometheus failed to start${NC}"
    echo "Check logs: docker-compose -f docker-compose.monitoring.yml logs prometheus"
    exit 1
fi

if docker ps | grep -q "grafana"; then
    echo -e "${GREEN}✅ Grafana is running${NC}"
else
    echo -e "${RED}❌ Grafana failed to start${NC}"
    echo "Check logs: docker-compose -f docker-compose.monitoring.yml logs grafana"
    exit 1
fi

if docker ps | grep -q "alertmanager"; then
    echo -e "${GREEN}✅ Alertmanager is running${NC}"
else
    echo -e "${RED}❌ Alertmanager failed to start${NC}"
    echo "Check logs: docker-compose -f docker-compose.monitoring.yml logs alertmanager"
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Monitoring stack is ready!"
echo "========================================="
echo ""
echo "Access your dashboards:"
echo ""
echo "  🔹 Prometheus:   http://localhost:9090"
echo "  🔹 Grafana:      http://localhost:3001"
echo "     Username:     admin"
echo "     Password:     (the password you set)"
echo "  🔹 Alertmanager: http://localhost:9093"
echo ""
echo "Next steps:"
echo ""
echo "1. Open Grafana: http://localhost:3001"
echo "2. Login with admin credentials"
echo "3. Add Prometheus data source:"
echo "   - URL: http://prometheus:9090"
echo "   - Access: Server (default)"
echo "4. Import Supabase dashboard (ID: 19822)"
echo ""
echo "Useful commands:"
echo ""
echo "  View logs:     docker-compose -f docker-compose.monitoring.yml logs -f"
echo "  Stop stack:    docker-compose -f docker-compose.monitoring.yml down"
echo "  Restart stack: docker-compose -f docker-compose.monitoring.yml restart"
echo ""
echo "Documentation: docs/PROMETHEUS_GRAFANA_QUICKSTART.md"
echo "========================================="
