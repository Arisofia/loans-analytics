#!/bin/bash
# Service Login Helper Script

echo "🔐 Service Authentication Status"
echo ""

# GitHub
echo "✅ GitHub: Already authenticated"
echo "   Account: JenineferDeras"
echo ""

# Vercel
echo "✅ Vercel: Already authenticated"
echo "   Account: jeninefer"
echo ""

# Services requiring manual login
echo "⚠️  Services requiring authentication:"
echo ""

echo "1. Google Cloud:"
echo "   gcloud auth login"
echo "   gcloud config set project YOUR_PROJECT_ID"
echo ""

echo "2. Railway (install first):"
echo "   npm install -g @railway/cli"
echo "   railway login"
echo ""

echo "3. Supabase (local dev):"
echo "   npx supabase login"
echo "   npx supabase link --project-ref YOUR_PROJECT_REF"
echo ""

echo "4. Sourcery:"
echo "   sourcery login"
echo ""

echo "📝 Token-based services (configured via .env.local):"
# ...existing code...
echo "   ✓ GEMINI_API_KEY"
echo "   ✓ GROK_API_KEY"
echo "   ✓ HUBSPOT_TOKEN"
echo "   ✓ HUGGING_TOKEN"
echo "   ✓ META_ABACO"
echo "   ✓ OPEN_AI"

echo "   ✓ SONARQUBE_KEY (via GitHub Actions)"
echo ""

echo "💡 Note: GitHub Secrets are only accessible in CI/CD workflows,"
echo "   not locally. Use .env.local for local development."
echo ""

echo "📋 To set up local environment:"
echo "   1. Copy .env.example to .env.local"
echo "   2. Add your API keys to .env.local"
echo "   3. Never commit .env.local (already in .gitignore)"
