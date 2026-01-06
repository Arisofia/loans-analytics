#!/usr/bin/env bash
set -euo pipefail

OUT_DIR=${1:-.github/workflows/extracted_runs}
KEEP=${2:-20}          # number of recent extracted files to keep
MAX_AGE_DAYS=${3:-7}   # delete files older than this number of days

mkdir -p "$OUT_DIR"
# Clean existing extracted files for idempotency
rm -f "$OUT_DIR"/*.sh || true

shopt -s nullglob
count=0
for f in .github/workflows/*.{yml,yaml}; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  # Use awk to find 'run:' lines and capture following indented lines
  awk -v outdir="$OUT_DIR" -v base="$base" '
    /^\	*run:\s*(\||$)/ { inside=1; c++; file = outdir "/" base ".run." c ".sh"; next }
    inside {
      # If line is empty, keep it
      if ($0 ~ /^[[:space:]]*$/) { print "" >> file; next }
      # If line starts with non-space and looks like a YAML key (a: or key:), then end block
      if ($0 ~ /^[^[:space:]]+[[:space:]]*:[^:]/) { inside=0; close(file); next }
      # Strip leading indentation up to the content
      sub(/^[ \t]*/, "", $0)
      print $0 >> file
    }
    END { if (inside) close(file) }
  ' "$f"
done

# Make files executable if any
if compgen -G "$OUT_DIR/*.sh" > /dev/null; then
  chmod +x "$OUT_DIR"/*.sh || true
fi

echo "Extracted run blocks to $OUT_DIR"

# Prune older extracted files to avoid buildup
#  - Remove files older than MAX_AGE_DAYS
#  - Ensure we keep at most KEEP most recent files
if compgen -G "$OUT_DIR/*.sh" > /dev/null; then
  echo "Pruning extracted files older than ${MAX_AGE_DAYS} days..."
  find "$OUT_DIR" -type f -mtime +${MAX_AGE_DAYS} -print -delete || true

  # Enforce KEEP limit (delete oldest files beyond KEEP)
  files=( $(ls -1tr "$OUT_DIR"/*.sh 2>/dev/null || true) )
  total=${#files[@]}
  if [ "$total" -gt "$KEEP" ]; then
    to_delete_count=$((total - KEEP))
    echo "More than ${KEEP} files found (${total}). Deleting ${to_delete_count} oldest files..."
    ls -1tr "$OUT_DIR"/*.sh | head -n "${to_delete_count}" | xargs -r rm -f || true
  fi
fi

# Summarize
remaining_count=$(ls -1 "$OUT_DIR"/*.sh 2>/dev/null | wc -l || true)
echo "Extraction complete. Remaining extracted run scripts: ${remaining_count}"