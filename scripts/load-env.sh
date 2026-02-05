#!/usr/bin/env bash
# Load environment variables from .env.local
# Usage: source scripts/load-env.sh

set -a # automatically export all variables
# shellcheck source=../.env.local
source "$(dirname "${BASH_SOURCE[0]}")/../.env.local"
set +a

# Validate required variables
REQUIRED_VARS=(
	"SUPABASE_URL"
	"SUPABASE_ANON_KEY"
	"SUPABASE_SERVICE_ROLE_KEY"
	"TEST_USER_EMAIL"
	"TEST_USER_PASSWORD"
)

MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
	if [[ -z ${!var} ]] || [[ ${!var} == "REPLACE_WITH_"* ]]; then
		MISSING_VARS+=("${var}")
	fi
done

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
	echo "❌ ERROR: The following environment variables are missing or not configured:"
	for var in "${MISSING_VARS[@]}"; do
		echo "   - $var"
	done
	echo ""
	echo "📝 To fix this:"
	echo "   1. Go to: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api"
	echo "   2. Copy the 'anon' key → SUPABASE_ANON_KEY"
	echo "   3. Copy the 'service_role' key → SUPABASE_SERVICE_ROLE_KEY"
	echo "   4. Set TEST_USER_EMAIL and TEST_USER_PASSWORD for a test user"
	echo "   5. Edit .env.local with the actual values"
	return 1
else
	echo "✅ Environment variables loaded successfully"
	echo "   URL: ${SUPABASE_URL}"
	echo "   Service Key: ${SUPABASE_SERVICE_ROLE_KEY:0:20}..."
	echo "   Test User: ${TEST_USER_EMAIL}"
fi
