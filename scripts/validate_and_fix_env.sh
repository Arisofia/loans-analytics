#!/bin/zsh
# Automated validation and fix script for repo, extensions, and permissions

REPO_PATH="$(pwd)"
EXT_PATH="$HOME/.vscode/extensions/ms-windows-ai-studio.windows-ai-studio-0.26.4-darwin-arm64/resources/lmt/chatAgents"
AGENT_FILE="AIAgentExpert.agent.md"

# 1. Validate repo path
if [ -d "$REPO_PATH" ]; then
  echo "Repo directory exists: $REPO_PATH"
else
  echo "ERROR: Repo directory missing: $REPO_PATH"
fi

# 2. Validate .git directory
if [ -d "$REPO_PATH/.git" ]; then
  echo ".git directory exists."
else
  echo "WARNING: .git missing. Initializing git..."
  cd "$REPO_PATH" && git init
fi

# 3. Validate extension file
if [ -d "$EXT_PATH" ]; then
  if [ -f "$EXT_PATH/$AGENT_FILE" ]; then
    echo "$AGENT_FILE exists in extension path."
  else
    echo "WARNING: $AGENT_FILE missing in extension path. Consider reinstalling extension."
  fi
else
  echo "WARNING: Extension path missing: $EXT_PATH"
fi

# 4. Fix permissions
sudo chown -R $(whoami) "$REPO_PATH"
echo "Permissions fixed for repo."

# 5. Validate workspace open in VS Code
if pgrep -x "Code" > /dev/null; then
  echo "VS Code is running. Please ensure $REPO_PATH is open as a folder."
else
  echo "VS Code is not running."
fi

# 6. Final status
# 6. Check for uncommitted changes
git -C "$REPO_PATH" status --porcelain | grep . && echo "Warning: Uncommitted changes detected!" || echo "No uncommitted changes."

# 7. Audit documentation files
for doc in "$REPO_PATH/docs/KPI-Operating-Model.md" "$REPO_PATH/docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md" "$REPO_PATH/COMPLIANCE_VALIDATION_SUMMARY.md" "$REPO_PATH/SECURITY.md"; do
  if [ -f "$doc" ]; then
    echo "$doc found. Summary:"
    head -10 "$doc"
  else
    echo "$doc missing!"
  fi
done

# 8. Audit environment variables
if [ -f "$REPO_PATH/.env.local" ]; then
  echo "\n.env.local contents:"
  head -20 "$REPO_PATH/.env.local"
else
  echo ".env.local missing!"
fi

# 9. KPI & dashboard keyword audit
for kpi in "$REPO_PATH/docs/KPI-Operating-Model.md" "$REPO_PATH/docs/FINTECH_DASHBOARD_WEB_APP_GUIDE.md"; do
  if [ -f "$kpi" ]; then
    grep -iE 'KPI|dashboard|metric|trace|visual' "$kpi" || echo "No KPI/dashboard keywords found in $kpi"
  fi
done

# 10. Compliance & security keyword audit
if [ -f "$REPO_PATH/COMPLIANCE_VALIDATION_SUMMARY.md" ]; then
  grep -iE 'compliance|audit|trace|policy|regulation' "$REPO_PATH/COMPLIANCE_VALIDATION_SUMMARY.md" || echo "No compliance keywords found in COMPLIANCE_VALIDATION_SUMMARY.md"
fi
if [ -f "$REPO_PATH/SECURITY.md" ]; then
  grep -iE 'audit|compliance|trace|risk|policy' "$REPO_PATH/SECURITY.md" || echo "No audit/compliance keywords found in SECURITY.md"
fi

# 11. Final status
echo "\nExtended validation and automation complete. Review warnings and summaries above."
