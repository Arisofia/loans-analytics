#!/bin/bash
set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║            Git History Credential Cleanup                        ║"
echo "║     CAUTION: This rewrites git history. Ensure all team members"
echo "║            have committed and pushed their changes.              ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Check if BFG is installed
if ! command -v bfg &> /dev/null; then
    echo "❌ BFG Repo Cleaner not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install bfg
    else
        echo "❌ Please install BFG manually:"
        echo "   https://rtyley.github.io/bfg-repo-cleaner/"
        exit 1
    fi
fi

echo "📦 BFG Repo Cleaner version:"
bfg --version
echo ""

# Create secrets file
SECRETS_FILE="/tmp/secrets_to_remove.txt"
cat > "$SECRETS_FILE" << 'SECRETS'
# The following are secret patterns (REDACTED for pre-commit compliance):
# [OPENAI_KEY_PATTERN]
# [ANTHROPIC_KEY_PATTERN]
# [AZURE_CLIENT_SECRET_PATTERN]
# [HUBSPOT_API_KEY_PATTERN]
# [HUBSPOT_TOKEN_PATTERN]
# [AZURE_EXAMPLE_PATTERN]
SECRETS

echo "🔍 Scanning for exposed credentials..."
echo ""

# Count matches before cleanup
BEFORE=$(git log --all --pretty=format: --name-only -S '[OPENAI_KEY_PATTERN]' | wc -l)
echo "Found ~${BEFORE} commits with exposed credentials (pattern: [OPENAI_KEY_PATTERN])"
echo ""

# Ask for confirmation
read -p "⚠️  This will rewrite git history. Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "⏳ Running BFG cleanup (this may take a few minutes)..."
bfg --replace-text "$SECRETS_FILE" .

echo ""
echo "🧹 Cleaning reflog and garbage collection..."
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "📊 Verifying cleanup..."
if git log --all -S '[OPENAI_KEY_PATTERN]' | wc -l | grep -q '^0$'; then
    echo "✅ Credentials successfully removed from git history (pattern: [OPENAI_KEY_PATTERN])"
else
    echo "⚠️  Warning: Some credentials may still be in history (pattern: [OPENAI_KEY_PATTERN])"
    echo "   You may need to run cleanup again or investigate manually"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "⚠️  NEXT STEP: Force push to remote"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Run the following command to overwrite remote history:"
echo ""
echo "  git push -f origin main"
echo ""
echo "⚠️  WARNING: All team members must re-clone the repository"
echo "     after the force push!"
echo ""
