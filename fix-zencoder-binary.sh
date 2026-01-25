#!/bin/zsh
# Automated Zencoder extension binary check and fix

EXT_DIR=~/.vscode/extensions
BIN_NAME=zencoder-cli
EXT_PATTERN="zencoderai.zencoder-*"

# 1. Check for the binary
BIN_PATH=$(find $EXT_DIR/$EXT_PATTERN/out/ -name $BIN_NAME 2>/dev/null | head -n 1)

if [[ -z "$BIN_PATH" ]]; then
  echo "Zencoder CLI binary not found. Attempting to reinstall extension..."
  code --uninstall-extension zencoderai.zencoder
  rm -rf $EXT_DIR/$EXT_PATTERN
  code --install-extension zencoderai.zencoder
  BIN_PATH=$(find $EXT_DIR/$EXT_PATTERN/out/ -name $BIN_NAME 2>/dev/null | head -n 1)
  if [[ -z "$BIN_PATH" ]]; then
    echo "ERROR: Zencoder CLI binary still not found after reinstall. Please check your VS Code installation."
    exit 1
  fi
fi

# 2. Ensure the binary is executable
chmod +x "$BIN_PATH"
echo "Zencoder CLI binary found and set as executable: $BIN_PATH"
echo "Restart VS Code to complete the fix."
