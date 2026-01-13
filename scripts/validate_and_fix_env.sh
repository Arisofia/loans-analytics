#!/bin/zsh
# Automated validation and fix script for repo, extensions, and permissions

# 0. Get repository root (relative to script location)
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
REPO_PATH=$(cd "$SCRIPT_DIR/.." && pwd)

echo "════════════════════════════════════════════════════════════════"
echo "  ABACO ANALYTICS - ENVIRONMENT VALIDATION & FIX"
echo "  Repo Root: $REPO_PATH"
echo "════════════════════════════════════════════════════════════════"

# 1. Validate repo path
if [ -d "$REPO_PATH" ]; then
  echo "✅ Repo directory exists: $REPO_PATH"
else
  echo "❌ ERROR: Repo directory missing: $REPO_PATH"
  exit 1
fi

# 2. Validate .git directory
if [ -d "$REPO_PATH/.git" ]; then
  echo "✅ .git directory exists."
else
  echo "⚠️  WARNING: .git missing. Initializing git..."
  cd "$REPO_PATH" && git init
fi

# 3. Detect Extension path (generic)
EXT_PATH_BASE="$HOME/.vscode/extensions"
# Look for windows-ai-studio extension (any version)
EXT_PATH=$(find "$EXT_PATH_BASE" -maxdepth 1 -name "ms-windows-ai-studio.windows-ai-studio-*" 2>/dev/null | head -n 1)
AGENT_FILE="AIAgentExpert.agent.md"

if [ -n "$EXT_PATH" ]; then
  RESOURCES_PATH="$EXT_PATH/resources/lmt/chatAgents"
  if [ -f "$RESOURCES_PATH/$AGENT_FILE" ]; then
    echo "✅ $AGENT_FILE exists in extension path: $RESOURCES_PATH"
  else
    echo "⚠️  WARNING: $AGENT_FILE missing in $RESOURCES_PATH. Consider reinstalling extension."
  fi
else
  echo "ℹ️  Extension path (windows-ai-studio) not detected. Skipping extension audit."
fi

# 4. Check permissions (no sudo unless necessary)
if [ ! -w "$REPO_PATH" ]; then
    echo "⚠️  Repo directory is not writable. Attempting to fix..."
    sudo chown -R $(whoami) "$REPO_PATH"
    echo "✅ Permissions fixed for repo."
else
    echo "✅ Permissions are correct (writable)."
fi

# 5. Validate workspace open in VS Code
if pgrep -x "Code" > /dev/null; then
  echo "ℹ️  VS Code is running. Please ensure $REPO_PATH is open as a folder."
else
  echo "ℹ️  VS Code is not running."
fi

# 6. Check for uncommitted changes
echo ""
git -C "$REPO_PATH" status --porcelain | grep . && echo "⚠️  Warning: Uncommitted changes detected!" || echo "✅ No uncommitted changes."

# 7. Audit documentation files
echo ""
echo "🔍 Auditing documentation..."
DOCS=(
    "docs/KPI-Operating-Model.md"
    "docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md"
    "COMPLIANCE_VALIDATION_SUMMARY.md"
    "SECURITY.md"
)

for doc_rel in "${DOCS[@]}"; do
  doc="$REPO_PATH/$doc_rel"
  if [ -f "$doc" ]; then
    echo "✅ $doc_rel found. Summary:"
    head -3 "$doc" | sed 's/^/  /'
  else
    echo "❌ $doc_rel missing!"
  fi
done

# 8. Audit environment variables
echo ""
if [ -f "$REPO_PATH/.env.local" ]; then
  echo "✅ .env.local exists. (Contents masked for security)"
elif [ -f "$REPO_PATH/.env" ]; then
  echo "✅ .env exists. (Contents masked for security)"
else
  echo "⚠️  .env and .env.local missing! Consider creating one from .env.example"
fi

# 9. KPI & dashboard keyword audit
echo ""
echo "📊 KPI & Dashboard Audit..."
for doc_rel in "docs/KPI-Operating-Model.md" "docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md"; do
  doc="$REPO_PATH/$doc_rel"
  if [ -f "$doc" ]; then
    MATCH_COUNT=$(grep -iE 'KPI|dashboard|metric|trace|visual' "$doc" | wc -l)
    if [ "$MATCH_COUNT" -gt 0 ]; then
        echo "✅ Found $MATCH_COUNT KPI/dashboard keywords in $doc_rel"
    else
        echo "⚠️  No KPI/dashboard keywords found in $doc_rel"
    fi
  fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ Extended validation and automation complete."
echo "════════════════════════════════════════════════════════════════"
