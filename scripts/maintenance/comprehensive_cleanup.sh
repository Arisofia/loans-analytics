#!/usr/bin/env bash
# ==============================================================================
# Comprehensive Repository Cleanup
#
# Purpose:
# - Remove deprecated/unused integration artifacts
# - Clean caches/backups/orphans
# - Verify references to retired integrations
# - Run post-cleanup quality checks
#
# Usage:
#   ./scripts/maintenance/comprehensive_cleanup.sh --dry-run
#   ./scripts/maintenance/comprehensive_cleanup.sh --with-rollback --commit
#   ./scripts/maintenance/comprehensive_cleanup.sh --commit-each-section
# ==============================================================================

set -euo pipefail

DRY_RUN=false
WITH_ROLLBACK=false
COMMIT_CHANGES=false
COMMIT_EACH_SECTION=false
LOG_FILE="cleanup.log"

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
ROLLBACK_ROOT=".rollback/${TIMESTAMP}"

usage() {
    cat <<'EOF'
Usage: comprehensive_cleanup.sh [options]

Options:
  --dry-run              Preview actions without deleting/modifying files.
  --with-rollback        Backup removed files under .rollback/<timestamp>/.
  --commit               Commit all changes at end (if any).
  --commit-each-section  Commit after each section (implies --commit).
  --log-file <path>      Override log file path (default: cleanup.log).
  --help                 Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --with-rollback)
            WITH_ROLLBACK=true
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

backup_path() {
    local path="$1"
    if [[ "$WITH_ROLLBACK" != true || "$DRY_RUN" == true || ! -e "$path" ]]; then
        return 0
    fi
    local dst="${ROLLBACK_ROOT}/${path}"
    mkdir -p "$(dirname "$dst")"
    cp -a "$path" "$dst"
    log "[backup] $path -> $dst"
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
        return 0
    fi
    backup_path "$path"
    rm -rf -- "$path"
    log "[removed] $path"
}

remove_paths() {
    local p
    for p in "$@"; do
        remove_path "$p"
    done
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
            \( -path "*/.git/*" -o -path "*/.venv/*" -o -path "*/node_modules/*" -o -path "*/.rollback/*" \) -prune \
            -o -type f -iname "$pattern" -print0 2>/dev/null)
    done
}

remove_matching_dirs() {
    local root="$1"
    shift
    local -a patterns=("$@")
    [[ -d "$root" ]] || return 0

    local pattern dir
    for pattern in "${patterns[@]}"; do
        while IFS= read -r -d '' dir; do
            remove_path "$dir"
        done < <(find "$root" \
            \( -path "*/.git/*" -o -path "*/.venv/*" -o -path "*/node_modules/*" -o -path "*/.rollback/*" \) -prune \
            -o -type d -iname "$pattern" -print0 2>/dev/null)
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

keyword_count() {
    local keyword="$1"
    if command_exists rg; then
        rg -i \
            --glob '*.py' \
            --glob '*.sh' \
            --glob '*.yml' \
            --glob '*.yaml' \
            --glob '*.md' \
            --glob '*.json' \
            --glob '*.sql' \
            --glob '*.ts' \
            --glob '*.js' \
            --glob '*.mjs' \
            --glob '!node_modules/**' \
            --glob '!.venv/**' \
            --glob '!.git/**' \
            "$keyword" . | wc -l | awk '{print $1}'
    else
        grep -R -i "$keyword" \
            --include='*.py' \
            --include='*.sh' \
            --include='*.yml' \
            --include='*.yaml' \
            --include='*.md' \
            --include='*.json' \
            --include='*.sql' \
            --include='*.ts' \
            --include='*.js' \
            --include='*.mjs' \
            --exclude-dir=.git \
            --exclude-dir=.venv \
            --exclude-dir=node_modules \
            . | wc -l | awk '{print $1}'
    fi
}

log "Starting comprehensive repository cleanup..."
log "dry_run=$DRY_RUN rollback=$WITH_ROLLBACK commit=$COMMIT_CHANGES commit_each_section=$COMMIT_EACH_SECTION"

# 1. REMOVE EXTERNAL INTEGRATION SERVICES
log "[1/14] Removing external service integration directories..."
remove_paths \
    "services/slack_bot" \
    "services/figma_sync" \
    "services/notion_integration" \
    "services/hubspot_connector" \
    "apps/slack_bot" \
    "apps/figma_sync" \
    "apps/notion_integration" \
    "apps/hubspot_connector" \
    "python/integrations/slack" \
    "python/integrations/figma" \
    "python/integrations/notion" \
    "python/integrations/hubspot"
commit_if_requested "chore(cleanup): remove external service integration directories"

# 2. REMOVE INTEGRATION SCRIPTS/WORKFLOWS
log "[2/14] Removing integration workflows and scripts..."
remove_matching_files ".github/workflows" \
    "*slack*.yml" "*slack*.yaml" \
    "*figma*.yml" "*figma*.yaml" \
    "*notion*.yml" "*notion*.yaml" \
    "*hubspot*.yml" "*hubspot*.yaml"
remove_matching_files "scripts" \
    "*slack*.sh" "*slack*.py" \
    "*figma*.sh" "*figma*.py" \
    "*notion*.sh" "*notion*.py" \
    "*hubspot*.sh" "*hubspot*.py"
commit_if_requested "chore(cleanup): remove integration scripts and workflows"

# 3. REMOVE HIDDEN FOLDERS, CACHES, VENV BACKUPS
log "[3/14] Removing hidden folders/caches/backups..."
remove_paths \
    ".zencoder" \
    ".zenflow" \
    ".hypothesis" \
    ".pytest_cache" \
    ".mypy_cache" \
    ".ruff_cache" \
    ".benchmarks" \
    ".coverage" \
    "htmlcov" \
    "venv" \
    ".venv.bak" \
    "backups" \
    ".backup"
commit_if_requested "chore(cleanup): remove hidden folders and caches"

# 4. REMOVE INTEGRATION FILES IN LEGACY ROOTS
log "[4/14] Removing integration files from legacy roots..."
remove_matching_dirs "services" "*slack*" "*figma*" "*notion*" "*hubspot*"
remove_matching_dirs "integrations" "*slack*" "*figma*" "*notion*" "*hubspot*"
remove_matching_dirs "config/integrations" "*slack*" "*figma*" "*notion*" "*hubspot*"
commit_if_requested "chore(cleanup): remove legacy integration files"

# 5. CLEAN PYTHON CODE ORPHANS/EMPTY FILES
log "[5/14] Cleaning Python/code-level orphans and empty files..."
if command_exists python3; then
    if [[ "$DRY_RUN" == true ]]; then
        python3 - <<'PY'
from pathlib import Path

roots = [Path("python"), Path("src"), Path("scripts"), Path("tests"), Path("docs")]
suffixes = {".py", ".md", ".yml", ".yaml", ".json", ".sql", ".sh", ".txt"}
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

roots = [Path("python"), Path("src"), Path("scripts"), Path("tests"), Path("docs")]
suffixes = {".py", ".md", ".yml", ".yaml", ".json", ".sql", ".sh", ".txt"}
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
    log "[warn] python3 not available; skipping section 5"
fi
commit_if_requested "chore(cleanup): remove empty code/doc/config files"

# 6. CLEAN CONFIG BACKUPS
log "[6/14] Removing config backup files..."
remove_matching_files "." "*.bak" "*.backup" "*.old" "*.orig" "*.rej"
commit_if_requested "chore(cleanup): remove backup config files"

# 7. CLEAN DUPLICATED COPY FILES
log "[7/14] Removing duplicate copy files (e.g. '* 2.*', '*(2).*')..."
remove_matching_files "." "* 2.*" "* 3.*" "* (2).*" "* (3).*"
commit_if_requested "chore(cleanup): remove duplicate copy files"

# 8. CLEAN ENV BACKUPS
log "[8/14] Removing environment backup files..."
remove_matching_files "." ".env*.bak" ".env*.backup" ".env*.old" ".env*.tmp"
commit_if_requested "chore(cleanup): remove env backup files"

# 9. CLEAN TEST ARTIFACTS
log "[9/14] Removing test artifacts..."
remove_paths "playwright-report" "test-results" ".nyc_output" "reports/tmp"
remove_matching_files "." "*.log" "*.tmp"
commit_if_requested "chore(cleanup): remove test artifacts and tmp logs"

# 10. CLEAN DOC DUPLICATES/ORPHANS
log "[10/14] Removing empty docs and stale duplicate docs..."
if [[ "$DRY_RUN" == true ]]; then
    find docs -type f -empty -print 2>/dev/null | sed 's/^/[dry-run] remove /' | tee -a "$LOG_FILE" || true
else
    while IFS= read -r -d '' empty_doc; do
        remove_path "$empty_doc"
    done < <(find docs -type f -empty -print0 2>/dev/null)
fi
remove_matching_files "docs" "* 2.md" "* (2).md" "* 3.md" "* (3).md"
commit_if_requested "chore(cleanup): remove empty and duplicate docs"

# 11. CLEAN ORPHANED SYMLINKS/EMPTY DIRECTORIES
log "[11/14] Removing orphaned symlinks and empty directories..."
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

# 12. UPDATE .gitignore
log "[12/14] Updating .gitignore..."
ensure_gitignore_entry ".rollback/"
ensure_gitignore_entry "cleanup.log"
ensure_gitignore_entry ".hypothesis/"
ensure_gitignore_entry "*.mp4"
ensure_gitignore_entry "*.mov"
ensure_gitignore_entry "*.mp3"
ensure_gitignore_entry "input.mp4"
ensure_gitignore_entry "output.mp4"
commit_if_requested "chore(cleanup): update gitignore patterns"

# 13. VERIFICATION
log "[13/14] Verification scan for integration keyword references..."
for keyword in slack figma notion hubspot zencoder zenflow; do
    count="$(keyword_count "$keyword")"
    log "[verify] ${keyword}: ${count}"
done

if command_exists rg; then
    log "[verify] top matching lines (first 50):"
    rg -i \
        --glob '*.py' \
        --glob '*.sh' \
        --glob '*.yml' \
        --glob '*.yaml' \
        --glob '*.md' \
        --glob '*.json' \
        --glob '*.sql' \
        --glob '*.ts' \
        --glob '*.js' \
        --glob '*.mjs' \
        --glob '!node_modules/**' \
        --glob '!.venv/**' \
        --glob '!.git/**' \
        "(slack|figma|notion|hubspot|zencoder|zenflow)" . \
        | head -n 50 | tee -a "$LOG_FILE" || true
fi

# 14. POST-CLEANUP OPTIMIZATION
log "[14/14] Post-cleanup optimization..."
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

if [[ "$DRY_RUN" != true && "$COMMIT_CHANGES" == true && "$COMMIT_EACH_SECTION" != true ]]; then
    git add -A
    if ! git diff --cached --quiet; then
        git commit -m "Comprehensive cleanup: removed deprecated integrations and artifacts"
        log "[git] committed final cleanup changes"
    else
        log "[git] no changes to commit"
    fi
fi

log "Cleanup completed."
