#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HAS_APP=0
HAS_SRC_APP=0

[[ -d "$ROOT/app" ]] && HAS_APP=1
[[ -d "$ROOT/src/app" ]] && HAS_SRC_APP=1

if [[ "$HAS_APP" -eq 1 && "$HAS_SRC_APP" -eq 1 ]]; then
  echo "ERROR: Both apps/web/app and apps/web/src/app exist. Choose exactly one."
  exit 1
fi

if [[ "$HAS_APP" -eq 0 && "$HAS_SRC_APP" -eq 0 ]]; then
  echo "ERROR: Neither apps/web/app nor apps/web/src/app exists. App Router missing."
  exit 1
fi

echo "OK: Single App Router root detected."
