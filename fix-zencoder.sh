#!/bin/zsh
# Automated Zencoder ENOENT Fix for VS Code (macOS)

EXT_ID="zencoderai.zencoder"

# 1. Uninstall Zencoder extension
echo "Uninstalling Zencoder extension..."
code --uninstall-extension $EXT_ID

# 2. Remove stale artifacts
echo "Removing old Zencoder extension folders..."
rm -rf ~/.vscode/extensions/${EXT_ID}-*

# 3. Restart VS Code (asks user to close all windows)
echo "Please fully quit VS Code (Cmd+Q) and press Enter to continue."
read

# 4. Reinstall Zencoder extension
echo "Reinstalling Zencoder extension..."
code --install-extension $EXT_ID

# 5. Ensure CLI is executable
find ~/.vscode/extensions/${EXT_ID}-*/out/ -name "zencoder-cli" -exec chmod +x {} \;

echo "Zencoder extension fix complete. Please reload your workspace."
