#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

WEBAPP_NAME="abaco-analytics-dashboard"
RESOURCE_GROUP="AI-MultiAgent-Ecosystem-RG"
APPINSIGHTS_NAME="abaco-insights"
ALERT_ACTION_GROUP="AbacoCriticalAlerts"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ABACO PRODUCTION MONITORING SETUP                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

check_requirements() {
    echo -e "${YELLOW}[1/5] Checking prerequisites...${NC}"

    if ! command -v az &> /dev/null; then
        echo -e "${RED}❌ Azure CLI not found. Install: brew install azure-cli${NC}"
        exit 1
    fi

    if ! az account show &> /dev/null; then
        echo -e "${YELLOW}⚠️ Not logged in to Azure. Run: az login${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ Prerequisites met${NC}\n"
}

create_action_group() {
    echo -e "${YELLOW}[2/5] Setting up alert action group...${NC}"

    local EMAIL="${ALERT_EMAIL:-your-email@example.com}"

    # Create action group
    az monitor action-group create \
        --resource-group $RESOURCE_GROUP \
        --name $ALERT_ACTION_GROUP \
        --short-name "AbacoCrit" \
        2>/dev/null || echo -e "${YELLOW}⚠️ Action group may already exist${NC}"

    # Add email receiver
    az monitor action-group receiver email add \
        --action-group-name $ALERT_ACTION_GROUP \
        --resource-group $RESOURCE_GROUP \
        --name "CriticalAlertEmail" \
        --email-receiver $EMAIL \
        2>/dev/null || true

    echo -e "${GREEN}✅ Action group configured${NC}\n"
}

create_alerts() {
    echo -e "${YELLOW}[3/5] Creating monitoring alerts...${NC}"

    # Alert 1: Response Time Degradation
    echo "   • Creating response time alert..."
    az monitor metrics alert create \
        --name "Dashboard-HighResponseTime" \
        --resource-group $RESOURCE_GROUP \
        --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEBAPP_NAME" \
        --condition "avg ResponseTime > 5000" \
        --description "Alert when dashboard response time exceeds 5 seconds" \
        --evaluation-frequency 1m \
        --window-size 5m \
        --action $ALERT_ACTION_GROUP \
        2>/dev/null || echo -e "      ${YELLOW}⚠️ May already exist${NC}"

    # Alert 2: HTTP Error Rate
    echo "   • Creating HTTP error alert..."
    az monitor metrics alert create \
        --name "Dashboard-HighErrorRate" \
        --resource-group $RESOURCE_GROUP \
        --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEBAPP_NAME" \
        --condition "total Http5xx > 10" \
        --description "Alert when 5xx errors exceed 10 in 5 minutes" \
        --evaluation-frequency 1m \
        --window-size 5m \
        --action $ALERT_ACTION_GROUP \
        2>/dev/null || echo -e "      ${YELLOW}⚠️ May already exist${NC}"

    # Alert 3: App Service Down
    echo "   • Creating availability alert..."
    az monitor metrics alert create \
        --name "Dashboard-Unavailable" \
        --resource-group $RESOURCE_GROUP \
        --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$WEBAPP_NAME" \
        --condition "avg AvailabilityPercentage < 99" \
        --description "Alert when dashboard availability drops below 99%" \
        --evaluation-frequency 1m \
        --window-size 5m \
        --action $ALERT_ACTION_GROUP \
        2>/dev/null || echo -e "      ${YELLOW}⚠️ May already exist${NC}"

    echo -e "${GREEN}✅ Alerts configured${NC}\n"
}

create_log_alerts() {
    echo -e "${YELLOW}[4/5] Creating log-based alerts...${NC}"

    # Find Application Insights resource ID
    local APPINSIGHTS_ID=$(az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP \
        --query id -o tsv 2>/dev/null)

    if [ -z "$APPINSIGHTS_ID" ]; then
        echo -e "${YELLOW}⚠️ Application Insights not found. Skipping log alerts.${NC}"
        return
    fi

    echo "   • Creating exception rate alert..."
    az monitor log-analytics alert create \
        --name "Dashboard-HighExceptionRate" \
        --resource-group $RESOURCE_GROUP \
        --scopes $APPINSIGHTS_ID \
        --condition "exceptions | summarize count() by tostring(type)" \
        --description "Alert on high exception rates" \
        --window-size 15m \
        --action $ALERT_ACTION_GROUP \
        2>/dev/null || echo -e "      ${YELLOW}⚠️ May require Log Analytics workspace${NC}"

    echo -e "${GREEN}✅ Log alerts configured${NC}\n"
}

create_dashboard() {
    echo -e "${YELLOW}[5/5] Creating monitoring dashboard...${NC}"

    echo "   • Dashboard creation requires Azure Portal"
    echo "     Manual steps:"
    echo "     1. Go to Azure Portal → Monitor → Dashboards"
    echo "     2. Create new dashboard"
    echo "     3. Add tiles for:"
    echo "        - Application response time"
    echo "        - Error rate (5xx errors)"
    echo "        - Availability percentage"
    echo "        - Request count"
    echo ""
    echo -e "${GREEN}✅ Dashboard steps provided${NC}\n"
}

verify_setup() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   VERIFICATION                                             ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # List created alerts
    echo -e "${YELLOW}Created Alerts:${NC}"
    az monitor metrics alert list --resource-group $RESOURCE_GROUP --query "[].name" -o tsv | sed 's/^/  • /'

    echo ""
    echo -e "${GREEN}✅ Monitoring setup complete!${NC}"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Configure email for $EMAIL to receive alerts"
    echo "  2. Add Slack webhooks to action group for real-time notifications"
    echo "  3. Create PowerBI dashboard for executive reporting"
    echo "  4. Set up daily health report via automation"
    echo ""
}

# Main execution
check_requirements
create_action_group
create_alerts
create_log_alerts
create_dashboard
verify_setup
