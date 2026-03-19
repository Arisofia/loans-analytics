#!/usr/bin/env bash
set -euo pipefail

if command -v git >/dev/null 2>&1; then
  GIT_BIN="$(command -v git)"
elif [ -n "${LOCALAPPDATA:-}" ] && [ -x "${LOCALAPPDATA}/Programs/Git/cmd/git.exe" ]; then
  GIT_BIN="${LOCALAPPDATA}/Programs/Git/cmd/git.exe"
else
  echo "ERROR: git executable not found."
  exit 1
fi

if [ -n "${PYTHON_BIN:-}" ] && [ -x "${PYTHON_BIN}" ]; then
  PYTHON_BIN="${PYTHON_BIN}"
elif [ -n "${LOCALAPPDATA:-}" ] && [ -x "${LOCALAPPDATA}/Programs/Python/Python312/python.exe" ]; then
  PYTHON_BIN="${LOCALAPPDATA}/Programs/Python/Python312/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python executable not found."
  exit 1
fi

REPO_ROOT="$($GIT_BIN rev-parse --show-toplevel)"
cd "$REPO_ROOT"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

log_del()  { echo -e "${RED}  x DELETE${RESET}  $1"; }
log_ok()   { echo -e "${GREEN}  ok${RESET}  $1"; }
log_warn() { echo -e "${YELLOW}  !${RESET}  $1"; }

echo -e "${BOLD}${CYAN}"
echo "=============================================================="
echo " PHASE 1 - PRODUCTION PURGE"
echo " Doctrine: delete unless proven necessary"
$DRY_RUN && echo " MODE: DRY RUN (no files will be changed)"
echo "=============================================================="
echo -e "${RESET}"

if [ ! -f "reports/PRODUCTION_INVENTORY.json" ]; then
  echo "ERROR: reports/PRODUCTION_INVENTORY.json not found."
  echo "Run phase0 first: python3 scripts/hardening/phase0_declare_canonical.py"
  exit 1
fi

DELETE_FILES="$($PYTHON_BIN - <<'PY'
import json
from pathlib import Path

data = json.loads(Path("reports/PRODUCTION_INVENTORY.json").read_text(encoding="utf-8"))
for item in data["inventory"]:
    if item["status"] == "DELETE_NOW":
        print(item["path"])
PY
)"

TOTAL=$(printf '%s\n' "$DELETE_FILES" | grep -c . || true)
echo "Files classified DELETE_NOW: $TOTAL"
echo ""

if ! $DRY_RUN && [ "$TOTAL" -gt 0 ]; then
  echo -e "${RED}${BOLD}This will permanently delete $TOTAL files from the working tree and git index.${RESET}"
  read -rp "Type DELETE to proceed: " CONFIRM
  [[ "$CONFIRM" == "DELETE" ]] || { echo "Aborted."; exit 0; }
fi

echo ""
echo "==== PURGING ===="
DELETED=0
SKIPPED=0

while IFS= read -r filepath; do
  [ -z "$filepath" ] && continue

  if $DRY_RUN; then
    log_del "$filepath (DRY RUN)"
    DELETED=$((DELETED + 1))
    continue
  fi

  if "$GIT_BIN" ls-files --error-unmatch "$filepath" >/dev/null 2>&1; then
    if "$GIT_BIN" rm -f --quiet "$filepath" >/dev/null 2>&1; then
      log_del "$filepath"
      DELETED=$((DELETED + 1))
    elif [ -e "$filepath" ]; then
      rm -rf "$filepath"
      log_del "$filepath (disk delete fallback)"
      DELETED=$((DELETED + 1))
    else
      log_warn "Not found: $filepath"
      SKIPPED=$((SKIPPED + 1))
    fi
  elif [ -e "$filepath" ]; then
    rm -rf "$filepath"
    log_del "$filepath (untracked)"
    DELETED=$((DELETED + 1))
  else
    log_warn "Not found: $filepath"
    SKIPPED=$((SKIPPED + 1))
  fi
done <<< "$DELETE_FILES"

echo ""
echo "==== PURGE CACHES ===="

if ! $DRY_RUN; then
  find . -type d -name __pycache__ -not -path './.git/*' -exec rm -rf {} + 2>/dev/null || true
  log_ok "All __pycache__ directories removed"

  for CACHE in .pytest_cache .mypy_cache .ruff_cache .hypothesis htmlcov; do
    if [ -d "$CACHE" ]; then
      "$GIT_BIN" rm -r --cached --ignore-unmatch "$CACHE/" >/dev/null 2>&1 || true
      rm -rf "$CACHE"
      log_ok "$CACHE removed"
    fi
  done

  for dir in \
    "backend/python/ingest" "tests" "infra" "tools" "db/sql" \
    "frontend/data/agent_outputs" ".zencoder" ".zenflow" \
    "backend/python/testing" "backend/src/agents/multi_agent"; do
    if [ -d "$dir" ] && [ -z "$(find "$dir" -mindepth 1 2>/dev/null)" ]; then
      "$GIT_BIN" rm -rf "$dir" >/dev/null 2>&1 || rm -rf "$dir"
      log_ok "Empty dir removed: $dir"
    fi
  done

  if [ -d "data/abaco" ]; then
    DATA_FILES=(collateral.csv customer_data.csv loan_data.csv payment_schedule.csv real_payment.csv)
    IDENTICAL=true
    for f in "${DATA_FILES[@]}"; do
      A="data/abaco/$f"; B="data/raw/$f"
      if [ -f "$A" ] && [ -f "$B" ] && ! cmp -s "$A" "$B"; then
        log_warn "data/abaco/$f differs from data/raw/$f - NOT auto-deleting data/abaco"
        IDENTICAL=false
        break
      fi
    done
    if $IDENTICAL && [ -z "$(find data/abaco -type f 2>/dev/null)" ]; then
      "$GIT_BIN" rm -rf data/abaco/ >/dev/null 2>&1 || rm -rf data/abaco/
      log_ok "data/abaco/ removed (no remaining files)"
    fi
  fi

  "$GIT_BIN" add -A
fi

echo ""
echo "==== SUMMARY ===="
echo "  Deleted:  $DELETED"
echo "  Skipped:  $SKIPPED"

if ! $DRY_RUN; then
  echo ""
  "$GIT_BIN" status --short | head -30 || true
fi