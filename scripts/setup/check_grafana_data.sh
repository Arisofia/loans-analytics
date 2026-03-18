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
echo -e "${BLUE}Grafana Data Troubleshooting${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Extract credentials
SUPABASE_PROJECT=$(grep "^SUPABASE_PROJECT_REF=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_URL="https://${SUPABASE_PROJECT}.supabase.co"
SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)

echo "📍 Project: ${SUPABASE_PROJECT}"
echo "🌐 URL: ${SUPABASE_URL}"
echo ""

# Step 1: Check monitoring tables
echo -e "${BLUE}Step 1: Checking monitoring tables...${NC}"
echo ""

# Check kpi_definitions
echo -n "  monitoring.kpi_definitions: "
check=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_definitions?select=count()" 2>/dev/null | jq '.[0].count' 2>/dev/null || echo "ERROR")

if [ "$check" != "ERROR" ]; then
    if [ -z "$check" ] || [ "$check" = "null" ]; then
        echo -e "${RED}❌ Table not found${NC}"
    else
        echo -e "${GREEN}✅ Found ${check} KPI definitions${NC}"
    fi
else
    echo -e "${RED}❌ Cannot access table${NC}"
fi

# Check kpi_values
echo -n "  monitoring.kpi_values: "
check=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_values?select=count()" 2>/dev/null | jq '.[0].count' 2>/dev/null || echo "ERROR")

if [ "$check" != "ERROR" ]; then
    if [ -z "$check" ] || [ "$check" = "null" ]; then
        echo -e "${RED}❌ Table not found${NC}"
    else
        echo -e "${GREEN}✅ Found ${check} KPI values${NC}"
    fi
else
    echo -e "${RED}❌ Cannot access table${NC}"
fi

echo ""

# Step 2: Check Grafana datasource
echo -e "${BLUE}Step 2: Checking Grafana datasource...${NC}"

# Test datasource
test_result=$(curl -s -u admin:admin123 \
  -X POST \
  -H "Content-Type: application/json" \
  "http://localhost:3001/api/datasources/1/query" \
  -d '{"queries":[{"refId":"A","rawSql":"SELECT 1"}]}' 2>/dev/null)

if echo "$test_result" | jq . &>/dev/null 2>&1; then
    echo -e "  ${GREEN}✅ Datasource is responding${NC}"
else
    echo -e "  ${YELLOW}⚠️  Could not test datasource${NC}"
fi

echo ""

# Step 3: Show what needs to be done
echo -e "${BLUE}Step 3: Next Actions${NC}"
echo ""

kpi_defs=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_definitions?select=count()" 2>/dev/null | jq '.[0].count' 2>/dev/null || echo "0")

kpi_vals=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_values?select=count()" 2>/dev/null | jq '.[0].count' 2>/dev/null || echo "0")

if [ "$kpi_defs" = "0" ] || [ -z "$kpi_defs" ]; then
    echo -e "${RED}❌ monitoring.kpi_definitions is empty or doesn't exist${NC}"
    echo ""
    echo "   1. Go to: https://supabase.com/dashboard/project/${SUPABASE_PROJECT}/sql"
    echo "   2. Create the table and definitions:"
    echo ""
    echo "   CREATE SCHEMA IF NOT EXISTS monitoring;"
    echo ""
    echo "   CREATE TABLE IF NOT EXISTS monitoring.kpi_definitions ("
    echo "     id SERIAL PRIMARY KEY,"
    echo "     name TEXT UNIQUE NOT NULL,"
    echo "     category TEXT NOT NULL,"
    echo "     description TEXT,"
    echo "     unit TEXT,"
    echo "     created_at TIMESTAMPTZ DEFAULT NOW()"
    echo "   );"
    echo ""
    echo "   CREATE TABLE IF NOT EXISTS monitoring.kpi_values ("
    echo "     id SERIAL PRIMARY KEY,"
    echo "     kpi_id INTEGER REFERENCES monitoring.kpi_definitions(id),"
    echo "     value NUMERIC NOT NULL,"
    echo "     timestamp TIMESTAMPTZ NOT NULL,"
    echo "     status TEXT,"
    echo "     created_at TIMESTAMPTZ DEFAULT NOW()"
    echo "   );"
    echo ""
    echo "   Then run:"
    echo "   python scripts/setup/create_tables_via_api.py"
    echo ""
else
    echo -e "${GREEN}✅ monitoring.kpi_definitions exists with ${kpi_defs} entries${NC}"
fi

echo ""

if [ "$kpi_vals" = "0" ] || [ -z "$kpi_vals" ]; then
    echo -e "${RED}❌ monitoring.kpi_values is empty${NC}"
    echo ""
    echo "   Run the data pipeline to populate:"
    echo "   python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv"
    echo ""
else
    echo -e "${GREEN}✅ monitoring.kpi_values has ${kpi_vals} records${NC}"
fi

echo ""

# Step 4: Display sample query
echo -e "${BLUE}Step 4: Query latest KPI values${NC}"
echo ""

sample=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_values?order=created_at.desc&limit=3" 2>/dev/null | jq '.[] | {kpi_id, value, timestamp}' 2>/dev/null || echo "No data")

if [ "$sample" != "No data" ]; then
    echo -e "${GREEN}✅ Latest KPI values:${NC}"
    echo "$sample" | head -20
else
    echo -e "${YELLOW}⚠️  No KPI values found${NC}"
fi

echo ""
echo -e "${BLUE}================================================${NC}"

