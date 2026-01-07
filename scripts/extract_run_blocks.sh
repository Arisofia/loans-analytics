#!/usr/bin/env bash
set -euo pipefail

OUT_DIR=${1:-.github/workflows/extracted_runs}
KEEP=${2:-20}          # number of recent extracted files to keep
MAX_AGE_DAYS=${3:-7}   # delete files older than this number of days

mkdir -p "$OUT_DIR"
# Clean existing extracted files for idempotency
rm -f "$OUT_DIR"/*.sh || true

shopt -s nullglob
for f in .github/workflows/*.{yml,yaml}; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  # Use awk to find multiline 'run: |' blocks and capture following indented lines
  awk -v outdir="$OUT_DIR" -v base="$base" '
    # Match multiline "run: |" lines (possibly starting with a dash)
    /^[[:space:]]*(-[[:space:]]*)?run:[[:space:]]*\|/ {
      # If we were already inside a block, close it
      if (inside) {
        close(file);
      }
      inside = 1;
      indent = 0;
      c++;
      file = outdir "/" base ".run." c ".sh";
      # Prepend a bash shebang so ShellCheck knows the target shell
      print "#!/usr/bin/env bash" > file;
      next;
    }
    inside {
      # If the line is purely whitespace, just append a newline
      if ($0 ~ /^[[:space:]]*$/) {
        print "" >> file;
        next;
      }

      # Calculate current line indentation
      match($0, /^[[:space:]]*/);
      current_indent = RLENGTH;

      # The first non-empty line after "run: |" determines the block indentation
      if (indent == 0) {
        indent = current_indent;
      }

      # If this line is less indented than the block started, the block has ended
      if (current_indent < indent) {
        if ($0 ~ /^[[:space:]]*[^[:space:]]+[[:space:]]*:/ || $0 ~ /^[[:space:]]*-\s*[^:]+:\s*/) {
          inside = 0;
          close(file);
          next;
        }
      }

      # Strip leading indentation based on the first line of the block
      content = substr($0, indent + 1);
      # Remove GitHub expressions like ${{ ... }} to avoid invalid Bash after extraction
      gsub(/\$\{\{[^}]+\}\}/, "", content);
      print content >> file;
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
  find "$OUT_DIR" -type f -mtime +"${MAX_AGE_DAYS}" -print -delete || true

  # Enforce KEEP limit (delete oldest files beyond KEEP)
  # Use mapfile if available for robust splitting, otherwise fallback to POSIX-compatible array
  if command -v mapfile >/dev/null 2>&1; then
    mapfile -t files < <(ls -1tr "$OUT_DIR"/*.sh 2>/dev/null || true)
  else
    files=( $(ls -1tr "$OUT_DIR"/*.sh 2>/dev/null || true) )
  fi
  total=${#files[@]}
  if [ "$total" -gt "$KEEP" ]; then
    to_delete_count=$((total - KEEP))
    echo "More than ${KEEP} files found (${total}). Deleting ${to_delete_count} oldest files..."
    ls -1tr "$OUT_DIR"/*.sh | head -n "${to_delete_count}" | xargs -r rm -f || true
  fi
fi

# Summarize
if command -v mapfile >/dev/null 2>&1; then
  mapfile -t remaining_files < <(ls -1 "$OUT_DIR"/*.sh 2>/dev/null || true)
  remaining_count=${#remaining_files[@]}
else
  remaining_files=( $(ls -1 "$OUT_DIR"/*.sh 2>/dev/null || true) )
  remaining_count=${#remaining_files[@]}
fi

echo "Extraction complete. Remaining extracted run scripts: ${remaining_count}"
