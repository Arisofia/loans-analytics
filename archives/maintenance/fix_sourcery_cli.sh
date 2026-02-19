#!/usr/bin/env bash
set -euo pipefail

# fix_sourcery_cli.sh
# - Stops any running Sourcery processes
# - Removes local Sourcery binaries
# - Reinstalls the VSCode extension (force)
# - Waits for the binary to appear and verifies --version
# - Collects diagnostic logs under ~/tmp/sourcery_fix_logs_<ts>

EXT_DIR="${HOME}/.vscode/extensions/sourcery.sourcery-1.43.0-darwin-arm64"
BIN="$EXT_DIR/sourcery_binaries/install/mac/sourcery"
LOGDIR="${HOME}/tmp/sourcery_fix_logs_$(date +%s)"
mkdir -p "$LOGDIR"
echo "[fix_sourcery] Logs will be saved to: $LOGDIR"

echo "[fix_sourcery] Stopping any running sourcery processes (if present)..."
pkill -f sourcery 2>/dev/null || true
sleep 1

echo "[fix_sourcery] Removing installed binary directory (if present)..."
rm -rf "$EXT_DIR/sourcery_binaries/install" || true

if command -v code >/dev/null 2>&1; then
	echo "[fix_sourcery] Uninstalling sourcery extension (if present)..."
	code --uninstall-extension sourcery.sourcery 2>&1 | tee "$LOGDIR/uninstall.log" || true

	echo "[fix_sourcery] Installing/forcing sourcery extension..."
	code --install-extension sourcery.sourcery --force 2>&1 | tee "$LOGDIR/install.log" || true
else
	echo "[fix_sourcery][ERROR] 'code' CLI not found in PATH. Install it from VSCode: Command Palette → 'Shell Command: Install 'code' command in PATH'." | tee "$LOGDIR/error.log"
	exit 1
fi

# Wait for binary to appear
echo "[fix_sourcery] Waiting up to 60s for binary to be installed..."
for i in $(seq 1 12); do
	if [ -x "$BIN" ]; then
		echo "[fix_sourcery] Binary found: $BIN"
		break
	fi
	sleep 5
done

if [ ! -x "$BIN" ]; then
	echo "[fix_sourcery][ERROR] Binary not found or not executable at: $BIN" | tee -a "$LOGDIR/install.log"
	echo "Listing extension dir for inspection:" | tee -a "$LOGDIR/install.log"
	ls -la "$EXT_DIR" 2>&1 | tee -a "$LOGDIR/install.log" || true

	echo "Recursive listing of sourcery_binaries:" | tee -a "$LOGDIR/install.log"
	find "$EXT_DIR/sourcery_binaries" -maxdepth 4 -type f -ls 2>&1 | tee -a "$LOGDIR/install.log" || true

	echo "Check for extension storage and install logs (globalStorage):" | tee -a "$LOGDIR/install.log"
	find "$HOME/Library/Application Support/Code/User/globalStorage" -iname '*sourcery*' -ls 2>&1 | tee -a "$LOGDIR/install.log" || true

	echo "Searching VSCode extension host logs for 'sourcery' (may take a moment)..." | tee -a "$LOGDIR/install.log"
	VSLOGS="$HOME/Library/Application Support/Code/logs"
	if [ -d "$VSLOGS" ]; then
		grep -iR "sourcery" "$VSLOGS" 2>/dev/null | tee -a "$LOGDIR/install.log" || true
		echo "Latest exthost log files (most recent):" | tee -a "$LOGDIR/install.log"
		ls -lt "$VSLOGS"/*/exthost/*.log 2>/dev/null | head -n 20 | tee -a "$LOGDIR/install.log" || true
	else
		echo "VSCode logs directory not found at expected location: $VSLOGS" | tee -a "$LOGDIR/install.log"
	fi

	echo "Network proxy environment variables (HTTP(S)_PROXY, NO_PROXY):" | tee -a "$LOGDIR/install.log"
	env | egrep -i 'proxy' 2>&1 | tee -a "$LOGDIR/install.log" || true

	echo "If you want to attempt manual install, set MANUAL_BINARY_URL and re-run the script:" | tee -a "$LOGDIR/install.log"
	echo "  MANUAL_BINARY_URL=https://.../sourcery-darwin-arm64 && ./scripts/fix_sourcery_cli.sh" | tee -a "$LOGDIR/install.log"

	# If env var set, try downloading the binary directly (use with caution)
	if [ -n "${MANUAL_BINARY_URL-}" ]; then
		echo "[fix_sourcery] MANUAL_BINARY_URL provided, attempting download..." | tee -a "$LOGDIR/install.log"
		mkdir -p "$(dirname "$BIN")"
		curl -fL "$MANUAL_BINARY_URL" -o "$BIN" 2>&1 | tee -a "$LOGDIR/install.log" || echo "[fix_sourcery][WARN] curl download failed" | tee -a "$LOGDIR/install.log"
		chmod +x "$BIN" || true
		if [ -x "$BIN" ]; then
			echo "[fix_sourcery] Manual binary downloaded and executable, attempting --version" | tee -a "$LOGDIR/install.log"
			"$BIN" --version 2>&1 | tee -a "$LOGDIR/install.log" || true
			echo "[fix_sourcery] Manual install completed; please reload VSCode." | tee -a "$LOGDIR/install.log"
			exit 0
		else
			echo "[fix_sourcery][ERROR] Manual download did not produce executable at $BIN" | tee -a "$LOGDIR/install.log"
		fi
	fi

	echo "Check Output -> Sourcery and Developer Tools console in VSCode for extension errors." | tee -a "$LOGDIR/install.log"
	exit 2
fi

echo "[fix_sourcery] Ensuring executable permissions..."
chmod +x "$BIN" || true

echo "[fix_sourcery] Capturing file type and version info..."
file "$BIN" 2>&1 | tee "$LOGDIR/file_info.log"
"$BIN" --version 2>&1 | tee "$LOGDIR/version.log" || true

echo "[fix_sourcery] Capturing some strings from the binary for diagnostics (first 200 lines)..."
strings "$BIN" | head -n 200 >"$LOGDIR/strings_head.log" || true

echo "[fix_sourcery] Completed. Review logs in: $LOGDIR"
echo "[fix_sourcery] Next steps: restart VSCode and check Output -> Sourcery and DevTools console. If it still fails, attach the logs from $LOGDIR when asking for help."

exit 0
