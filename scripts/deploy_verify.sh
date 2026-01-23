#!/usr/bin/env bash
# Robust deploy-verify helper script
# Usage: ./scripts/deploy_verify.sh --branch BRANCH --target-url URL

set -u
SCRIPT_NAME=$(basename "$0")
LOG_DIR="./tmp/deploy-verify-logs/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$LOG_DIR"
REPORT="$LOG_DIR/report.txt"

log() { printf "%s %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$REPORT"; }
err() { printf "%s ERROR: %s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$REPORT" >&2; }

RETRIES() { local n=$1; shift; local i=0; local rc=0; while :; do ((i++)); "$@"; rc=$?; if [ $rc -eq 0 ]; then return 0; fi; if [ $i -ge $n ]; then return $rc; fi; sleep $((2**i)); done }

# Default parameters
BRANCH="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'HEAD')"
TARGET_URL=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --branch) BRANCH=$2; shift 2;;
    --target-url) TARGET_URL=$2; shift 2;;
    --help) echo "Usage: $SCRIPT_NAME [--branch BRANCH] [--target-url URL]"; exit 0;;
    *) err "Unknown arg: $1"; shift;;
  esac
done

log "Starting deploy-verify run on branch: $BRANCH"
log "Log dir: $LOG_DIR"

# Tool checks
for cmd in git gh curl jq; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    err "Required command not found: $cmd"; # don't abort; record and continue
  fi
done

# Confirm HEAD commit
HEAD_SHA=$(git rev-parse --short "$BRANCH" 2>/dev/null || git rev-parse --short HEAD)
log "HEAD SHA: $HEAD_SHA"

auth_ok=0
if gh auth status >/dev/null 2>&1; then
  auth_ok=1
  log "gh authenticated"
else
  err "gh not authenticated. Some workflow actions will fail."
fi

# Check repository secret
secret_present=0
if [ $auth_ok -eq 1 ]; then
  if gh secret list | grep -q '^MIDDLEWARE_SHARED_SECRET$'; then
    secret_present=1
    log "Repository secret MIDDLEWARE_SHARED_SECRET found"
  else
    err "Repository secret MIDDLEWARE_SHARED_SECRET NOT found"
  fi
else
  err "Skipping secret check due to unauthenticated gh"
fi

# Trigger Secret-check workflow (if available)
secret_check_run_url=""
if [ $auth_ok -eq 1 ]; then
  log "Dispatching secret-check workflow"
  gh workflow run secret-check.yml --ref "$BRANCH" || err "Failed to dispatch secret-check.yml"
  # Poll for recent run
  REQ_ATTEMPTS=6
  i=0
  while [ $i -lt $REQ_ATTEMPTS ]; do
    i=$((i+1))
    run=$(gh run list --workflow secret-check.yml --branch "$BRANCH" --limit 1 --json database --jq '.[0].html_url' 2>/dev/null || true)
    if [ -n "$run" ]; then
      secret_check_run_url=$run
      log "Found secret-check run: $run"
      break
    fi
    sleep 3
  done
  if [ -z "$secret_check_run_url" ]; then
    err "Could not find dispatched secret-check run"
  fi
else
  err "Skipping secret-check dispatch because gh unauthenticated"
fi

# Deploy-verify workflow dispatch
deploy_verify_run_url=""
if [ -n "$TARGET_URL" -a $auth_ok -eq 1 ]; then
  log "Dispatching deploy-verify workflow with target_url=$TARGET_URL"
  gh workflow run deploy-verify.yml --ref "$BRANCH" -f target_url="$TARGET_URL" || err "Failed to dispatch deploy-verify.yml"
  # Poll for run
  i=0
  while [ $i -lt 8 ]; do
    i=$((i+1))
    run=$(gh run list --workflow deploy-verify.yml --branch "$BRANCH" --limit 1 --json database --jq '.[0].html_url' 2>/dev/null || true)
    if [ -n "$run" ]; then
      deploy_verify_run_url=$run
      log "Found deploy-verify run: $run"
      break
    fi
    sleep 4
  done
  if [ -z "$deploy_verify_run_url" ]; then
    err "Could not find dispatched deploy-verify run"
  fi
else
  log "Skipping deploy-verify dispatch (no target_url or gh unauthenticated)"
fi

# Endpoint checks (best effort)
if [ -n "$TARGET_URL" ]; then
  log "Performing endpoint checks against $TARGET_URL"
  # Without secret
  status_no_secret=$(curl -s -o /dev/null -w "%{http_code}" "$TARGET_URL" || echo "000")
  log "No-secret HTTP status: $status_no_secret"
  # With secret if available in env
  if [ -n "${MIDDLEWARE_SHARED_SECRET:-}" ]; then
    status_with_secret=$(curl -s -o /dev/null -w "%{http_code}" -H "X-Middleware-Secret: ${MIDDLEWARE_SHARED_SECRET}" "$TARGET_URL" || echo "000")
    log "With-secret HTTP status: $status_with_secret"
  else
    err "MIDDLEWARE_SHARED_SECRET not in env: skipping with-secret check"
  fi
else
  log "No target_url provided; skipping endpoint tests"
fi

# Summary
cat <<EOF | tee -a "$REPORT"
SUMMARY
HEAD: $HEAD_SHA
secret_present: $secret_present
secret_check_run_url: $secret_check_run_url
deploy_verify_run_url: $deploy_verify_run_url
EOF

log "Deploy-verify script finished. Report: $REPORT"
exit 0
