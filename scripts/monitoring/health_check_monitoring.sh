#!/bin/bash
#
# Monitoring Stack Health Check
# Automated verification of all monitoring services
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Monitoring Stack Health Check${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

EXIT_CODE=0

# Check Docker
echo -e "${BLUE}Docker:${NC}"
if docker ps >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "  ${RED}✗ Docker daemon is not running${NC}"
    EXIT_CODE=1
fi
echo ""

# Check containers
echo -e "${BLUE}Containers:${NC}"
CONTAINERS=("prometheus" "grafana" "alertmanager")
for container in "${CONTAINERS[@]}"; do
    if docker ps --filter "name=$container" --filter "status=running" --format '{{.Names}}' | grep -q "^${container}$"; then
        UPTIME=$(docker ps --filter "name=$container" --format '{{.Status}}')
        echo -e "  ${GREEN}✓ $container${NC} - $UPTIME"
    else
        echo -e "  ${RED}✗ $container is not running${NC}"
        EXIT_CODE=1
    fi
done
echo ""

# Check service endpoints
echo -e "${BLUE}Service Health:${NC}"

# Prometheus
if curl -sf http://localhost:9090/-/healthy >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Prometheus${NC} - http://localhost:9090"
else
    echo -e "  ${RED}✗ Prometheus is not responding${NC}"
    EXIT_CODE=1
fi

# Grafana
if curl -sf http://localhost:3001/api/health >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Grafana${NC} - http://localhost:3001"
else
    echo -e "  ${RED}✗ Grafana is not responding${NC}"
    EXIT_CODE=1
fi

# Alertmanager
if curl -sf http://localhost:9093/-/healthy >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓ Alertmanager${NC} - http://localhost:9093"
else
    echo -e "  ${RED}✗ Alertmanager is not responding${NC}"
    EXIT_CODE=1
fi
echo ""

# Check Prometheus targets
echo -e "${BLUE}Prometheus Targets:${NC}"
TARGETS_JSON=$(curl -s http://localhost:9090/api/v1/targets 2>/dev/null || echo "{}")

# Critical targets that must be UP
CRITICAL_TARGETS=("supabase-db" "prometheus")

if command -v python3 >/dev/null 2>&1 && [[ "$TARGETS_JSON" != "{}" ]]; then
    echo "$TARGETS_JSON" | python3 -c "
import json
import sys

critical = ['supabase-db', 'prometheus']

try:
    data = json.load(sys.stdin)
    targets = data.get('data', {}).get('activeTargets', [])

    critical_failed = False
    for target in targets:
        job = target.get('labels', {}).get('job', 'unknown')
        health = target.get('health', 'unknown')

        if health == 'up':
            print(f'  \033[0;32m✓ {job}\033[0m')
        else:
            if job in critical:
                print(f'  \033[0;31m✗ {job}\033[0m - CRITICAL - {health}')
                critical_failed = True
            else:
                print(f'  \033[1;33m⚠ {job}\033[0m - {health} (optional service)')

    if critical_failed:
        sys.exit(1)
except json.JSONDecodeError as e:
    print(f'  \033[1;33m⚠ Could not parse targets: {e}\033[0m')
except Exception as e:
    print(f'  \033[1;33m⚠ Error checking targets: {e}\033[0m')
"
    if [[ $? -ne 0 ]]; then
        EXIT_CODE=1
    fi
else
    echo -e "  ${YELLOW}⚠ Could not retrieve target status${NC}"
fi
echo ""

# Check Grafana datasource
echo -e "${BLUE}Grafana Configuration:${NC}"
DATASOURCES=$(curl -s -u admin:${GRAFANA_ADMIN_PASSWORD:-admin123} http://localhost:3001/api/datasources 2>/dev/null || echo "[]")

if echo "$DATASOURCES" | grep -q "Prometheus"; then
    echo -e "  ${GREEN}✓ Prometheus datasource configured${NC}"
else
    echo -e "  ${YELLOW}⚠ Prometheus datasource not found${NC}"
    echo -e "    Run: make monitoring-start"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✓ All checks passed - Stack is healthy${NC}"
else
    echo -e "${RED}✗ Some checks failed - Review above${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo -e "  1. Restart stack: ${BLUE}make monitoring-stop && make monitoring-start${NC}"
    echo -e "  2. View logs:     ${BLUE}make monitoring-logs${NC}"
    echo -e "  3. Check Docker:  ${BLUE}docker ps -a${NC}"
fi
echo -e "${BLUE}========================================${NC}"

exit $EXIT_CODE
