#!/bin/bash

# ==============================================================================
#
#  Repo Doctor & Automation Script
#
#  This script automates the following tasks:
#  1. Checks for and installs necessary tools (ffmpeg).
#  2. Cleans the Git working directory by ignoring generated media files.
#  3. Scans GitHub Actions workflows for common problems.
#  4. Commits and pushes all changes to the current branch.
#
#  Usage: ./repo-doctor.sh
#
# ==============================================================================

# --- Configuration & Colors ---
NC='\033[0m' # No Color
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'

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

# 1. Prerequisite Checks
info "Step 1: Checking prerequisites..."
if ! command -v git &> /dev/null; then
    fail "Git is not installed. Please install Git and run again."
fi
if ! command -v brew &> /dev/null; then
    fail "Homebrew is not installed. Please install Homebrew (see https://brew.sh/) and run again."
fi
success "Prerequisites are met."

# 2. Install Missing Tools
info "Step 2: Checking for required tools..."
if ! command -v ffmpeg &> /dev/null; then
    warn "ffmpeg is not found. Attempting to install with Homebrew..."
    brew install ffmpeg || fail "Failed to install ffmpeg. Please install it manually."
    success "ffmpeg has been installed."
else
    success "ffmpeg is already installed."
fi

# 3. Clean Git Repository
info "Step 3: Cleaning Git repository..."
GITIGNORE_PATTERNS="\n# Ignore generated media files\n*.mp4\n*.mov\n*.mp3\n"
if [ -f ".gitignore" ] && grep -q "*.mp4" .gitignore; then
    success ".gitignore is already configured to ignore media files."
else
    warn ".gitignore is missing media file patterns. Adding them now."
    printf "$GITIGNORE_PATTERNS" >> .gitignore
    success "Added media file patterns to .gitignore."
fi

# 4. Scan GitHub Workflows
info "Step 4: Scanning GitHub Actions workflows for issues..."
WORKFLOW_DIR=".github/workflows"
HAS_ISSUES=false

# Scan for duplicate OPENAI_API_KEY
warn "Scanning for duplicate OPENAI_API_KEY entries..."
DUPLICATE_KEYS=$(grep -r "OPENAI_API_KEY" "$WORKFLOW_DIR" 2>/dev/null | cut -d: -f1 | uniq -c | grep -v " 1 ")
if [ -n "$DUPLICATE_KEYS" ]; then
    HAS_ISSUES=true
    warn "Found files with multiple OPENAI_API_KEY definitions:"
    echo "$DUPLICATE_KEYS"
else
    success "No duplicate OPENAI_API_KEY issues found."
fi

# Scan for illegal job-level if: secrets...
warn "Scanning for illegal job-level 'if: secrets...' usage..."
ILLEGAL_IFS=$(grep -r -E "^\s*if:.*\s*secrets\." "$WORKFLOW_DIR" 2>/dev/null)
if [ -n "$ILLEGAL_IFS" ]; then
    HAS_ISSUES=true
    warn "Found workflows with potentially invalid job-level 'if' conditions:"
    echo "$ILLEGAL_IFS"
else
    success "No invalid job-level 'if' conditions found."
fi

if [ "$HAS_ISSUES" = false ]; then
    success "Workflow scan completed with no major issues found."
fi

# 5. Commit and Push Changes
info "Step 5: Committing and pushing all changes..."
if [[ -z $(git status --porcelain) ]]; then
    success "Working tree is clean. Nothing to commit."
else
    git add .
    COMMIT_MSG="chore: Run repo-doctor to clean gitignore and scan workflows"
    info "Committing changes with message: '$COMMIT_MSG'"
    git commit -m "$COMMIT_MSG" || fail "Git commit failed."
    
    info "Pushing changes to the remote branch..."
    git push || fail "Git push failed. Please resolve any upstream conflicts and push manually."
    success "All changes have been successfully committed and pushed."
fi

echo -e "\n${GREEN}Automation complete! Your repository is clean and your changes are on GitHub.${NC}"
