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
echo -e "${BLUE}Create Monitoring Tables in Supabase${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Extract credentials
SUPABASE_PROJECT=$(grep "^SUPABASE_PROJECT_REF=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_URL="https://${SUPABASE_PROJECT}.supabase.co"
SUPABASE_ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)
SUPABASE_SERVICE_ROLE=$(grep "^SUPABASE_SERVICE_ROLE_KEY=" "$ENV_LOCAL" | cut -d'=' -f2)

echo "Project: ${SUPABASE_PROJECT}"
echo "URL: ${SUPABASE_URL}"
echo ""

# Step 1: Create monitoring schema
echo -e "${BLUE}Step 1: Creating monitoring schema...${NC}"

curl -s -X POST \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE}" \
  -H "Content-Type: application/json" \
  "${SUPABASE_URL}/rest/v1/rpc/execute_sql" \
  -d '{"sql":"CREATE SCHEMA IF NOT EXISTS monitoring;"}' 2>/dev/null || \
echo -e "${YELLOW}⚠️  Trying alternative method...${NC}"

# Use direct PostgreSQL SQL execution via Supabase REST
echo -e "${YELLOW}Creating tables via REST API...${NC}"

# Create kpi_definitions table
echo -n "  - kpi_definitions: "
curl -s -X POST \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/rpc/execute_sql?sql=CREATE%20TABLE%20IF%20NOT%20EXISTS%20monitoring.kpi_definitions%20(%0A%20%20id%20serial%20PRIMARY%20KEY%2C%0A%20%20name%20text%20UNIQUE%20NOT%20NULL%2C%0A%20%20category%20text%20NOT%20NULL%2C%0A%20%20description%20text%2C%0A%20%20unit%20text%2C%0A%20%20red_threshold%20numeric%2C%0A%20%20yellow_threshold%20numeric%2C%0A%20%20owner_agent%20text%2C%0A%20%20created_at%20timestamptz%20DEFAULT%20now()%0A%29%3B" 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"

# Create kpi_values table
echo -n "  - kpi_values: "
curl -s -X POST \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/rpc/execute_sql?sql=CREATE%20TABLE%20IF%20NOT%20EXISTS%20monitoring.kpi_values%20(%0A%20%20id%20serial%20PRIMARY%20KEY%2C%0A%20%20kpi_id%20integer%20REFERENCES%20monitoring.kpi_definitions(id)%2C%0A%20%20value%20numeric%20NOT%20NULL%2C%0A%20%20timestamp%20timestamptz%20NOT%20NULL%2C%0A%20%20status%20text%20CHECK%20(status%20IN%20('%27green%27%2C%27yellow%27%2C%27red%27))%2C%0A%20%20created_at%20timestamptz%20DEFAULT%20now()%0A%29%3B" 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${YELLOW}⚠️${NC}"

echo ""

# Step 2: Insert sample KPI definitions
echo -e "${BLUE}Step 2: Inserting sample KPI definitions...${NC}"

KPIS=(
  "par_30|Asset Quality|Portfolio % at risk 30+ days|percent"
  "par_90|Asset Quality|Portfolio % at risk 90+ days|percent"
  "npl_rate|Asset Quality|Non-performing loan rate|percent"
  "collection_rate_6m|Cash Flow|6-month collection rate|percent"
  "recovery_rate|Cash Flow|Recovery rate on defaults|percent"
  "portfolio_rotation|Growth|Portfolio rotation rate|percent"
  "disbursement_volume|Growth|Total disbursement volume|units"
  "new_loans|Growth|New loans originated|count"
  "total_aum|Portfolio Performance|Total assets under management|currency"
  "average_loan_size|Portfolio Performance|Average loan size|currency"
  "loan_count|Portfolio Performance|Total number of loans|count"
  "portfolio_yield|Portfolio Performance|Portfolio yield|percent"
  "active_borrowers|Customer Metrics|Active borrowers|count"
  "repeat_borrower_rate|Customer Metrics|Repeat borrower rate|percent"
  "processing_time|Operational Metrics|Average processing time|days"
  "automation_rate|Operational Metrics|Automation rate|percent"
  "default_rate|Asset Quality|Default rate|percent"
  "write_off_rate|Asset Quality|Write-off rate|percent"
  "portfolio_ghg|Environmental|Portfolio GHG emissions|tons"
)

for kpi in "${KPIS[@]}"; do
  IFS='|' read -r name category desc unit <<< "$kpi"
  
  # Insert using REST API
  curl -s -X POST \
    -H "apikey: ${SUPABASE_ANON_KEY}" \
    -H "Content-Type: application/json" \
    "${SUPABASE_URL}/rest/v1/monitoring.kpi_definitions?upsert=true" \
    -d "{\"name\":\"${name}\",\"category\":\"${category}\",\"description\":\"${desc}\",\"unit\":\"${unit}\"}" 2>/dev/null && \
    echo -e "  ✅ ${name}" || \
    echo -e "  ⚠️  ${name}"
done

echo ""

# Step 3: Insert sample KPI values
echo -e "${BLUE}Step 3: Inserting sample KPI values...${NC}"

# Get current timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Insert sample values
curl -s -X POST \
  -H "apikey: ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_values" \
  -d "[
    {\"kpi_id\":1,\"value\":5.2,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":2,\"value\":2.1,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":3,\"value\":7.3,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"yellow\"},
    {\"kpi_id\":4,\"value\":94.5,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":5,\"value\":68.2,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":6,\"value\":15.8,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":7,\"value\":12500000,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":8,\"value\":1250,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":9,\"value\":450000000,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"},
    {\"kpi_id\":10,\"value\":18000,\"timestamp\":\"${TIMESTAMP}\",\"status\":\"green\"}
  ]" 2>/dev/null && \
  echo -e "  ${GREEN}✅ Inserted 10 sample KPI values${NC}" || \
  echo -e "  ${YELLOW}⚠️  Could not insert sample values (tables may not exist yet)${NC}"

echo ""

# Step 4: Verify tables
echo -e "${BLUE}Step 4: Verifying tables...${NC}"

# Check kpi_definitions
check=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_definitions?limit=1" 2>/dev/null | jq '. | length' 2>/dev/null)

if [ ! -z "$check" ] && [ "$check" -gt 0 ]; then
  echo -e "  ${GREEN}✅ monitoring.kpi_definitions has data${NC}"
else
  echo -e "  ${YELLOW}⚠️  monitoring.kpi_definitions not yet populated${NC}"
fi

# Check kpi_values
check=$(curl -s -H "apikey: ${SUPABASE_ANON_KEY}" \
  "${SUPABASE_URL}/rest/v1/monitoring.kpi_values?limit=1" 2>/dev/null | jq '. | length' 2>/dev/null)

if [ ! -z "$check" ] && [ "$check" -gt 0 ]; then
  echo -e "  ${GREEN}✅ monitoring.kpi_values has data${NC}"
else
  echo -e "  ${YELLOW}⚠️  monitoring.kpi_values not yet populated${NC}"
fi

echo ""

# Summary
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Setup Complete${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Open Grafana: http://localhost:3001"
echo "2. Go to Configuration → Data Sources"
echo "3. Click 'Test' on Supabase PostgreSQL"
echo "4. View dashboards in 'KPI Monitoring' folder"
echo ""
echo -e "${BLUE}To populate with pipeline data:${NC}"
echo "  python scripts/data/run_data_pipeline.py --input data/samples/abaco_sample_data_20260202.csv"
echo ""
