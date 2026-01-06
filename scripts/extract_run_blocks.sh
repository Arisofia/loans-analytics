#!/usr/bin/env bash
set -euo pipefail

OUT_DIR=${1:-.github/workflows/extracted_runs}
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
