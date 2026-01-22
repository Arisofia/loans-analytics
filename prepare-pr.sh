#!/bin/bash

# ==============================================================================
#
#  Prepare Pull Request Script
#
#  This script automates the process of syncing a feature branch with the
#  main branch, cleaning up the commit history via rebase, and pushing it
#  to the remote repository to prepare for a Pull Request.
#
#  Usage: ./prepare-pr.sh
#
# ==============================================================================

# --- Configuration & Colors ---
NC='\033[0m' # No Color
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
TARGET_BRANCH="main"

# --- Helper Functions ---
info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

fail() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# --- Main Logic ---

# 1. Check for clean working directory
info "Step 1: Checking for a clean working directory..."
if [[ -n $(git status --porcelain) ]]; then
    fail "Your working directory is not clean. Please commit or stash your changes before running this script."
fi
success "Working directory is clean."

# 2. Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" == "$TARGET_BRANCH" ]; then
    fail "You are on the '$TARGET_BRANCH' branch. This script should be run from a feature branch."
fi
info "Current feature branch is '$CURRENT_BRANCH'."

# 3. Fetch latest changes from remote
info "Step 2: Fetching latest changes from the remote repository..."
git fetch origin || fail "Failed to fetch from origin."
success "Latest changes have been fetched."

# 4. Rebase the current branch onto the target branch
info "Step 3: Rebasing '$CURRENT_BRANCH' onto 'origin/$TARGET_BRANCH'..."
if git rebase "origin/$TARGET_BRANCH"; then
    success "Rebase completed successfully."
else
    warn "Rebase failed. This is likely due to merge conflicts."
    warn "Please resolve the conflicts manually, then run 'git rebase --continue'."
    warn "If you want to abort, run 'git rebase --abort'."
    exit 1
fi

# 5. Force-push the rebased branch to the cloud
info "Step 4: Pushing the updated branch to the cloud..."
warn "A rebase requires a force-push. This will overwrite the remote branch '$CURRENT_BRANCH'."
read -p "Do you want to proceed? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    fail "Push aborted by user."
fi

# Using --force-with-lease is safer than a standard --force
git push --force-with-lease origin "$CURRENT_BRANCH" || fail "Failed to push to origin."
success "Branch '$CURRENT_BRANCH' has been synced and pushed to the cloud."

# 6. Provide Pull Request link
info "Step 5: Generating Pull Request link..."
REPO_URL=$(git config --get remote.origin.url | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')
PR_URL="$REPO_URL/pull/new/$CURRENT_BRANCH"

success "Your branch is ready! Open a Pull Request at the following URL:"
echo -e "${YELLOW}$PR_URL${NC}"
