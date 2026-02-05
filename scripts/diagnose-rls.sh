#!/usr/bin/env bash
# Diagnostic script to check and validate RLS test prerequisites

set -a
source "$(dirname "${BASH_SOURCE[0]}")/../.env.local"
set +a

echo "═══════════════════════════════════════════════════════════"
echo "RLS TEST DIAGNOSTIC CHECK"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check 1: URL
if [[ -z $SUPABASE_URL ]]; then
	echo "❌ SUPABASE_URL is not set"
else
	echo "✅ SUPABASE_URL: $SUPABASE_URL"
fi

# Check 2: Anon key
if [[ -z $SUPABASE_ANON_KEY ]]; then
	echo "❌ SUPABASE_ANON_KEY is not set"
elif [[ $SUPABASE_ANON_KEY == *"..."* ]]; then
	echo "⚠️  SUPABASE_ANON_KEY appears incomplete (contains '...')"
	echo "   Value: ${SUPABASE_ANON_KEY:0:50}..."
else
	echo "✅ SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:50}..."
	echo "   Length: ${#SUPABASE_ANON_KEY} characters"
fi

# Check 3: Service role key
if [[ -z $SUPABASE_SERVICE_ROLE_KEY ]]; then
	echo "❌ SUPABASE_SERVICE_ROLE_KEY is not set"
elif [[ $SUPABASE_SERVICE_ROLE_KEY == *"..."* ]]; then
	echo "❌ SUPABASE_SERVICE_ROLE_KEY is INCOMPLETE (contains '...')"
	echo "   Current value: ${SUPABASE_SERVICE_ROLE_KEY:0:50}..."
	echo "   ⚠️  Error: Invalid API key - this is why tests are failing!"
else
	echo "✅ SUPABASE_SERVICE_ROLE_KEY: ${SUPABASE_SERVICE_ROLE_KEY:0:50}..."
	echo "   Length: ${#SUPABASE_SERVICE_ROLE_KEY} characters"
fi

# Check 4: Test user email
if [[ -z $TEST_USER_EMAIL ]]; then
	echo "❌ TEST_USER_EMAIL is not set"
else
	echo "✅ TEST_USER_EMAIL: $TEST_USER_EMAIL"
fi

# Check 5: Test user password
if [[ -z $TEST_USER_PASSWORD ]]; then
	echo "❌ TEST_USER_PASSWORD is not set"
elif [[ $TEST_USER_PASSWORD == "YourSecurePassword123!"* ]]; then
	echo "⚠️  TEST_USER_PASSWORD appears to be placeholder"
	echo "   ⚠️  Error: Invalid login credentials - user doesn't exist!"
else
	echo "✅ TEST_USER_PASSWORD is set (not displaying)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "WHAT YOU NEED TO DO:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "1. Get SUPABASE_SERVICE_ROLE_KEY (FULL, no '...' at end)"
echo "   👉 Visit: https://supabase.com/dashboard/project/goxdevkqozomyhsyxhte/settings/api"
echo '   👉 Find the section "Project API keys"'
echo '   👉 Look for the "service_role" key (NOT anon)'
echo "   👉 Click the 📋 copy icon to copy the ENTIRE token"
echo ""
echo "2. Create test user in Supabase"
echo "   👉 Go to: Authentication → Users → Add User"
echo "   👉 Email: test-user@abaco.com"
echo "   👉 Password: (your choice - strong password)"
echo "   👉 Remember this password for TEST_USER_PASSWORD"
echo ""
echo "3. Update .env.local with FULL keys (no '...' anywhere)"
echo "   nano .env.local"
echo ""
echo "4. Re-run tests:"
echo "   source scripts/load-env.sh && node scripts/test-rls.js"
echo ""
