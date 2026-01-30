#!/bin/bash
# Load environment variables from .env.local with proper variable expansion
# Usage: source scripts/load_env.sh

# Find .env.local file
if [ -f .env.local ]; then
    ENV_FILE=.env.local
elif [ -f "$(dirname "$0")/../.env.local" ]; then
    ENV_FILE="$(dirname "$0")/../.env.local"
else
    echo "❌ Error: .env.local not found"
    return 1 2>/dev/null || exit 1
fi

# Export variables with proper expansion
set -a
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ $key =~ ^#.*$ ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove leading/trailing whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Evaluate variable expansions (e.g., ${VAR})
    eval "export $key=\"$value\""
done < "$ENV_FILE"
set +a

echo "✅ Environment variables loaded from .env.local"
echo ""
echo "Available Supabase variables:"
echo "  NEXT_PUBLIC_SUPABASE_URL: ${NEXT_PUBLIC_SUPABASE_URL:0:30}..."
echo "  SUPABASE_PROJECT_REF: ${SUPABASE_PROJECT_REF}"
echo "  SUPABASE_ANON_KEY: ${SUPABASE_ANON_KEY:0:20}..."

if [ -z "$SUPABASE_SECRET_API_KEY" ]; then
    echo ""
    echo "⚠️  WARNING: SUPABASE_SECRET_API_KEY not set"
    echo "   Required for Metrics API access"
    echo "   Get it from: https://supabase.com/dashboard/project/${SUPABASE_PROJECT_REF}/settings/api"
else
    echo "  SUPABASE_SECRET_API_KEY: ${SUPABASE_SECRET_API_KEY:0:15}..."
fi

if [ -z "$SUPABASE_DATABASE_URL" ]; then
    echo ""
    echo "⚠️  WARNING: SUPABASE_DATABASE_URL not set"
    echo "   Required for direct database connection"
    echo "   Get password from: https://supabase.com/dashboard/project/${SUPABASE_PROJECT_REF}/settings/database"
fi

echo ""
echo "To test Metrics API, run:"
echo "  curl -H 'Authorization: Bearer \$SUPABASE_SECRET_API_KEY' \\"
echo "       -H 'apikey: \$SUPABASE_SECRET_API_KEY' \\"
echo "       'https://\${SUPABASE_PROJECT_REF}.supabase.co/customer/v1/privileged/metrics'"
