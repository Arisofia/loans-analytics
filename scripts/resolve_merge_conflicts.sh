#!/bin/bash

################################################################################
# Merge Resolution Script for abaco-loans-analytics
# 
# Purpose: Safely resolve all merge conflicts by taking the current branch
#          version, clean up unmerged files, and prepare for a clean commit.
#
# Usage: ./merge-resolution.sh [--dry-run] [--auto-commit]
# 
# Options:
#   --dry-run       Show what would be done without making changes
#   --auto-commit   Automatically commit resolved changes
#
# Date Created: 2026-01-11 05:50:58 UTC
# Author: Jenoutlook
################################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script variables
DRY_RUN=false
AUTO_COMMIT=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/merge-resolution-$(date +%Y%m%d-%H%M%S).log"

################################################################################
# Helper Functions
################################################################################

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "$LOG_FILE"
}

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    --dry-run       Show what would be done without making changes
    --auto-commit   Automatically commit resolved changes
    --help          Display this help message

Examples:
    # Preview changes without applying them
    $0 --dry-run
    
    # Resolve conflicts and auto-commit
    $0 --auto-commit
    
    # Resolve conflicts (interactive commit)
    $0

EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --auto-commit)
                AUTO_COMMIT=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        log_error "git is not installed"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "Not in a git repository"
        exit 1
    fi
    
    # Check for merge in progress
    if [ -f "$(git rev-parse --git-dir)/MERGE_HEAD" ]; then
        log_info "Merge in progress detected"
    else
        log_warning "No merge in progress. Script is designed for resolving merge conflicts."
    fi
    
    log_success "Prerequisites check completed"
}

display_merge_status() {
    log_info "Current merge status:"
    echo ""
    git status
    echo ""
}

resolve_conflicts() {
    log_info "Resolving merge conflicts..."
    
    # Get list of conflicted files
    local conflicted_files=$(git diff --name-only --diff-filter=U)
    
    if [ -z "$conflicted_files" ]; then
        log_warning "No conflicted files found"
        return 0
    fi
    
    log_info "Found the following conflicted files:"
    echo "$conflicted_files" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    
    # Resolve all conflicts by taking ours (current branch)
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would resolve conflicts by taking current branch version"
        echo "$conflicted_files" | while read -r file; do
            log_info "[DRY-RUN] Would resolve: $file"
        done
    else
        log_info "Resolving all conflicts by taking current branch version..."
        echo "$conflicted_files" | while read -r file; do
            git checkout --ours "$file"
            git add "$file"
            log_success "Resolved: $file (taking current branch version)"
        done
    fi
}

clean_unmerged_files() {
    log_info "Cleaning up unmerged files..."
    
    # Get list of unmerged files (files that were deleted by one side)
    local unmerged_files=$(git diff --name-only --diff-filter=DU --cached)
    
    if [ -z "$unmerged_files" ]; then
        log_info "No unmerged files to clean up"
        return 0
    fi
    
    log_info "Found unmerged files:"
    echo "$unmerged_files" | while read -r file; do
        echo "  - $file"
    done
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would remove unmerged files"
    else
        echo "$unmerged_files" | while read -r file; do
            if [ -f "$file" ]; then
                git rm "$file" 2>/dev/null || true
                log_success "Removed: $file"
            fi
        done
    fi
}

verify_resolution() {
    log_info "Verifying merge resolution..."
    
    # Check for any remaining conflicts
    local remaining_conflicts=$(git diff --name-only --diff-filter=U)
    
    if [ -n "$remaining_conflicts" ]; then
        log_error "Unresolved conflicts remain:"
        echo "$remaining_conflicts"
        return 1
    fi
    
    # Check git status
    local status=$(git status --porcelain | grep -E '^(UU|AA|DD|AU|UD|DD)' || true)
    
    if [ -n "$status" ]; then
        log_warning "Unresolved merge status entries found:"
        echo "$status"
        return 1
    fi
    
    log_success "All conflicts resolved successfully"
    return 0
}

prepare_for_commit() {
    log_info "Preparing for commit..."
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would stage all resolved changes"
        return 0
    fi
    
    # Stage all resolved changes
    git add -A
    
    # Show what would be committed
    log_info "Changes staged for commit:"
    git status --short
}

create_merge_commit() {
    log_info "Creating merge commit..."
    
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    local merge_branch=$(git rev-parse MERGE_HEAD 2>/dev/null || echo "unknown")
    
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] Would create merge commit with message:"
        echo "  Merge branch '${merge_branch}' into '${current_branch}'"
        echo ""
        echo "  Conflicts resolved by taking current branch version."
        echo "  Unmerged files cleaned up."
        echo ""
        echo "  Resolution script: merge-resolution.sh"
        echo "  Resolved at: $(date '+%Y-%m-%d %H:%M:%S %Z')"
        return 0
    fi
    
    if [ "$AUTO_COMMIT" = true ]; then
        log_info "Creating merge commit automatically..."
        git commit -m "Merge branch '${merge_branch}' into '${current_branch}' - Conflicts resolved

Conflicts resolved by taking current branch version.
Unmerged files cleaned up.

Resolution script: merge-resolution.sh
Resolved at: $(date '+%Y-%m-%d %H:%M:%S %Z')" || {
            log_error "Failed to create merge commit"
            return 1
        }
        log_success "Merge commit created successfully"
    else
        log_warning "Automatic commit disabled. Review changes and commit manually:"
        log_info "git commit -m 'Your merge commit message'"
    fi
}

display_summary() {
    log_info "=========================================="
    log_info "Merge Resolution Summary"
    log_info "=========================================="
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY-RUN mode: No changes were made"
    fi
    
    log_info "Repository: Arisofia/abaco-loans-analytics"
    log_info "Current branch: $(git rev-parse --abbrev-ref HEAD)"
    log_info "Script executed: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    log_info "Log file: $LOG_FILE"
    log_info "=========================================="
}

################################################################################
# Main Execution
################################################################################

main() {
    log_info "=========================================="
    log_info "Starting Merge Resolution Script"
    log_info "=========================================="
    echo ""
    
    parse_arguments "$@"
    
    if [ "$DRY_RUN" = true ]; then
        log_warning "Running in DRY-RUN mode (no changes will be made)"
        echo ""
    fi
    
    check_prerequisites
    echo ""
    
    display_merge_status
    
    resolve_conflicts
    echo ""
    
    clean_unmerged_files
    echo ""
    
    if verify_resolution; then
        prepare_for_commit
        echo ""
        
        create_merge_commit
        echo ""
        
        log_success "Merge resolution completed successfully!"
    else
        log_error "Merge resolution failed due to unresolved conflicts"
        exit 1
    fi
    
    echo ""
    display_summary
}

# Run main function with all arguments
main "$@"
