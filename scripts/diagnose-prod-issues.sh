#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "======================================"
echo "ABACO PRODUCTION DIAGNOSTIC TOOL"
echo "======================================"
echo ""

WEBAPP_NAME="abaco-analytics-dashboard"
RESOURCE_GROUP="AI-MultiAgent-Ecosystem-RG"

echo -e "${YELLOW}PROD-001: DASHBOARD SERVICE HEALTH${NC}"
echo "========================================"

echo -e "\n1️⃣ Checking Azure App Service status..."
if command -v az &> /dev/null; then
    APP_STATUS=$(az webapp show --name $WEBAPP_NAME --resource-group $RESOURCE_GROUP --query "state" -o tsv 2>/dev/null)
    if [ $? -eq 0 ]; then
        if [ "$APP_STATUS" = "Running" ]; then
            echo -e "${GREEN}✅ App Service Status: $APP_STATUS${NC}"
        else
            echo -e "${RED}🔴 App Service Status: $APP_STATUS${NC}"
        fi
    else
        echo -e "${RED}❌ Cannot access Azure CLI. Run: az login${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Azure CLI not installed. Install via: brew install azure-cli${NC}"
fi

echo -e "\n2️⃣ Testing dashboard URL connectivity..."
DASHBOARD_URL="https://${WEBAPP_NAME}.azurewebsites.net"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -I $DASHBOARD_URL 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Dashboard accessible (HTTP $HTTP_CODE)${NC}"
elif [ "$HTTP_CODE" = "000" ]; then
    echo -e "${RED}🔴 DNS resolution failed - try restarting Azure App Service${NC}"
else
    echo -e "${YELLOW}⚠️ HTTP Status: $HTTP_CODE (check logs for details)${NC}"
fi

echo -e "\n3️⃣ Checking dashboard requirements..."
if [ -f "dashboard/requirements.txt" ]; then
    echo -e "${GREEN}✅ Found dashboard/requirements.txt${NC}"
    echo "   Dependencies:"
    head -10 dashboard/requirements.txt | sed 's/^/   - /'
else
    echo -e "${RED}❌ Missing dashboard/requirements.txt${NC}"
fi

echo -e "\n4️⃣ Checking for database connection configuration..."
if [ -f "dashboard/app.py" ]; then
    if grep -q "DATABASE\|database\|DB_\|sqlalchemy\|psycopg" dashboard/app.py; then
        echo -e "${GREEN}✅ Database references found in dashboard/app.py${NC}"
        grep -i "DATABASE\|DB_\|sqlalchemy\|psycopg" dashboard/app.py | head -5 | sed 's/^/   /'
    else
        echo -e "${YELLOW}⚠️ No obvious database references in dashboard/app.py${NC}"
    fi
fi

echo -e "\n\n${YELLOW}PROD-003: DATA PIPELINE INVESTIGATION${NC}"
echo "========================================"

echo -e "\n5️⃣ Checking pipeline configurations..."
PIPELINE_FILES=(
    "src/pipeline/orchestrator.py"
    "src/abaco_pipeline/main.py"
    ".github/workflows/daily-ingest.yml"
    ".github/workflows/cascade_ingest.yml"
)

for file in "${PIPELINE_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ Found: $file${NC}"
    else
        echo -e "${RED}❌ Missing: $file${NC}"
    fi
done

echo -e "\n6️⃣ Checking for API key configuration..."
if [ -f "src/pipeline/orchestrator.py" ] || [ -f "src/abaco_pipeline/main.py" ]; then
    echo "   Searching for API key references..."
    for file in src/pipeline/*.py src/abaco_pipeline/*.py; do
        if [ -f "$file" ]; then
            if grep -q "HUBSPOT\|OPENAI\|API_KEY\|api_key" "$file" 2>/dev/null; then
                echo -e "   ${GREEN}✅ $(basename $file)${NC} - API key references found"
            fi
        fi
    done
fi

echo -e "\n7️⃣ Checking Python dependencies for pipelines..."
if [ -f "requirements.txt" ]; then
    DEPS=("polars" "pandas" "requests" "azure" "hubspot" "sqlalchemy")
    for dep in "${DEPS[@]}"; do
        if grep -q "^$dep\|^$dep[><=\-]" requirements.txt 2>/dev/null; then
            echo -e "${GREEN}✅ $dep${NC} - installed"
        fi
    done
fi

echo -e "\n\n${YELLOW}ARCHITECTURE DISCOVERY${NC}"
echo "========================================"

echo -e "\n8️⃣ Searching for database connection strings..."
echo "   Checking environment variable patterns..."
find . -name "*.py" -o -name "*.yml" -o -name "*.yaml" -o -name "*.sh" 2>/dev/null | xargs grep -l "DATABASE_URL\|DB_HOST\|DB_NAME\|SQLALCHEMY" 2>/dev/null | head -10 | sed 's/^/   Found: /'

echo -e "\n9️⃣ Checking for data storage references..."
find . -name "*.py" -path "*/pipeline/*" 2>/dev/null | xargs grep -l "\.csv\|\.parquet\|blob\|storage\|adls" 2>/dev/null | head -5 | sed 's/^/   /'

echo -e "\n\n${YELLOW}NEXT ACTIONS${NC}"
echo "========================================"
echo "1. Check Azure Portal → App Services → abaco-analytics-dashboard → Instances"
echo "2. Verify instance LW1SDLWK0006XP status (should be 'En ejecución')"
echo "3. Review GitHub Actions logs for failing pipelines"
echo "4. Provide database connection details for production data"
echo ""
