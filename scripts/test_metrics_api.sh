#!/bin/bash
# Test Supabase Metrics API connectivity
# Usage: bash scripts/test_metrics_api.sh

set -e

# Load environment variables
source "$(dirname "$0")/load_env.sh" > /dev/null 2>&1

echo "🔍 Testing Supabase Metrics API..."
echo "   Project: ${SUPABASE_PROJECT_REF}"
echo "   Endpoint: https://${SUPABASE_PROJECT_REF}.supabase.co/customer/v1/privileged/metrics"
echo ""

# Check if SECRET_API_KEY is set
if [ -z "$SUPABASE_SECRET_API_KEY" ]; then
    echo "❌ ERROR: SUPABASE_SECRET_API_KEY not set"
    echo "   Edit .env.local and add your Secret API Key"
    exit 1
fi

echo "🔐 Secret API Key: ${SUPABASE_SECRET_API_KEY:0:15}..."
echo ""

# Make request to Metrics API (using basic auth: service_role:secret_key)
echo "📡 Sending request..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
    --user "service_role:${SUPABASE_SECRET_API_KEY}" \
    "https://${SUPABASE_PROJECT_REF}.supabase.co/customer/v1/privileged/metrics")

# Extract HTTP status code (last line)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "📊 HTTP Status: ${HTTP_CODE}"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Metrics API is accessible"
    echo ""
    echo "Sample metrics (first 30 lines):"
    echo "=================================="
    echo "$BODY" | head -30
    echo "=================================="
    echo ""
    METRIC_COUNT=$(echo "$BODY" | grep -c "^[a-z]" || true)
    echo "📈 Total metrics found: ~${METRIC_COUNT}"
    echo ""
    echo "✓ You can now configure Prometheus to scrape this endpoint"
    echo "  See: config/prometheus.yml"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ AUTHENTICATION FAILED"
    echo "   Your Secret API Key may be incorrect or expired"
    echo ""
    echo "Response:"
    echo "$BODY"
    echo ""
    echo "🔧 Fix: Get a new Secret API Key from:"
    echo "   https://supabase.com/dashboard/project/${SUPABASE_PROJECT_REF}/settings/api"
elif [ "$HTTP_CODE" = "404" ]; then
    echo "❌ ENDPOINT NOT FOUND"
    echo "   The Metrics API endpoint may not be available for your project"
    echo ""
    echo "Response:"
    echo "$BODY"
    echo ""
    echo "💡 Check if your Supabase project tier supports Metrics API"
else
    echo "⚠️  UNEXPECTED RESPONSE"
    echo ""
    echo "Response body:"
    echo "$BODY"
    echo ""
    echo "🔍 Debug info:"
    echo "   - Check if PROJECT_REF is correct: ${SUPABASE_PROJECT_REF}"
    echo "   - Verify Secret API Key in Supabase Dashboard"
    echo "   - Ensure your project has Metrics API enabled"
fi
