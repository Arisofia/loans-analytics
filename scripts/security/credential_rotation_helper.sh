#!/bin/bash
set -euo pipefail

echo "=========================================="
echo "CREDENTIAL ROTATION HELPER"
echo "=========================================="
echo ""
echo "⚠️  CRITICAL: Credentials found in git history must be rotated"
echo ""
echo "1. AZURE_CLIENT_SECRET - Regenerate in Azure Portal"
echo "2. OPENAI_API_KEY - Create new key at platform.openai.com"
echo "3. ANTHROPIC_API_KEY - Create new key at console.anthropic.com"
echo "4. HUBSPOT_API_KEY - Create new private app"
echo ""
echo "After rotating, create GitHub Secrets and run git history cleanup."
