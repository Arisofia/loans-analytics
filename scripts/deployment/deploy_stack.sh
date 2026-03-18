#!/bin/bash

# Complete Stack Deployment Script
# Deploys the full Abaco Loans Analytics Platform

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "🚀 Abaco Loans Analytics - Full Stack Deployment"
echo "=========================================="
echo ""

# Check Docker
if ! command -v docker &>/dev/null; then
	echo -e "${YELLOW}⚠️  Docker not found. Installing Docker...${NC}"
	curl -fsSL https://get.docker.com -o get-docker.sh
	sudo sh get-docker.sh
	rm get-docker.sh
fi

# Resolve compose command across environments
DOCKER_COMPOSE_CMD=()
if command -v docker-compose &>/dev/null; then
	DOCKER_COMPOSE_CMD=("docker-compose")
elif docker compose version &>/dev/null; then
	DOCKER_COMPOSE_CMD=("docker" "compose")
else
	echo -e "${YELLOW}⚠️  Docker Compose not found. Installing...${NC}"
	sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
	sudo chmod +x /usr/local/bin/docker-compose
	DOCKER_COMPOSE_CMD=("docker-compose")
fi

echo -e "${GREEN}✅ Docker and Docker Compose are ready (${DOCKER_COMPOSE_CMD[*]})${NC}"
echo ""

# Check if canonical input data exists
CANONICAL_INPUT="data/samples/abaco_sample_data_20260202.csv"
if [ ! -f "$CANONICAL_INPUT" ]; then
	echo -e "${YELLOW}⚠️  Canonical input dataset not found: $CANONICAL_INPUT${NC}"
	echo -e "${YELLOW}   Prepare data inputs before deploying the stack.${NC}"
	exit 1
fi
echo -e "${GREEN}✅ Input dataset found: $CANONICAL_INPUT${NC}"

# Build and start services
echo -e "${BLUE}🏗️  Building Docker images...${NC}"
"${DOCKER_COMPOSE_CMD[@]}" --profile dashboard build dashboard agent-scheduler

echo ""
echo -e "${BLUE}🚀 Starting services...${NC}"
"${DOCKER_COMPOSE_CMD[@]}" --profile dashboard up -d dashboard agent-scheduler

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "=========================================="
echo "📊 Services Running:"
echo "=========================================="
echo ""
echo "  🌐 Dashboard:    http://localhost:8501"
echo "  🤖 Agent Scheduler: Running in background (daily at 2 AM)"
echo ""
echo "=========================================="
echo "📋 Management Commands:"
echo "=========================================="
echo ""
echo "  View logs:       ${DOCKER_COMPOSE_CMD[*]} --profile dashboard logs -f"
echo "  Stop services:   ${DOCKER_COMPOSE_CMD[*]} --profile dashboard down"
echo "  Restart:         ${DOCKER_COMPOSE_CMD[*]} --profile dashboard restart"
echo "  Status:          ${DOCKER_COMPOSE_CMD[*]} --profile dashboard ps"
echo ""
echo "=========================================="
echo "📚 Quick Start:"
echo "=========================================="
echo ""
echo "1. Open http://localhost:8501 in your browser"
echo "2. Click 'Load Sample Data (Spanish Loans)' in sidebar"
echo "3. Explore the 5 dashboard tabs:"
echo "   • Delinquency Trends"
echo "   • Risk Distribution"
echo "   • Regional Analysis"
echo "   • Vintage Analysis"
echo "   • Loan Table (filterable, searchable)"
echo ""
echo "=========================================="
