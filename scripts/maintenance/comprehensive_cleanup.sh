#!/usr/bin/env bash
# ==============================================================================
# Comprehensive Repository Cleanup
#
# Purpose:
# - Remove caches, backups, duplicate copies, and temporary artifacts
# - Remove empty files/directories and orphan symlinks
# - Run post-cleanup quality checks
# ==============================================================================

set -euo pipefail

DRY_RUN=false
COMMIT_CHANGES=false
COMMIT_EACH_SECTION=false
CLEAN_WORKFLOW_RUNS=false
KEEP_COUNT="${KEEP_COUNT:-25}"
RUN_LIST_LIMIT="${RUN_LIST_LIMIT:-1000}"
LOG_FILE="cleanup.log"

usage() {
    cat <<'USAGE'
Usage: comprehensive_cleanup.sh [options]

Options:
  --dry-run              Preview actions without deleting/modifying files.
  --commit               Commit all changes at end (if any).
  --commit-each-section  Commit after each section (implies --commit).
  --cleanup-workflow-runs  Delete old GitHub Actions runs (keeps latest N).
  --keep <N>             Number of workflow runs to keep (default: 25).
  --log-file <path>      Override log file path (default: cleanup.log).
  --help                 Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --commit)
            COMMIT_CHANGES=true
            shift
            ;;
        --commit-each-section)
            COMMIT_CHANGES=true
            COMMIT_EACH_SECTION=true
            shift
            ;;
        --cleanup-workflow-runs)
            CLEAN_WORKFLOW_RUNS=true
            shift
            ;;
        --keep)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --keep"
                exit 1
            fi
            KEEP_COUNT="$2"
            shift 2
            ;;
        --log-file)
            if [[ $# -lt 2 ]]; then
                echo "Missing value for --log-file"
                exit 1
            fi
            LOG_FILE="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

: >"$LOG_FILE"

log() {
    echo "$@" | tee -a "$LOG_FILE"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

remove_path() {
    local path="$1"
    if [[ "$path" == "$LOG_FILE" || "$path" == "./$LOG_FILE" ]]; then
        log "[skip] not removing active log file: $path"
        return 0
    fi
    if [[ ! -e "$path" && ! -L "$path" ]]; then
        return 0
    fi
    if [[ "$DRY_RUN" == true ]]; then
        log "[dry-run] remove $path"
    else
        rm -rf -- "$path"
        log "[removed] $path"
    fi
}

remove_matching_files() {
    local root="$1"
    shift
    local -a patterns=("$@")
    [[ -d "$root" ]] || return 0

    local pattern file
    for pattern in "${patterns[@]}"; do
        while IFS= read -r -d '' file; do
            remove_path "$file"
        done < <(find "$root" \
            \( -path "*/.git/*" -o -path "*/.venv/*" -o -path "*/node_modules/*" \) -prune \
            -o -type f -iname "$pattern" -print0 2>/dev/null)
    done
}

commit_if_requested() {
    local msg="$1"
    if [[ "$DRY_RUN" == true || "$COMMIT_CHANGES" != true || "$COMMIT_EACH_SECTION" != true ]]; then
        return 0
    fi
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "$msg"
        log "[git] committed: $msg"
    fi
}

ensure_gitignore_entry() {
    local entry="$1"
    local gitignore=".gitignore"
    touch "$gitignore"
    if grep -Fxq "$entry" "$gitignore"; then
        return 0
    fi
    if [[ "$DRY_RUN" == true ]]; then
        log "[dry-run] append to .gitignore: $entry"
    else
        echo "$entry" >>"$gitignore"
        log "[updated] .gitignore += $entry"
    fi
}

log "Starting comprehensive repository cleanup..."
log "dry_run=$DRY_RUN commit=$COMMIT_CHANGES commit_each_section=$COMMIT_EACH_SECTION cleanup_workflow_runs=$CLEAN_WORKFLOW_RUNS keep_count=$KEEP_COUNT run_list_limit=$RUN_LIST_LIMIT"

# 1. Remove caches and transient artifacts
log "[1/8] Removing caches and transient artifacts..."
for p in \
    ".hypothesis" \
    ".pytest_cache" \
    ".mypy_cache" \
    ".ruff_cache" \
    ".benchmarks" \
    ".coverage" \
    "htmlcov" \
    "venv" \
    ".venv.bak" \
    "playwright-report" \
    "test-results" \
    ".nyc_output" \
    "reports/tmp"; do
    remove_path "$p"
done
commit_if_requested "chore(cleanup): remove caches and transient artifacts"

# 2. Remove backup files and duplicate copy files
log "[2/8] Removing backup and duplicate files..."
remove_matching_files "." "*.bak" "*.backup" "*.old" "*.orig" "*.rej"
remove_matching_files "." "* 2.*" "* 3.*" "* (2).*" "* (3).*"
remove_matching_files "." ".env*.bak" ".env*.backup" ".env*.old" ".env*.tmp"
remove_matching_files "." "*.tmp" "*.cleanup-backup"
commit_if_requested "chore(cleanup): remove backups and duplicate copies"

# 3. Remove empty files in source/docs folders
log "[3/8] Removing empty files..."
if command_exists python3; then
    if [[ "$DRY_RUN" == true ]]; then
        python3 - <<'PY'
from pathlib import Path
roots = [Path("backend/python"), Path("backend/src"), Path("frontend/streamlit_app"), Path("scripts"), Path("tests"), Path("docs")]
suffixes = {".py", ".md", ".yml", ".yaml", ".json", ".sql", ".sh", ".txt", ".ts", ".js", ".mjs"}
count = 0
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in suffixes and p.stat().st_size == 0:
            count += 1
print(f"[dry-run] empty files that would be removed: {count}")
PY
    else
        python3 - <<'PY'
from pathlib import Path
roots = [Path("backend/python"), Path("backend/src"), Path("frontend/streamlit_app"), Path("scripts"), Path("tests"), Path("docs")]
suffixes = {".py", ".md", ".yml", ".yaml", ".json", ".sql", ".sh", ".txt", ".ts", ".js", ".mjs"}
deleted = 0
for root in roots:
    if not root.exists():
        continue
    for p in root.rglob("*"):
        if p.is_file() and p.suffix in suffixes and p.stat().st_size == 0:
            p.unlink()
            deleted += 1
print(f"[removed] empty files: {deleted}")
PY
    fi
else
    log "[warn] python3 not available; skipping empty-file cleanup"
fi
commit_if_requested "chore(cleanup): remove empty files"

# 4. Remove orphan symlinks and empty directories
log "[4/8] Removing orphan symlinks and empty directories..."
while IFS= read -r -d '' orphan; do
    remove_path "$orphan"
done < <(find . -type l ! -exec test -e {} \; -print0 2>/dev/null || true)

if [[ "$DRY_RUN" != true ]]; then
    find . \
        -type d \
        -empty \
        ! -path "./.git/*" \
        ! -path "./.venv/*" \
        ! -path "./node_modules/*" \
        -delete 2>/dev/null || true
fi
commit_if_requested "chore(cleanup): remove orphan symlinks and empty directories"

# 5. Update .gitignore with cleanup-related entries
log "[5/8] Updating .gitignore..."
ensure_gitignore_entry "cleanup.log"
ensure_gitignore_entry ".hypothesis/"
ensure_gitignore_entry "*.mp4"
ensure_gitignore_entry "*.mov"
ensure_gitignore_entry "*.mp3"
ensure_gitignore_entry "input.mp4"
ensure_gitignore_entry "output.mp4"
commit_if_requested "chore(cleanup): update gitignore"

# 6. Verify duplicate-copy files are gone
log "[6/8] Verifying duplicate-copy files..."
if command_exists rg; then
    count=$(rg -n "(\s2\.|\(2\)\.|\s3\.|\(3\)\.)" --hidden -g '!.git' | wc -l | awk '{print $1}')
    log "[verify] potential duplicate-copy filename references: ${count}"
fi

# 7. Post-cleanup quality checks
log "[7/8] Running post-cleanup quality checks..."
if command_exists ruff; then
    if [[ "$DRY_RUN" == true ]]; then
        log "[dry-run] ruff check --fix ."
    else
        if ! ruff check --fix .; then
            log "[warn] ruff reported remaining issues"
        fi
    fi
else
    log "[warn] ruff not found"
fi

if command_exists mypy; then
    if [[ "$DRY_RUN" == true ]]; then
        log "[dry-run] mypy ."
    else
        if ! mypy .; then
            log "[warn] mypy reported issues"
        fi
    fi
else
    log "[warn] mypy not found"
fi

# 8. Optional cleanup of old workflow runs
log "[8/8] Optional cleanup of old workflow runs..."
if [[ "$CLEAN_WORKFLOW_RUNS" == true ]]; then
    if ! command_exists gh; then
        log "[warn] gh not found; skipping workflow run cleanup"
    elif ! command_exists jq; then
        log "[warn] jq not found; skipping workflow run cleanup"
    elif ! gh auth status >/dev/null 2>&1; then
        log "[warn] gh is not authenticated; skipping workflow run cleanup"
    else
        all_runs=$(gh run list --limit "$RUN_LIST_LIMIT" --json databaseId,createdAt | \
            jq -r 'sort_by(.createdAt) | reverse | .[].databaseId')
        total_count=$(printf '%s\n' "$all_runs" | sed '/^$/d' | wc -l | awk '{print $1}')
        log "[info] total workflow runs: $total_count"

        if [[ "$total_count" -le "$KEEP_COUNT" ]]; then
            log "[info] nothing to delete; keep_count=$KEEP_COUNT"
        else
            runs_to_delete=$(printf '%s\n' "$all_runs" | sed '/^$/d' | tail -n +$((KEEP_COUNT + 1)))
            delete_count=$(printf '%s\n' "$runs_to_delete" | sed '/^$/d' | wc -l | awk '{print $1}')
            log "[info] deleting $delete_count workflow runs (keeping latest $KEEP_COUNT)"

            if [[ "$DRY_RUN" == true ]]; then
                preview=$(printf '%s\n' "$runs_to_delete" | sed '/^$/d' | head -20)
                log "[dry-run] workflow runs to delete (first 20):"
                log "$preview"
            else
                deleted=0
                failed=0
                while IFS= read -r run_id; do
                    [[ -z "$run_id" ]] && continue
                    if gh run delete "$run_id" --confirm >/dev/null 2>&1; then
                        deleted=$((deleted + 1))
                    else
                        failed=$((failed + 1))
                    fi
                    if [[ $deleted -gt 0 && $((deleted % 100)) -eq 0 ]]; then
                        sleep 2
                    fi
                done <<<"$runs_to_delete"
                log "[done] workflow runs deleted=$deleted failed=$failed"
            fi
        fi
    fi
else
    log "[skip] use --cleanup-workflow-runs to enable this step"
fi

if [[ "$DRY_RUN" != true && "$COMMIT_CHANGES" == true && "$COMMIT_EACH_SECTION" != true ]]; then
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Comprehensive cleanup: remove stale artifacts and duplicates"
        log "[git] committed final cleanup changes"
    else
        log "[git] no changes to commit"
    fi
fi

log "Cleanup completed."
