#!/bin/bash

###############################################################################
# Post-Deployment Monitoring and Health Check
#
# This script validates a deployed instance of Abaco Analytics Dashboard:
# 1. Health endpoint checks
# 2. App responsiveness
# 3. Error rate monitoring
# 4. Basic functionality tests
#
# Usage:
#   ./scripts/monitor_deployment.sh [URL] [DURATION_HOURS]
#
# Examples:
#   ./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 1
#   ./scripts/monitor_deployment.sh https://abaco-analytics-dashboard.azurewebsites.net 24
#
# Requirements:
#   - curl
#   - jq (optional, for JSON parsing)
###############################################################################

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Default parameters
APP_URL="${1:-https://abaco-analytics-dashboard.azurewebsites.net}"
MONITOR_HOURS="${2:-1}"
HEALTH_PATH="/?page=health"
CHECK_INTERVAL=60  # seconds

# Parse URL
if [[ ! "$APP_URL" =~ ^https?:// ]]; then
    APP_URL="https://$APP_URL"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Post-Deployment Health Monitor${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo "Target URL: $APP_URL"
echo "Monitor Duration: $MONITOR_HOURS hour(s)"
echo "Check Interval: $CHECK_INTERVAL seconds"
echo ""

# Calculate end time
END_TIME=$(($(date +%s) + MONITOR_HOURS * 3600))

# Counters
TOTAL_CHECKS=0
SUCCESSFUL_CHECKS=0
FAILED_CHECKS=0
ERROR_RESPONSES=0
TIMEOUTS=0

# Arrays for tracking latencies
declare -a LATENCIES

echo -e "${YELLOW}Starting health monitoring...${NC}\n"

while [[ $(date +%s) -lt $END_TIME ]]; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Health check with latency
    START_TIME=$(date +%s%N)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$APP_URL$HEALTH_PATH" 2>/dev/null || echo "000")
    END_TIME_CURL=$(date +%s%N)
    
    LATENCY=$(( (END_TIME_CURL - START_TIME) / 1000000 ))  # Convert nanoseconds to milliseconds
    LATENCIES+=($LATENCY)
    
    if [[ "$HTTP_CODE" == "200" ]]; then
        SUCCESSFUL_CHECKS=$((SUCCESSFUL_CHECKS + 1))
        STATUS="${GREEN}✅ OK${NC}"
    elif [[ "$HTTP_CODE" == "000" ]]; then
        TIMEOUTS=$((TIMEOUTS + 1))
        STATUS="${RED}❌ TIMEOUT${NC}"
    else
        ERROR_RESPONSES=$((ERROR_RESPONSES + 1))
        STATUS="${YELLOW}⚠️  HTTP $HTTP_CODE${NC}"
    fi
    
    printf "[%s] %s | Latency: %dms | Status: %b\n" "$TIMESTAMP" "Check #$TOTAL_CHECKS" "$LATENCY" "$STATUS"
    
    # Sleep before next check (unless we're at the end)
    if [[ $(date +%s) -lt $END_TIME ]]; then
        sleep $CHECK_INTERVAL
    fi
done

# Calculate statistics
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Health Check Summary${NC}"
echo -e "${BLUE}========================================${NC}\n"

SUCCESS_RATE=$((SUCCESSFUL_CHECKS * 100 / TOTAL_CHECKS))
echo "Total checks: $TOTAL_CHECKS"
echo "Successful: $SUCCESSFUL_CHECKS"
echo "Failed: $FAILED_CHECKS"
echo "Errors: $ERROR_RESPONSES"
echo "Timeouts: $TIMEOUTS"
echo "Success rate: $SUCCESS_RATE%"
echo ""

# Calculate latency statistics
if [[ ${#LATENCIES[@]} -gt 0 ]]; then
    IFS=$'\n' sorted_latencies=($(sort -n <<<"${LATENCIES[*]}"))
    MIN_LATENCY=${sorted_latencies[0]}
    MAX_LATENCY=${sorted_latencies[-1]}
    AVG_LATENCY=0
    
    for latency in "${LATENCIES[@]}"; do
        AVG_LATENCY=$((AVG_LATENCY + latency))
    done
    AVG_LATENCY=$((AVG_LATENCY / ${#LATENCIES[@]}))
    
    MEDIAN_INDEX=$(( (${#sorted_latencies[@]} - 1) / 2 ))
    MEDIAN_LATENCY=${sorted_latencies[$MEDIAN_INDEX]}
    
    echo "Latency Statistics:"
    echo "  Min:    ${MIN_LATENCY}ms"
    echo "  Max:    ${MAX_LATENCY}ms"
    echo "  Mean:   ${AVG_LATENCY}ms"
    echo "  Median: ${MEDIAN_LATENCY}ms"
    echo ""
fi

# Health assessment
echo -e "${BLUE}Assessment:${NC}"

if [[ $SUCCESS_RATE -ge 95 ]]; then
    echo -e "${GREEN}✅ HEALTHY${NC} - App is stable and responsive"
elif [[ $SUCCESS_RATE -ge 80 ]]; then
    echo -e "${YELLOW}⚠️  DEGRADED${NC} - Some issues detected, monitor closely"
else
    echo -e "${RED}❌ CRITICAL${NC} - Major issues, investigate immediately"
fi

echo ""
echo "Recommendations:"
if [[ $TIMEOUTS -gt 0 ]]; then
    echo "  - Timeout detected: Check App Service CPU/memory in Azure Portal"
fi
if [[ $ERROR_RESPONSES -gt 0 ]]; then
    echo "  - Error responses detected: Review App Service logs for details"
fi
if [[ ${MAX_LATENCY:-0} -gt 5000 ]]; then
    echo "  - High latency detected: Check database connections and network"
fi
if [[ $SUCCESS_RATE -lt 100 ]]; then
    echo "  - Continue monitoring for 24 hours to validate stability"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Monitoring complete!${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Exit with status based on health
if [[ $SUCCESS_RATE -ge 95 ]]; then
    exit 0
elif [[ $SUCCESS_RATE -ge 80 ]]; then
    exit 1  # Degraded
else
    exit 2  # Critical
fi
