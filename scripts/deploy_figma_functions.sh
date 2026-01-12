#!/bin/bash
# Deploy Supabase Edge Functions for Figma Sync
# This script deploys the functions with --no-verify-jwt to allow public access

PROJECT_REF="tugujujhcjyggmshtgoa"

echo "🚀 Deploying Figma Sync Edge Functions to Supabase..."

# Deploy figma-kpis
echo "📦 Deploying figma-kpis..."
supabase functions deploy figma-kpis --project-ref $PROJECT_REF --no-verify-jwt

# Deploy figma-marketing
echo "📦 Deploying figma-marketing..."
supabase functions deploy figma-marketing --project-ref $PROJECT_REF --no-verify-jwt

echo "✅ Deployment complete!"
echo "KPI Feed: https://$PROJECT_REF.functions.supabase.co/figma-kpis"
echo "Marketing Feed: https://$PROJECT_REF.functions.supabase.co/figma-marketing"
echo ""
echo "💡 Note: These endpoints are now configured as public feeds with CORS enabled."
